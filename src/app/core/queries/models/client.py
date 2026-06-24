from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID


@dataclass(frozen=True, slots=True)
class ClientQm:
    id: UUID
    organization_id: UUID
    user_id: UUID | None
    phone: str
    email: str | None
    first_name: str
    last_name: str
    verification_status: str
    trust_score: int
    trust_level: str
    is_blacklisted: bool
    blacklist_reason: str | None
    wallet_balance: Decimal
    debt_balance: Decimal
    registration_source: str
    rejection_reason: str | None
    metadata: dict[str, Any] | None
    email_verified: bool
    created_at: datetime
    updated_at: datetime
