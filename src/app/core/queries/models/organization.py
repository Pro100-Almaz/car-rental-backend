from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID


@dataclass(frozen=True, slots=True)
class OrganizationQm:
    id: UUID
    name: str
    slug: str
    settings: dict[str, Any] | None
    subscription_plan: str
    created_at: datetime
    updated_at: datetime
