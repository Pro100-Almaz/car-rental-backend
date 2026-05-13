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
    id_document_url: str | None
    license_front_url: str | None
    license_back_url: str | None
    verification_status: str
    trust_score: int
    trust_level: str
    is_blacklisted: bool
    blacklist_reason: str | None
    wallet_balance: Decimal
    debt_balance: Decimal
    metadata: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime
