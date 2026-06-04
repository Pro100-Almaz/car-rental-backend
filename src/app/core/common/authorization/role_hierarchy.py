from collections.abc import Mapping
from typing import Final

from app.core.common.entities.types_ import UserRole

ROLE_HIERARCHY: Final[Mapping[UserRole, set[UserRole]]] = {
    UserRole.SUPER_ADMIN: {
        UserRole.ADMIN,
        UserRole.BOOKING_MANAGER,
        UserRole.FINANCIAL_MANAGER,
        UserRole.INVESTOR,
        UserRole.TECHNICIAN,
        UserRole.CLIENT,
    },
    UserRole.ADMIN: {
        UserRole.BOOKING_MANAGER,
        UserRole.FINANCIAL_MANAGER,
        UserRole.INVESTOR,
        UserRole.TECHNICIAN,
        UserRole.CLIENT,
    },
    UserRole.BOOKING_MANAGER: set(),
    UserRole.FINANCIAL_MANAGER: set(),
    UserRole.INVESTOR: set(),
    UserRole.TECHNICIAN: set(),
    UserRole.CLIENT: set(),
}
