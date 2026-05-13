from typing import Protocol, TypedDict
from uuid import UUID

from app.core.queries.models.vehicle_pricing import VehiclePricingQm


class ListVehiclePricingQm(TypedDict):
    items: list[VehiclePricingQm]


class VehiclePricingReader(Protocol):
    async def get_by_id(
        self,
        *,
        vehicle_pricing_id: UUID,
    ) -> VehiclePricingQm | None: ...

    async def list_vehicle_pricing(
        self,
        *,
        vehicle_id: UUID,
        is_active: bool | None = None,
    ) -> ListVehiclePricingQm: ...
