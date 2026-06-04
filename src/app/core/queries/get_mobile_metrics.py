import logging
from dataclasses import dataclass
from uuid import UUID

from app.core.common.authorization.authorize import authorize
from app.core.common.authorization.current_user_service import CurrentUserService
from app.core.common.authorization.rbac import HasPermission, PermissionCheckContext
from app.core.queries.models.mobile_metrics import MobileMetricsQm
from app.core.queries.ports.mobile_metrics_reader import MobileMetricsReader

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class GetMobileMetricsRequest:
    organization_id: UUID


class GetMobileMetrics:
    def __init__(
        self,
        current_user_service: CurrentUserService,
        mobile_metrics_reader: MobileMetricsReader,
    ) -> None:
        self._current_user_service = current_user_service
        self._mobile_metrics_reader = mobile_metrics_reader

    async def execute(self, request: GetMobileMetricsRequest) -> MobileMetricsQm:
        logger.info("Get mobile metrics: started.")

        current_user = await self._current_user_service.get_current_user()
        authorize(
            HasPermission(),
            context=PermissionCheckContext(
                subject=current_user,
                required_permission="analytics.*",
            ),
        )

        return await self._mobile_metrics_reader.get_metrics(
            organization_id=request.organization_id,
        )
