from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True, slots=True)
class BranchQm:
    id: UUID
    organization_id: UUID
    name: str
    address: str
    latitude: Decimal | None
    longitude: Decimal | None
    timezone: str
    created_at: datetime
