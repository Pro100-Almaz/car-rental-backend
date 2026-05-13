from collections.abc import Mapping, Set
from typing import Final

from app.core.common.entities.types_ import PayoutStatus

VALID_PAYOUT_TRANSITIONS: Final[Mapping[PayoutStatus, Set[PayoutStatus]]] = {
    PayoutStatus.CALCULATED: {PayoutStatus.APPROVED},
    PayoutStatus.APPROVED: {PayoutStatus.PAID},
    PayoutStatus.PAID: set(),
}
