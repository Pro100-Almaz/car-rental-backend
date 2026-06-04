import logging
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import TypedDict
from uuid import UUID

from app.core.commands.exceptions import (
    ClientNotFoundError,
    InvalidRentalStatusTransitionError,
    PendingExtensionExistsError,
    RentalDateOverlapError,
    RentalNotFoundError,
)
from app.core.commands.ports.client_tx_storage import ClientTxStorage
from app.core.commands.ports.extension_request_tx_storage import ExtensionRequestTxStorage
from app.core.commands.ports.flusher import Flusher
from app.core.commands.ports.rental_tx_storage import RentalTxStorage
from app.core.commands.ports.transaction_manager import TransactionManager
from app.core.commands.ports.utc_timer import UtcTimer
from app.core.common.authorization.authorize import authorize
from app.core.common.authorization.current_user_service import CurrentUserService
from app.core.common.authorization.rbac import HasPermission, PermissionCheckContext
from app.core.common.entities.extension_request import ExtensionRequest
from app.core.common.entities.types_ import (
    ClientId,
    ExtensionRequestStatus,
    OrganizationId,
    RentalId,
    RentalStatus,
    VehicleId,
)
from app.core.common.exceptions import BaseError
from app.core.common.factories.id_factory import create_extension_request_id
from app.core.common.value_objects.utc_datetime import UtcDatetime

logger = logging.getLogger(__name__)

MAX_EXTENSION_DAYS = 30


class InvalidExtensionDatesError(BaseError):
    default_message: str = "Invalid extension dates."


@dataclass(frozen=True, slots=True, kw_only=True)
class SubmitExtensionRequestInput:
    rental_id: UUID
    new_end_date: datetime
    additional_cost: Decimal


class SubmitExtensionRequestResponse(TypedDict):
    id: UUID
    created_at: datetime


class SubmitExtensionRequestCommand:
    def __init__(
        self,
        current_user_service: CurrentUserService,
        utc_timer: UtcTimer,
        rental_tx_storage: RentalTxStorage,
        client_tx_storage: ClientTxStorage,
        extension_request_tx_storage: ExtensionRequestTxStorage,
        flusher: Flusher,
        transaction_manager: TransactionManager,
    ) -> None:
        self._current_user_service = current_user_service
        self._utc_timer = utc_timer
        self._rental_tx_storage = rental_tx_storage
        self._client_tx_storage = client_tx_storage
        self._extension_request_tx_storage = extension_request_tx_storage
        self._flusher = flusher
        self._transaction_manager = transaction_manager

    async def execute(self, request: SubmitExtensionRequestInput) -> SubmitExtensionRequestResponse:
        logger.info("Submit extension request: started.")

        current_user = await self._current_user_service.get_current_user()
        authorize(
            HasPermission(),
            context=PermissionCheckContext(
                subject=current_user,
                required_permission="mobile.rental",
            ),
        )

        client = await self._client_tx_storage.get_by_id(ClientId(current_user.client_id))
        if client is None:
            raise ClientNotFoundError

        rental_id = RentalId(request.rental_id)
        rental = await self._rental_tx_storage.get_by_id(rental_id)
        if rental is None:
            raise RentalNotFoundError
        if rental.client_id != client.id_:
            raise RentalNotFoundError

        if rental.status != RentalStatus.ACTIVE:
            raise InvalidRentalStatusTransitionError(
                "Only active rentals can be extended."
            )

        if request.new_end_date <= rental.scheduled_end:
            raise InvalidExtensionDatesError(
                "New end date must be after current scheduled end."
            )
        extension_days = (request.new_end_date - rental.scheduled_end).days
        if extension_days > MAX_EXTENSION_DAYS:
            raise InvalidExtensionDatesError(
                f"Extension cannot exceed {MAX_EXTENSION_DAYS} days."
            )
        if request.additional_cost < Decimal(0):
            raise InvalidExtensionDatesError(
                "Additional cost cannot be negative."
            )

        pending = await self._extension_request_tx_storage.get_pending_for_rental(rental_id)
        if pending is not None:
            raise PendingExtensionExistsError

        has_overlap = await self._rental_tx_storage.has_overlap(
            vehicle_id=VehicleId(rental.vehicle_id),
            scheduled_start=rental.scheduled_end,
            scheduled_end=request.new_end_date,
        )
        if has_overlap:
            raise RentalDateOverlapError

        now = UtcDatetime(self._utc_timer.now.value)
        ext_request = ExtensionRequest(
            id_=create_extension_request_id(),
            organization_id=OrganizationId(rental.organization_id),
            rental_id=rental_id,
            client_id=client.id_,
            new_end_date=UtcDatetime(request.new_end_date),
            additional_cost=request.additional_cost,
            status=ExtensionRequestStatus.PENDING,
            rejection_reason=None,
            reviewed_by=None,
            reviewed_at=None,
            created_at=now,
        )
        self._extension_request_tx_storage.add(ext_request)
        await self._flusher.flush()
        await self._transaction_manager.commit()

        logger.info("Submit extension request: done.")
        return SubmitExtensionRequestResponse(
            id=ext_request.id_,
            created_at=ext_request.created_at.value,
        )
