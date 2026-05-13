from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any, TypedDict
from uuid import UUID


@dataclass(frozen=True, slots=True, kw_only=True)
class VehicleTimelineEventQm:
    id: UUID
    event_type: str
    event_date: datetime
    title: str
    description: str | None
    amount: Decimal | None
    metadata: dict[str, Any] | None


class VehicleTimelineQm(TypedDict):
    events: list[VehicleTimelineEventQm]
    total: int
