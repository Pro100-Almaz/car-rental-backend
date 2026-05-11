from app.core.common.entities.types_ import BranchId, OrganizationId, UserId, UserPasswordHash, UserRole
from app.core.common.entities.user import User
from app.core.common.exceptions import (
    ActivationChangeNotPermittedError,
    RoleAssignmentNotPermittedError,
    RoleChangeNotPermittedError,
)
from app.core.common.ports.password_hasher import PasswordHasher
from app.core.common.value_objects.email import Email
from app.core.common.value_objects.raw_password import RawPassword
from app.core.common.value_objects.utc_datetime import UtcDatetime


class UserService:
    def __init__(self, password_hasher: PasswordHasher) -> None:
        self._password_hasher = password_hasher

    def create_user(
        self,
        user_id: UserId,
        organization_id: OrganizationId,
        email: Email,
        password_hash: UserPasswordHash,
        *,
        first_name: str,
        last_name: str,
        now: UtcDatetime,
        role: UserRole = UserRole.DISPATCHER,
        is_active: bool = True,
        phone: str | None = None,
        branch_id: BranchId | None = None,
    ) -> User:
        if role.is_system:
            raise RoleAssignmentNotPermittedError
        return User(
            id_=user_id,
            organization_id=organization_id,
            email=email,
            phone=phone,
            password_hash=password_hash,
            role=role,
            first_name=first_name,
            last_name=last_name,
            is_active=is_active,
            last_login_at=None,
            branch_id=branch_id,
            created_at=now,
            updated_at=now,
        )

    async def create_user_with_raw_password(
        self,
        user_id: UserId,
        organization_id: OrganizationId,
        email: Email,
        raw_password: RawPassword,
        *,
        first_name: str,
        last_name: str,
        now: UtcDatetime,
        role: UserRole = UserRole.DISPATCHER,
        is_active: bool = True,
        phone: str | None = None,
        branch_id: BranchId | None = None,
    ) -> User:
        password_hash = await self._password_hasher.hash(raw_password)
        return self.create_user(
            user_id,
            organization_id,
            email,
            password_hash,
            first_name=first_name,
            last_name=last_name,
            now=now,
            role=role,
            is_active=is_active,
            phone=phone,
            branch_id=branch_id,
        )

    async def is_password_valid(self, user: User, raw_password: RawPassword) -> bool:
        return await self._password_hasher.verify(
            raw_password=raw_password,
            hashed_password=user.password_hash,
        )

    async def change_password(
        self,
        user: User,
        raw_password: RawPassword,
        *,
        now: UtcDatetime,
    ) -> None:
        user.password_hash = await self._password_hasher.hash(raw_password)
        user.updated_at = now

    def set_role(
        self,
        user: User,
        *,
        now: UtcDatetime,
        role: UserRole,
    ) -> bool:
        if user.role.is_system:
            raise RoleChangeNotPermittedError
        if role.is_system:
            raise RoleAssignmentNotPermittedError
        if user.role == role:
            return False
        user.role = role
        user.updated_at = now
        return True

    def set_activation(
        self,
        user: User,
        *,
        now: UtcDatetime,
        is_active: bool,
    ) -> bool:
        if user.role.is_system:
            raise ActivationChangeNotPermittedError
        if user.is_active == is_active:
            return False
        user.is_active = is_active
        user.updated_at = now
        return True
