from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True, slots=True)
class AdditionalServiceQm:
    id: UUID
    organization_id: UUID
    name: str
    price: Decimal
    is_active: bool
    created_at: datetime
