import logging
from dataclasses import dataclass
from typing import TypedDict
from uuid import UUID

from app.core.commands.change_vehicle_status import VALID_TRANSITIONS
from app.core.commands.ports.transaction_manager import TransactionManager
from app.core.commands.ports.utc_timer import UtcTimer
from app.core.commands.ports.vehicle_tx_storage import VehicleTxStorage
from app.core.common.authorization.authorize import authorize
from app.core.common.authorization.current_user_service import CurrentUserService
from app.core.common.authorization.rbac import HasPermission, PermissionCheckContext
from app.core.common.entities.types_ import VehicleId, VehicleStatus
from app.core.common.value_objects.utc_datetime import UtcDatetime

logger = logging.getLogger(__name__)


class BulkStatusResultItem(TypedDict):
    vehicle_id: UUID
    success: bool
    error: str | None


@dataclass(frozen=True, slots=True, kw_only=True)
class BulkChangeVehicleStatusRequest:
    vehicle_ids: list[UUID]
    status: VehicleStatus


class BulkChangeVehicleStatusResponse(TypedDict):
    results: list[BulkStatusResultItem]
    succeeded: int
    failed: int


class BulkChangeVehicleStatus:
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

    async def execute(self, request: BulkChangeVehicleStatusRequest) -> BulkChangeVehicleStatusResponse:
        logger.info("Bulk change vehicle status: started.")

        current_user = await self._current_user_service.get_current_user()
        authorize(
            HasPermission(),
            context=PermissionCheckContext(
                subject=current_user,
                required_permission="fleet.update",
            ),
        )

        now = UtcDatetime(self._utc_timer.now.value)
        results: list[BulkStatusResultItem] = []
        succeeded = 0
        failed = 0

        for vid in request.vehicle_ids:
            vehicle = await self._vehicle_tx_storage.get_by_id(VehicleId(vid), for_update=True)
            if vehicle is None:
                results.append(BulkStatusResultItem(vehicle_id=vid, success=False, error="Vehicle not found"))
                failed += 1
                continue

            allowed = VALID_TRANSITIONS.get(vehicle.status, set())
            if request.status not in allowed:
                results.append(
                    BulkStatusResultItem(
                        vehicle_id=vid,
                        success=False,
                        error=f"Cannot transition from '{vehicle.status}' to '{request.status}'",
                    )
                )
                failed += 1
                continue

            vehicle.status = request.status
            vehicle.updated_at = now
            results.append(BulkStatusResultItem(vehicle_id=vid, success=True, error=None))
            succeeded += 1

        await self._transaction_manager.commit()

        logger.info("Bulk change vehicle status: done. succeeded=%d, failed=%d", succeeded, failed)
        return BulkChangeVehicleStatusResponse(results=results, succeeded=succeeded, failed=failed)
