import logging
from dataclasses import dataclass
from uuid import UUID

from app.core.queries.ports.vehicle_pricing_reader import ListVehiclePricingQm, VehiclePricingReader

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class ListVehiclePricingRequest:
    vehicle_id: UUID
    is_active: bool | None = None


class ListVehiclePricing:
    def __init__(
        self,
        vehicle_pricing_reader: VehiclePricingReader,
    ) -> None:
        self._vehicle_pricing_reader = vehicle_pricing_reader

    async def execute(self, request: ListVehiclePricingRequest) -> ListVehiclePricingQm:
        logger.info("List vehicle pricing: started.")

        result = await self._vehicle_pricing_reader.list_vehicle_pricing(
            vehicle_id=request.vehicle_id,
            is_active=request.is_active,
        )

        logger.info("List vehicle pricing: done.")
        return result
