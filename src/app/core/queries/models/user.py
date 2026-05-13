from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class UserQm:
    id: UUID
    organization_id: UUID
    email: str
    phone: str | None
    role: str
    first_name: str
    last_name: str
    is_active: bool
    email_verified: bool
    last_login_at: datetime | None
    branch_id: UUID | None
    created_at: datetime
    updated_at: datetime
