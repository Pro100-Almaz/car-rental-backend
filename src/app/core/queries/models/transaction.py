from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID


@dataclass(frozen=True, slots=True)
class TransactionQm:
    id: UUID
    organization_id: UUID
    rental_id: UUID | None
    client_id: UUID
    type: str
    amount: Decimal
    currency: str
    payment_method: str
    status: str
    external_id: str | None
    metadata: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime
