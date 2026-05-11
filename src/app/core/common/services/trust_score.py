from typing import Final

from app.core.common.entities.types_ import TrustLevel

VIP_THRESHOLD: Final[int] = 100
TRUSTED_THRESHOLD: Final[int] = 50
VERIFIED_THRESHOLD: Final[int] = 20

TRUST_EVENTS: Final[dict[str, int]] = {
    "rental_completed": +5,
    "on_time_return": +3,
    "late_return": -5,
    "late_return_severe": -15,
    "clean_return": +2,
    "dirty_return": -3,
    "no_damage": +2,
    "damage_reported": -10,
    "fine_incurred": -5,
    "dispute_filed": -8,
    "dispute_resolved": +3,
    "debt_paid_on_time": +4,
    "debt_overdue": -20,
    "document_verified": +10,
}


def get_trust_level(score: int) -> TrustLevel:
    if score >= VIP_THRESHOLD:
        return TrustLevel.VIP
    if score >= TRUSTED_THRESHOLD:
        return TrustLevel.TRUSTED
    if score >= VERIFIED_THRESHOLD:
        return TrustLevel.VERIFIED
    return TrustLevel.NEW
