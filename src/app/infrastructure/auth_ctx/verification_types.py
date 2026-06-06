from datetime import timedelta
from typing import NewType
from uuid import UUID

VerificationCodeTtl = NewType("VerificationCodeTtl", timedelta)
ResendCooldown = NewType("ResendCooldown", timedelta)
type DefaultOrganizationId = UUID | None
