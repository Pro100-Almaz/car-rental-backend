from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True, slots=True)
class CashJournalEntryQm:
    id: UUID
    organization_id: UUID
    date: date
    operation_type: str
    vehicle_id: UUID | None
    rental_id: UUID | None
    expense_category_id: UUID | None
    payment_method: str
    amount: Decimal
    description: str | None
    receipt_url: str | None
    confirmed_by: UUID | None
    confirmed_at: datetime | None
    created_by: UUID
    created_at: datetime
