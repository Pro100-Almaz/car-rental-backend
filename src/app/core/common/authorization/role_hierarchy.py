from collections.abc import Mapping
from typing import Final

from app.core.common.entities.types_ import UserRole

ROLE_HIERARCHY: Final[Mapping[UserRole, set[UserRole]]] = {
    UserRole.SUPER_ADMIN: {
        UserRole.OWNER,
        UserRole.BRANCH_MANAGER,
        UserRole.DISPATCHER,
        UserRole.FINANCE,
        UserRole.FIELD_STAFF,
        UserRole.CLIENT,
    },
    UserRole.OWNER: {
        UserRole.BRANCH_MANAGER,
        UserRole.DISPATCHER,
        UserRole.FINANCE,
        UserRole.FIELD_STAFF,
    },
    UserRole.BRANCH_MANAGER: {
        UserRole.DISPATCHER,
        UserRole.FINANCE,
        UserRole.FIELD_STAFF,
    },
    UserRole.DISPATCHER: set(),
    UserRole.FINANCE: set(),
    UserRole.FIELD_STAFF: set(),
    UserRole.CLIENT: set(),
}
