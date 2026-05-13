import logging
from dataclasses import dataclass
from datetime import datetime
from typing import TypedDict
from uuid import UUID

from app.core.commands.ports.flusher import Flusher
from app.core.commands.ports.transaction_manager import TransactionManager
from app.core.commands.ports.utc_timer import UtcTimer
from app.core.commands.ports.vehicle_category_tx_storage import VehicleCategoryTxStorage
from app.core.common.authorization.authorize import authorize
from app.core.common.authorization.current_user_service import CurrentUserService
from app.core.common.authorization.rbac import HasPermission, PermissionCheckContext
from app.core.common.entities.types_ import OrganizationId
from app.core.common.entities.vehicle_category import VehicleCategoryEntity
from app.core.common.factories.id_factory import create_vehicle_category_id
from app.core.common.value_objects.utc_datetime import UtcDatetime

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class CreateVehicleCategoryRequest:
    organization_id: UUID
    name: str
    sort_order: int = 0


class CreateVehicleCategoryResponse(TypedDict):
    id: UUID
    created_at: datetime


class CreateVehicleCategory:
    def __init__(
        self,
        current_user_service: CurrentUserService,
        utc_timer: UtcTimer,
        vehicle_category_tx_storage: VehicleCategoryTxStorage,
        flusher: Flusher,
        transaction_manager: TransactionManager,
    ) -> None:
        self._current_user_service = current_user_service
        self._utc_timer = utc_timer
        self._storage = vehicle_category_tx_storage
        self._flusher = flusher
        self._transaction_manager = transaction_manager

    async def execute(self, request: CreateVehicleCategoryRequest) -> CreateVehicleCategoryResponse:
        logger.info("Create vehicle category: started.")

        current_user = await self._current_user_service.get_current_user()
        authorize(
            HasPermission(),
            context=PermissionCheckContext(
                subject=current_user,
                required_permission="fleet.create",
            ),
        )

        now = UtcDatetime(self._utc_timer.now.value)
        category = VehicleCategoryEntity(
            id_=create_vehicle_category_id(),
            organization_id=OrganizationId(request.organization_id),
            name=request.name,
            sort_order=request.sort_order,
            is_active=True,
            created_at=now,
        )
        self._storage.add(category)
        await self._flusher.flush()
        await self._transaction_manager.commit()

        logger.info("Create vehicle category: done.")
        return CreateVehicleCategoryResponse(
            id=category.id_,
            created_at=category.created_at.value,
        )
