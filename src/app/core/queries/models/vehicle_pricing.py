from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True, slots=True, kw_only=True)
class VehiclePricingQm:
    id: UUID
    vehicle_id: UUID
    base_daily_rate: Decimal
    name: str
    multiplier: Decimal
    valid_from: date
    valid_to: date
    is_active: bool
    created_at: datetime
