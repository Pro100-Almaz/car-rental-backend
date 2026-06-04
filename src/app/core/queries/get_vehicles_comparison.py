import logging
from dataclasses import dataclass
from datetime import date
from uuid import UUID

from app.core.queries.models.report_vehicles_comparison import VehiclesComparisonQm
from app.core.queries.ports.report_reader import ReportReader

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class GetVehiclesComparisonRequest:
    organization_id: UUID
    date_from: date
    date_to: date


class GetVehiclesComparison:
    def __init__(
        self,
        report_reader: ReportReader,
    ) -> None:
        self._report_reader = report_reader

    async def execute(self, request: GetVehiclesComparisonRequest) -> VehiclesComparisonQm:
        logger.info("Get vehicles comparison: started.")

        result = await self._report_reader.get_vehicles_comparison(
            organization_id=request.organization_id,
            date_from=request.date_from,
            date_to=request.date_to,
        )

        logger.info("Get vehicles comparison: done.")
        return result
