import logging
from dataclasses import dataclass
from datetime import date
from uuid import UUID

from app.core.queries.models.dashboard_revenue_chart import DashboardRevenueChartQm
from app.core.queries.ports.dashboard_reader import DashboardReader

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class GetDashboardRevenueChartRequest:
    organization_id: UUID
    date_from: date
    date_to: date


class GetDashboardRevenueChart:
    def __init__(self, dashboard_reader: DashboardReader) -> None:
        self._dashboard_reader = dashboard_reader

    async def execute(self, request: GetDashboardRevenueChartRequest) -> DashboardRevenueChartQm:
        logger.info("Get dashboard revenue chart: started.")

        result = await self._dashboard_reader.get_revenue_chart(
            organization_id=request.organization_id,
            date_from=request.date_from,
            date_to=request.date_to,
        )

        logger.info("Get dashboard revenue chart: done.")
        return result
