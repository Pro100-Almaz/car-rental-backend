from datetime import datetime
from decimal import Decimal
from typing import TypedDict
from uuid import UUID


class ExtensionRequestQm(TypedDict):
    id: UUID
    organization_id: UUID
    rental_id: UUID
    client_id: UUID
    new_end_date: datetime
    additional_cost: Decimal
    status: str
    rejection_reason: str | None
    reviewed_by: UUID | None
    reviewed_at: datetime | None
    created_at: datetime


class ListExtensionRequestsQm(TypedDict):
    items: list[ExtensionRequestQm]
    total: int
