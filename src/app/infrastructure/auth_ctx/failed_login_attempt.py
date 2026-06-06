from dataclasses import dataclass, field
from datetime import datetime


@dataclass(eq=False, kw_only=True)
class FailedLoginAttempt:
    id_: int | None = field(default=None)  # filled by DB identity sequence
    email_lower: str = ""
    ip: str = ""
    attempted_at: datetime = field(default_factory=datetime.utcnow)
