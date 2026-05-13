import logging
from dataclasses import dataclass
from uuid import UUID

from app.core.queries.models.vehicle_pricing import VehiclePricingQm
from app.core.queries.ports.vehicle_pricing_reader import VehiclePricingReader

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class GetVehiclePricingRequest:
    vehicle_pricing_id: UUID


class GetVehiclePricing:
    def __init__(
        self,
        vehicle_pricing_reader: VehiclePricingReader,
    ) -> None:
        self._vehicle_pricing_reader = vehicle_pricing_reader

    async def execute(self, request: GetVehiclePricingRequest) -> VehiclePricingQm | None:
        logger.info("Get vehicle pricing: started.")

        result = await self._vehicle_pricing_reader.get_by_id(
            vehicle_pricing_id=request.vehicle_pricing_id,
        )

        logger.info("Get vehicle pricing: done.")
        return result
