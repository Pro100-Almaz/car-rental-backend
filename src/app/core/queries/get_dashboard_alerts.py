import logging
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.core.queries.models.dashboard_alerts import DashboardAlertsQm
from app.core.queries.ports.dashboard_reader import DashboardReader

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class GetDashboardAlertsRequest:
    organization_id: UUID
    now: datetime


class GetDashboardAlerts:
    def __init__(self, dashboard_reader: DashboardReader) -> None:
        self._dashboard_reader = dashboard_reader

    async def execute(self, request: GetDashboardAlertsRequest) -> DashboardAlertsQm:
        logger.info("Get dashboard alerts: started.")

        result = await self._dashboard_reader.get_alerts(
            organization_id=request.organization_id,
            now=request.now,
        )

        logger.info("Get dashboard alerts: done.")
        return result
