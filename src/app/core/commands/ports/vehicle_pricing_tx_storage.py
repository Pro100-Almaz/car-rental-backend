from typing import Protocol

from app.core.common.entities.types_ import VehiclePricingId
from app.core.common.entities.vehicle_pricing import VehiclePricing


class VehiclePricingTxStorage(Protocol):
    def add(self, vehicle_pricing: VehiclePricing) -> None: ...

    async def get_by_id(
        self,
        vehicle_pricing_id: VehiclePricingId,
        *,
        for_update: bool = False,
    ) -> VehiclePricing | None: ...
