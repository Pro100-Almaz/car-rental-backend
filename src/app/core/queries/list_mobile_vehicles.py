import logging
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.core.common.authorization.authorize import authorize
from app.core.common.authorization.current_user_service import CurrentUserService
from app.core.common.authorization.rbac import HasPermission, PermissionCheckContext
from app.core.queries.ports.mobile_vehicle_reader import ListMobileVehiclesQm, MobileVehicleReader

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class ListMobileVehiclesRequest:
    organization_id: UUID
    category: str | None = None
    fuel_type: str | None = None
    transmission: str | None = None
    branch_id: UUID | None = None
    search: str | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None


class ListMobileVehicles:
    def __init__(
        self,
        current_user_service: CurrentUserService,
        mobile_vehicle_reader: MobileVehicleReader,
    ) -> None:
        self._current_user_service = current_user_service
        self._mobile_vehicle_reader = mobile_vehicle_reader

    async def execute(self, request: ListMobileVehiclesRequest) -> ListMobileVehiclesQm:
        logger.info("List mobile vehicles: started.")

        current_user = await self._current_user_service.get_current_user()
        authorize(
            HasPermission(),
            context=PermissionCheckContext(
                subject=current_user,
                required_permission="mobile.vehicles",
            ),
        )

        result = await self._mobile_vehicle_reader.list_available(
            organization_id=request.organization_id,
            category=request.category,
            fuel_type=request.fuel_type,
            transmission=request.transmission,
            branch_id=request.branch_id,
            search=request.search,
            date_from=request.date_from,
            date_to=request.date_to,
        )

        logger.info("List mobile vehicles: done.")
        return result
