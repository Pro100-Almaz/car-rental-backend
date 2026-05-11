import logging
from collections.abc import Mapping, Set
from dataclasses import dataclass
from typing import Final
from uuid import UUID

from app.core.commands.exceptions import InvalidVehicleStatusTransitionError, VehicleNotFoundError
from app.core.commands.ports.transaction_manager import TransactionManager
from app.core.commands.ports.utc_timer import UtcTimer
from app.core.commands.ports.vehicle_tx_storage import VehicleTxStorage
from app.core.common.authorization.authorize import authorize
from app.core.common.authorization.current_user_service import CurrentUserService
from app.core.common.authorization.rbac import HasPermission, PermissionCheckContext
from app.core.common.entities.types_ import VehicleId, VehicleStatus
from app.core.common.value_objects.utc_datetime import UtcDatetime

logger = logging.getLogger(__name__)

VALID_TRANSITIONS: Final[Mapping[VehicleStatus, Set[VehicleStatus]]] = {
    VehicleStatus.AVAILABLE: {
        VehicleStatus.RESERVED,
        VehicleStatus.IN_SERVICE,
        VehicleStatus.IN_WASH,
        VehicleStatus.DECOMMISSIONED,
    },
    VehicleStatus.RESERVED: {
        VehicleStatus.RENTED,
        VehicleStatus.AVAILABLE,
    },
    VehicleStatus.RENTED: {
        VehicleStatus.RETURNING,
    },
    VehicleStatus.RETURNING: {
        VehicleStatus.AVAILABLE,
        VehicleStatus.IN_SERVICE,
        VehicleStatus.IN_WASH,
    },
    VehicleStatus.IN_SERVICE: {
        VehicleStatus.AVAILABLE,
        VehicleStatus.DECOMMISSIONED,
    },
    VehicleStatus.IN_WASH: {
        VehicleStatus.AVAILABLE,
    },
    VehicleStatus.DECOMMISSIONED: set(),
}


@dataclass(frozen=True, slots=True, kw_only=True)
class ChangeVehicleStatusRequest:
    vehicle_id: UUID
    status: VehicleStatus


class ChangeVehicleStatus:
    def __init__(
        self,
        current_user_service: CurrentUserService,
        utc_timer: UtcTimer,
        vehicle_tx_storage: VehicleTxStorage,
        transaction_manager: TransactionManager,
    ) -> None:
        self._current_user_service = current_user_service
        self._utc_timer = utc_timer
        self._vehicle_tx_storage = vehicle_tx_storage
        self._transaction_manager = transaction_manager

    async def execute(self, request: ChangeVehicleStatusRequest) -> None:
        logger.info("Change vehicle status: started.")

        current_user = await self._current_user_service.get_current_user()
        authorize(
            HasPermission(),
            context=PermissionCheckContext(
                subject=current_user,
                required_permission="fleet.update",
            ),
        )

        vehicle_id = VehicleId(request.vehicle_id)
        vehicle = await self._vehicle_tx_storage.get_by_id(vehicle_id, for_update=True)
        if vehicle is None:
            raise VehicleNotFoundError

        allowed = VALID_TRANSITIONS.get(vehicle.status, set())
        if request.status not in allowed:
            raise InvalidVehicleStatusTransitionError(
                f"Cannot transition from '{vehicle.status}' to '{request.status}'."
            )

        vehicle.status = request.status
        vehicle.updated_at = UtcDatetime(self._utc_timer.now.value)
        await self._transaction_manager.commit()

        logger.info("Change vehicle status: done.")
