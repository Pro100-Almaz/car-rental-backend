import logging
from dataclasses import dataclass
from uuid import UUID

from app.core.common.authorization.authorize import authorize
from app.core.common.authorization.current_user_service import CurrentUserService
from app.core.common.authorization.rbac import HasPermission, PermissionCheckContext
from app.core.queries.models.mobile_vehicle import MobileVehicleQm
from app.core.queries.ports.mobile_vehicle_reader import MobileVehicleReader

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class GetMobileVehicleRequest:
    organization_id: UUID
    vehicle_id: UUID


class GetMobileVehicle:
    def __init__(
        self,
        current_user_service: CurrentUserService,
        mobile_vehicle_reader: MobileVehicleReader,
    ) -> None:
        self._current_user_service = current_user_service
        self._mobile_vehicle_reader = mobile_vehicle_reader

    async def execute(self, request: GetMobileVehicleRequest) -> MobileVehicleQm | None:
        logger.info("Get mobile vehicle: started.")

        current_user = await self._current_user_service.get_current_user()
        authorize(
            HasPermission(),
            context=PermissionCheckContext(
                subject=current_user,
                required_permission="mobile.vehicles",
            ),
        )

        result = await self._mobile_vehicle_reader.get_by_id(
            vehicle_id=request.vehicle_id,
            organization_id=request.organization_id,
        )

        logger.info("Get mobile vehicle: done.")
        return result
