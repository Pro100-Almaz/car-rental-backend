from datetime import datetime

from app.core.common.entities.base import Entity
from app.core.common.entities.types_ import BranchId, OrganizationId, UserId, UserPasswordHash, UserRole
from app.core.common.value_objects.email import Email
from app.core.common.value_objects.utc_datetime import UtcDatetime


class User(Entity[UserId]):
    def __init__(
        self,
        *,
        id_: UserId,
        organization_id: OrganizationId,
        email: Email,
        phone: str | None,
        password_hash: UserPasswordHash,
        role: UserRole,
        first_name: str,
        last_name: str,
        is_active: bool,
        last_login_at: datetime | None,
        branch_id: BranchId | None,
        created_at: UtcDatetime,
        updated_at: UtcDatetime,
    ) -> None:
        super().__init__(id_=id_)
        self.organization_id = organization_id
        self.email = email
        self.phone = phone
        self.password_hash = password_hash
        self.role = role
        self.first_name = first_name
        self.last_name = last_name
        self.is_active = is_active
        self.last_login_at = last_login_at
        self.branch_id = branch_id
        self._created_at = created_at
        self.updated_at = updated_at

    @property
    def created_at(self) -> UtcDatetime:
        return self._created_at
