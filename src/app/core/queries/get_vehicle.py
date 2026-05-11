import logging
from dataclasses import dataclass
from uuid import UUID

from app.core.queries.models.vehicle import VehicleQm
from app.core.queries.ports.vehicle_reader import VehicleReader

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class GetVehicleRequest:
    vehicle_id: UUID


class GetVehicle:
    def __init__(
        self,
        vehicle_reader: VehicleReader,
    ) -> None:
        self._vehicle_reader = vehicle_reader

    async def execute(self, request: GetVehicleRequest) -> VehicleQm | None:
        logger.info("Get vehicle: started.")

        result = await self._vehicle_reader.get_by_id(
            vehicle_id=request.vehicle_id,
        )

        logger.info("Get vehicle: done.")
        return result
