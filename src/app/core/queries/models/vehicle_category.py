from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TypedDict
from uuid import UUID


@dataclass(frozen=True, slots=True, kw_only=True)
class VehicleCategoryQm:
    id: UUID
    organization_id: UUID
    name: str
    sort_order: int
    is_active: bool
    created_at: datetime


class ListVehicleCategoriesQm(TypedDict):
    categories: list[VehicleCategoryQm]
    total: int
