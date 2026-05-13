import logging
from dataclasses import dataclass
from uuid import UUID

from app.core.commands.ports.flusher import Flusher
from app.core.commands.ports.transaction_manager import TransactionManager
from app.core.commands.ports.vehicle_category_tx_storage import VehicleCategoryTxStorage
from app.core.common.authorization.authorize import authorize
from app.core.common.authorization.current_user_service import CurrentUserService
from app.core.common.authorization.rbac import HasPermission, PermissionCheckContext

logger = logging.getLogger(__name__)

_UNSET = object()


class VehicleCategoryNotFoundError(Exception):
    pass


@dataclass(frozen=True, slots=True, kw_only=True)
class UpdateVehicleCategoryRequest:
    category_id: UUID
    name: str | object = _UNSET
    sort_order: int | object = _UNSET
    is_active: bool | object = _UNSET


class UpdateVehicleCategory:
    def __init__(
        self,
        current_user_service: CurrentUserService,
        vehicle_category_tx_storage: VehicleCategoryTxStorage,
        flusher: Flusher,
        transaction_manager: TransactionManager,
    ) -> None:
        self._current_user_service = current_user_service
        self._storage = vehicle_category_tx_storage
        self._flusher = flusher
        self._transaction_manager = transaction_manager

    async def execute(self, request: UpdateVehicleCategoryRequest) -> None:
        logger.info("Update vehicle category: started.")

        current_user = await self._current_user_service.get_current_user()
        authorize(
            HasPermission(),
            context=PermissionCheckContext(
                subject=current_user,
                required_permission="fleet.update",
            ),
        )

        category = await self._storage.get_by_id(request.category_id)
        if category is None:
            raise VehicleCategoryNotFoundError

        if request.name is not _UNSET:
            category.name = request.name
        if request.sort_order is not _UNSET:
            category.sort_order = request.sort_order
        if request.is_active is not _UNSET:
            category.is_active = request.is_active

        await self._flusher.flush()
        await self._transaction_manager.commit()

        logger.info("Update vehicle category: done.")
