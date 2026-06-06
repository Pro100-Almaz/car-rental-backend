from dataclasses import dataclass
from datetime import datetime

from app.core.common.entities.types_ import AccessTokenJti, UserId


@dataclass(eq=False, kw_only=True)
class RevokedAccessJti:
    jti: AccessTokenJti
    user_id: UserId
    expires_at: datetime
