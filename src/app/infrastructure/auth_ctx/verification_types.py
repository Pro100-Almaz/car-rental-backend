from datetime import timedelta
from typing import NewType

VerificationCodeTtl = NewType("VerificationCodeTtl", timedelta)
ResendCooldown = NewType("ResendCooldown", timedelta)
