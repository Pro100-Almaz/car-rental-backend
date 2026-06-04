import logging
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.core.common.authorization.authorize import authorize
from app.core.common.authorization.current_user_service import CurrentUserService
from app.core.common.authorization.rbac import HasPermission, PermissionCheckContext
from app.core.queries.ports.mobile_vehicle_reader import MobileVehicleReader, VehicleAvailabilityQm

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class GetVehicleAvailabilityRequest:
    vehicle_id: UUID
    scheduled_start: datetime
    scheduled_end: datetime


class GetVehicleAvailability:
    def __init__(
        self,
        current_user_service: CurrentUserService,
        mobile_vehicle_reader: MobileVehicleReader,
    ) -> None:
        self._current_user_service = current_user_service
        self._mobile_vehicle_reader = mobile_vehicle_reader

    async def execute(self, request: GetVehicleAvailabilityRequest) -> VehicleAvailabilityQm:
        logger.info("Get vehicle availability: started.")

        current_user = await self._current_user_service.get_current_user()
        authorize(
            HasPermission(),
            context=PermissionCheckContext(
                subject=current_user,
                required_permission="mobile.vehicles",
            ),
        )

        result = await self._mobile_vehicle_reader.check_availability(
            vehicle_id=request.vehicle_id,
            scheduled_start=request.scheduled_start,
            scheduled_end=request.scheduled_end,
        )

        logger.info("Get vehicle availability: done.")
        return result
