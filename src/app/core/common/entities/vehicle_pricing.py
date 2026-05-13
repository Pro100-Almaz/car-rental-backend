from datetime import date
from decimal import Decimal

from app.core.common.entities.base import Entity
from app.core.common.entities.types_ import VehicleId, VehiclePricingId
from app.core.common.value_objects.utc_datetime import UtcDatetime


class VehiclePricing(Entity[VehiclePricingId]):
    def __init__(
        self,
        *,
        id_: VehiclePricingId,
        vehicle_id: VehicleId,
        base_daily_rate: Decimal,
        name: str,
        multiplier: Decimal,
        valid_from: date,
        valid_to: date,
        is_active: bool,
        created_at: UtcDatetime,
    ) -> None:
        super().__init__(id_=id_)
        self.vehicle_id = vehicle_id
        self.base_daily_rate = base_daily_rate
        self.name = name
        self.multiplier = multiplier
        self.valid_from = valid_from
        self.valid_to = valid_to
        self.is_active = is_active
        self._created_at = created_at

    @property
    def created_at(self) -> UtcDatetime:
        return self._created_at
