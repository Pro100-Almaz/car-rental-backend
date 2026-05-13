import logging
from dataclasses import dataclass
from datetime import date
from uuid import UUID

from app.core.queries.models.vehicle_financials import VehicleFinancialsQm
from app.core.queries.ports.vehicle_financials_reader import VehicleFinancialsReader

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class GetVehicleFinancialsRequest:
    vehicle_id: UUID
    date_from: date
    date_to: date


class GetVehicleFinancials:
    def __init__(
        self,
        vehicle_financials_reader: VehicleFinancialsReader,
    ) -> None:
        self._reader = vehicle_financials_reader

    async def execute(self, request: GetVehicleFinancialsRequest) -> VehicleFinancialsQm:
        logger.info("Get vehicle financials: started.")

        result = await self._reader.get_financials(
            vehicle_id=request.vehicle_id,
            date_from=request.date_from,
            date_to=request.date_to,
        )

        logger.info("Get vehicle financials: done.")
        return result
