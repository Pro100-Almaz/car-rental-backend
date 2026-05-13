from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID


@dataclass(frozen=True, slots=True)
class VehicleQm:
    id: UUID
    organization_id: UUID
    nickname: str | None
    make: str
    model: str
    year: int
    vin: str | None
    license_plate: str
    color: str
    category: str
    status: str
    fuel_type: str
    transmission: str
    current_mileage: int
    purchase_price: Decimal | None
    purchase_date: date | None
    insurance_expiry: date | None
    inspection_expiry: date | None
    gps_device_id: str | None
    current_latitude: Decimal | None
    current_longitude: Decimal | None
    current_fuel_level: int | None
    branch_id: UUID | None
    photos: list[str] | None
    features: dict[str, Any] | None
    pricing_override: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime
