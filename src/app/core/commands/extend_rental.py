import logging
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from app.core.commands.exceptions import (
    InvalidRentalStatusTransitionError,
    PendingExtensionExistsError,
    RentalNotFoundError,
)
from app.core.commands.ports.extension_request_tx_storage import ExtensionRequestTxStorage
from app.core.commands.ports.rental_tx_storage import RentalTxStorage
from app.core.commands.ports.transaction_manager import TransactionManager
from app.core.commands.ports.utc_timer import UtcTimer
from app.core.common.authorization.authorize import authorize
from app.core.common.authorization.current_user_service import CurrentUserService
from app.core.common.authorization.rbac import HasPermission, PermissionCheckContext
from app.core.common.entities.extension_request import ExtensionRequest
from app.core.common.entities.types_ import ExtensionRequestStatus, RentalId, RentalStatus
from app.core.common.factories.id_factory import create_extension_request_id
from app.core.common.value_objects.utc_datetime import UtcDatetime

logger = logging.getLogger(__name__)

_EXTENDABLE_STATUSES = {RentalStatus.CONFIRMED, RentalStatus.ACTIVE}


@dataclass(frozen=True, slots=True, kw_only=True)
class ExtendRentalRequest:
    rental_id: UUID
    new_scheduled_end: datetime
    new_estimated_total: Decimal


class ExtendRental:
    def __init__(
        self,
        current_user_service: CurrentUserService,
        utc_timer: UtcTimer,
        rental_tx_storage: RentalTxStorage,
        extension_request_tx_storage: ExtensionRequestTxStorage,
        transaction_manager: TransactionManager,
    ) -> None:
        self._current_user_service = current_user_service
        self._utc_timer = utc_timer
        self._rental_tx_storage = rental_tx_storage
        self._extension_request_tx_storage = extension_request_tx_storage
        self._transaction_manager = transaction_manager

    async def execute(self, request: ExtendRentalRequest) -> None:
        logger.info("Extend rental: started.")

        current_user = await self._current_user_service.get_current_user()
        authorize(
            HasPermission(),
            context=PermissionCheckContext(
                subject=current_user,
                required_permission="rental.update",
            ),
        )

        rental_id = RentalId(request.rental_id)
        rental = await self._rental_tx_storage.get_by_id(rental_id)
        if rental is None:
            raise RentalNotFoundError

        if rental.status not in _EXTENDABLE_STATUSES:
            raise InvalidRentalStatusTransitionError(f"Cannot extend rental with status '{rental.status}'.")

        existing_pending = await self._extension_request_tx_storage.get_pending_for_rental(rental_id)
        if existing_pending is not None:
            raise PendingExtensionExistsError

        now = UtcDatetime(self._utc_timer.now.value)
        ext_req = ExtensionRequest(
            id_=create_extension_request_id(),
            organization_id=rental.organization_id,
            rental_id=rental.id_,
            client_id=rental.client_id,
            new_end_date=UtcDatetime(request.new_scheduled_end),
            additional_cost=request.new_estimated_total - rental.estimated_total,
            status=ExtensionRequestStatus.PENDING,
            rejection_reason=None,
            reviewed_by=None,
            reviewed_at=None,
            created_at=now,
        )
        self._extension_request_tx_storage.add(ext_req)
        await self._transaction_manager.commit()

        logger.info("Extend rental: done. extension_request_id=%s", ext_req.id_)
