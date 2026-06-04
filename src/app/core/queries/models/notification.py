from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID


@dataclass(frozen=True, slots=True)
class NotificationQm:
    id: UUID
    user_id: UUID
    organization_id: UUID
    type: str
    title: str
    body: str
    deep_link: str | None
    metadata: dict[str, Any] | None
    is_read: bool
    read_at: datetime | None
    created_at: datetime
