from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID


@dataclass(frozen=True, slots=True)
class ServiceTaskQm:
    id: UUID
    organization_id: UUID
    vehicle_id: UUID
    rental_id: UUID | None
    assigned_to: UUID | None
    task_type: str
    priority: str
    status: str
    description: str | None
    estimated_cost: Decimal | None
    actual_cost: Decimal | None
    proof_photos: list[Any] | None
    notes: str | None
    due_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime
