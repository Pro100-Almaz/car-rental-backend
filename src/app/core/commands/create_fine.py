import logging
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import TypedDict
from uuid import UUID

from app.core.commands.ports.fine_tx_storage import FineTxStorage
from app.core.commands.ports.flusher import Flusher
from app.core.commands.ports.transaction_manager import TransactionManager
from app.core.commands.ports.utc_timer import UtcTimer
from app.core.common.authorization.authorize import authorize
from app.core.common.authorization.current_user_service import CurrentUserService
from app.core.common.authorization.rbac import HasPermission, PermissionCheckContext
from app.core.common.entities.fine import Fine
from app.core.common.entities.types_ import (
    ClientId,
    FineStatus,
    FineType,
    OrganizationId,
    RentalId,
    VehicleId,
)
from app.core.common.factories.id_factory import create_fine_id
from app.core.common.value_objects.utc_datetime import UtcDatetime

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class CreateFineRequest:
    organization_id: UUID
    vehicle_id: UUID
    rental_id: UUID | None = None
    client_id: UUID | None = None
    fine_type: FineType
    amount: Decimal
    description: str | None = None
    fine_date: date
    document_url: str | None = None


class CreateFineResponse(TypedDict):
    id: UUID
    created_at: datetime


class CreateFine:
    def __init__(
        self,
        current_user_service: CurrentUserService,
        utc_timer: UtcTimer,
        fine_tx_storage: FineTxStorage,
        flusher: Flusher,
        transaction_manager: TransactionManager,
    ) -> None:
        self._current_user_service = current_user_service
        self._utc_timer = utc_timer
        self._fine_tx_storage = fine_tx_storage
        self._flusher = flusher
        self._transaction_manager = transaction_manager

    async def execute(self, request: CreateFineRequest) -> CreateFineResponse:
        logger.info("Create fine: started.")

        current_user = await self._current_user_service.get_current_user()
        authorize(
            HasPermission(),
            context=PermissionCheckContext(
                subject=current_user,
                required_permission="fine.create",
            ),
        )

        now = UtcDatetime(self._utc_timer.now.value)
        fine = Fine(
            id_=create_fine_id(),
            organization_id=OrganizationId(request.organization_id),
            vehicle_id=VehicleId(request.vehicle_id),
            rental_id=RentalId(request.rental_id) if request.rental_id else None,
            client_id=ClientId(request.client_id) if request.client_id else None,
            fine_type=request.fine_type,
            amount=request.amount,
            description=request.description,
            fine_date=request.fine_date,
            document_url=request.document_url,
            status=FineStatus.PENDING,
            created_at=now,
            updated_at=now,
        )
        self._fine_tx_storage.add(fine)
        await self._flusher.flush()
        await self._transaction_manager.commit()

        logger.info("Create fine: done.")
        return CreateFineResponse(
            id=fine.id_,
            created_at=fine.created_at.value,
        )
