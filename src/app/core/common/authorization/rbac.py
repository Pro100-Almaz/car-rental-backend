import fnmatch
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Final

from app.core.common.authorization.base import Permission, PermissionContext
from app.core.common.entities.types_ import UserRole
from app.core.common.entities.user import User

PERMISSIONS: Final[Mapping[UserRole, Sequence[str]]] = {
    UserRole.SUPER_ADMIN: ["*"],
    UserRole.OWNER: [
        "fleet.*",
        "rental.*",
        "client.*",
        "comms.*",
        "tasks.*",
        "analytics.*",
        "finance.*",
        "users.*",
        "invites.*",
    ],
    UserRole.BRANCH_MANAGER: [
        "fleet.*",
        "rental.*",
        "client.*",
        "comms.*",
        "tasks.*",
        "analytics.read",
        "users.read",
        "invites.create",
    ],
    UserRole.DISPATCHER: [
        "fleet.read",
        "rental.*",
        "client.read",
        "comms.*",
        "tasks.*",
    ],
    UserRole.FINANCE: [
        "fleet.read",
        "rental.read",
        "client.read",
        "analytics.*",
        "finance.*",
    ],
    UserRole.FIELD_STAFF: [
        "tasks.own.*",
        "fleet.read_assigned",
    ],
    UserRole.CLIENT: [
        "rental.own.*",
        "client.own.*",
    ],
}


def has_permission(user: User, required: str) -> bool:
    user_perms = PERMISSIONS.get(user.role, [])
    return any(fnmatch.fnmatch(required, perm) for perm in user_perms)


@dataclass(frozen=True, slots=True, kw_only=True)
class PermissionCheckContext(PermissionContext):
    subject: User
    required_permission: str


class HasPermission(Permission[PermissionCheckContext]):
    def is_satisfied_by(self, context: PermissionCheckContext) -> bool:
        return has_permission(context.subject, context.required_permission)
