import fnmatch
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Final

from app.core.common.authorization.base import Permission, PermissionContext
from app.core.common.entities.types_ import UserRole
from app.core.common.entities.user import User

PERMISSIONS: Final[Mapping[UserRole, Sequence[str]]] = {
    UserRole.SUPER_ADMIN: ["*"],
    UserRole.ADMIN: [
        "fleet.*",
        "rental.*",
        "client.*",
        "comms.*",
        "tasks.*",
        "analytics.*",
        "finance.*",
        "investors.*",
        "maintenance.*",
        "users.*",
        "invites.*",
        "settings.*",
    ],
    UserRole.BOOKING_MANAGER: [
        "fleet.read",
        "fleet.status.limited",
        "fleet.photos.upload",
        "fleet.docs.upload",
        "rental.*",
        "client.read",
        "client.create",
        "client.edit",
        "client.docs.upload",
        "comms.*",
        "tasks.*",
        "finance.cash_journal.read",
        "finance.cash_journal.create",
    ],
    UserRole.FINANCIAL_MANAGER: [
        "fleet.read",
        "rental.read",
        "client.read",
        "finance.*",
        "investors.read",
        "investors.payout.create",
        "investors.payout.approve",
        "analytics.*",
        "settings.expense_categories",
    ],
    UserRole.INVESTOR: [
        "fleet.own.read",
        "analytics.own.read",
        "investors.own.read",
        "investors.own.payouts.read",
        "investors.own.export",
    ],
    UserRole.TECHNICIAN: [
        "fleet.read",
        "maintenance.*",
    ],
    UserRole.CLIENT: [
        "mobile.*",
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
