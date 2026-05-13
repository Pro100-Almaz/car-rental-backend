from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class InvestorQm:
    id: UUID
    organization_id: UUID
    full_name: str
    type_: str
    contact_phone: str | None
    contact_email: str | None
    user_id: UUID | None
    notes: str | None
    created_at: datetime
    updated_at: datetime
