from dataclasses import dataclass
from uuid import UUID

from app.core.common.entities.types_ import UserRole
from app.core.common.value_objects.utc_datetime import UtcDatetime


@dataclass(eq=False, kw_only=True)
class Invite:
    id_: UUID
    organization_id: UUID
    email: str
    role: UserRole
    token: str
    invited_by: UUID
    expires_at: UtcDatetime
    used_at: UtcDatetime | None
    created_at: UtcDatetime
