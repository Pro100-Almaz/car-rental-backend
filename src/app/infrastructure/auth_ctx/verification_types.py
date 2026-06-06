from datetime import timedelta
from typing import NewType, TypeAlias
from uuid import UUID

VerificationCodeTtl = NewType("VerificationCodeTtl", timedelta)
ResendCooldown = NewType("ResendCooldown", timedelta)
DefaultOrganizationId: TypeAlias = UUID | None
