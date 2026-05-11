from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True, slots=True)
class FineQm:
    id: UUID
    organization_id: UUID
    vehicle_id: UUID
    rental_id: UUID | None
    client_id: UUID | None
    fine_type: str
    amount: Decimal
    description: str | None
    fine_date: date
    document_url: str | None
    status: str
    created_at: datetime
    updated_at: datetime
