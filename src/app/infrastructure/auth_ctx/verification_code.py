from dataclasses import dataclass
from uuid import UUID

from app.core.common.value_objects.utc_datetime import UtcDatetime


@dataclass(eq=False, kw_only=True)
class EmailVerificationCode:
    id_: UUID
    user_id: UUID
    code: str
    expires_at: UtcDatetime
    created_at: UtcDatetime
