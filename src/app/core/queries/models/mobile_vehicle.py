from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID


@dataclass(frozen=True, slots=True)
class MobileVehicleQm:
    id: UUID
    organization_id: UUID
    nickname: str | None
    make: str
    model: str
    year: int
    license_plate: str
    color: str
    category: str
    status: str
    fuel_type: str
    transmission: str
    branch_id: UUID | None
    photos: list[str] | None
    features: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime
