from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import TypedDict
from uuid import UUID


@dataclass(frozen=True, slots=True)
class ReturnsQueueItemQm:
    rental_id: UUID
    vehicle_id: UUID
    vehicle_nickname: str | None
    vehicle_license_plate: str
    client_id: UUID
    client_name: str
    status: str
    scheduled_start: datetime
    scheduled_end: datetime
    estimated_total: Decimal
    is_overdue: bool


class ReturnsQueueQm(TypedDict):
    items: list[ReturnsQueueItemQm]
    total: int
