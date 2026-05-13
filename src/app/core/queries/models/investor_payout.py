from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True, slots=True)
class InvestorPayoutQm:
    id: UUID
    organization_id: UUID
    investor_id: UUID
    period_month: date
    calculated_profit: Decimal
    share_amount: Decimal
    status: str
    paid_at: datetime | None
    notes: str | None
    created_at: datetime
