import calendar
import logging
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from uuid import UUID

from app.core.queries.models.dashboard_kpis import DashboardKpisQm
from app.core.queries.ports.dashboard_reader import DashboardReader

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class GetDashboardKpisRequest:
    organization_id: UUID
    date_from: date
    date_to: date
    now: datetime


class GetDashboardKpis:
    def __init__(self, dashboard_reader: DashboardReader) -> None:
        self._dashboard_reader = dashboard_reader

    async def execute(self, request: GetDashboardKpisRequest) -> DashboardKpisQm:
        logger.info("Get dashboard KPIs: started.")

        prev_date_from, prev_date_to = self._previous_period(request.date_from, request.date_to)

        result = await self._dashboard_reader.get_kpis(
            organization_id=request.organization_id,
            date_from=request.date_from,
            date_to=request.date_to,
            prev_date_from=prev_date_from,
            prev_date_to=prev_date_to,
            now=request.now,
        )

        logger.info("Get dashboard KPIs: done.")
        return result

    @staticmethod
    def _previous_period(d_from: date, d_to: date) -> tuple[date, date]:
        days = (d_to - d_from).days + 1
        if days >= 28 and d_from.day == 1:
            if d_from.month == 1:
                prev_year, prev_month = d_from.year - 1, 12
            else:
                prev_year, prev_month = d_from.year, d_from.month - 1
            prev_from = date(prev_year, prev_month, 1)
            prev_to = date(prev_year, prev_month, calendar.monthrange(prev_year, prev_month)[1])
            return prev_from, prev_to
        prev_to = d_from - timedelta(days=1)
        prev_from = prev_to - timedelta(days=days - 1)
        return prev_from, prev_to
