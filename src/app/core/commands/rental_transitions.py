from collections.abc import Mapping, Set
from typing import Final

from app.core.common.entities.types_ import RentalStatus

VALID_RENTAL_TRANSITIONS: Final[Mapping[RentalStatus, Set[RentalStatus]]] = {
    RentalStatus.PENDING: {
        RentalStatus.CONFIRMED,
        RentalStatus.CANCELLED,
    },
    RentalStatus.CONFIRMED: {
        RentalStatus.ACTIVE,
        RentalStatus.CANCELLED,
    },
    RentalStatus.ACTIVE: {
        RentalStatus.RETURNING,
    },
    RentalStatus.RETURNING: {
        RentalStatus.COMPLETED,
        RentalStatus.DISPUTED,
    },
    RentalStatus.COMPLETED: {
        RentalStatus.DISPUTED,
    },
    RentalStatus.CANCELLED: set(),
    RentalStatus.DISPUTED: set(),
}
