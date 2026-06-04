import logging
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.core.queries.models.dashboard_active_rentals import DashboardActiveRentalsQm
from app.core.queries.ports.dashboard_reader import DashboardReader

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class GetDashboardActiveRentalsRequest:
    organization_id: UUID
    limit: int = 5
    now: datetime = None  # type: ignore[assignment]


class GetDashboardActiveRentals:
    def __init__(self, dashboard_reader: DashboardReader) -> None:
        self._dashboard_reader = dashboard_reader

    async def execute(self, request: GetDashboardActiveRentalsRequest) -> DashboardActiveRentalsQm:
        logger.info("Get dashboard active rentals: started.")

        result = await self._dashboard_reader.get_active_rentals(
            organization_id=request.organization_id,
            limit=request.limit,
            now=request.now,
        )

        logger.info("Get dashboard active rentals: done.")
        return result
