from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class ExpenseCategoryQm:
    id: UUID
    organization_id: UUID
    name: str
    type_: str
    is_system: bool
    sort_order: int
    is_active: bool
    created_at: datetime
