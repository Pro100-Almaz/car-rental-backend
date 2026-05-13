import logging
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import TypedDict
from uuid import UUID

from app.core.commands.exceptions import EmailAlreadyExistsError
from app.core.commands.ports.flusher import Flusher
from app.core.commands.ports.transaction_manager import TransactionManager
from app.core.commands.ports.user_tx_storage import UserTxStorage
from app.core.commands.ports.utc_timer import UtcTimer
from app.core.common.authorization.authorize import authorize
from app.core.common.authorization.current_user_service import CurrentUserService
from app.core.common.authorization.permissions import CanManageRole, RoleManagementContext
from app.core.common.entities.types_ import BranchId, OrganizationId, UserRole
from app.core.common.factories.id_factory import create_user_id
from app.core.common.services.user import UserService
from app.core.common.value_objects.email import Email
from app.core.common.value_objects.raw_password import RawPassword

logger = logging.getLogger(__name__)


class UserRoleRequestEnum(StrEnum):
    OWNER = "owner"
    BRANCH_MANAGER = "branch_manager"
    DISPATCHER = "dispatcher"
    FINANCE = "finance"
    FIELD_STAFF = "field_staff"


@dataclass(frozen=True, slots=True, kw_only=True)
class CreateUserRequest:
    organization_id: UUID
    email: str
    phone: str | None
    password: str
    role: UserRoleRequestEnum
    first_name: str
    last_name: str
    branch_id: UUID | None


class CreateUserResponse(TypedDict):
    id: UUID
    created_at: datetime


class CreateUser:
    def __init__(
        self,
        current_user_service: CurrentUserService,
        user_service: UserService,
        utc_timer: UtcTimer,
        user_tx_storage: UserTxStorage,
        flusher: Flusher,
        transaction_manager: TransactionManager,
    ) -> None:
        self._current_user_service = current_user_service
        self._user_service = user_service
        self._utc_timer = utc_timer
        self._user_tx_storage = user_tx_storage
        self._flusher = flusher
        self._transaction_manager = transaction_manager

    async def execute(self, request: CreateUserRequest) -> CreateUserResponse:
        logger.info("Create user: started.")

        current_user = await self._current_user_service.get_current_user()
        role = UserRole(request.role)
        authorize(
            CanManageRole(),
            context=RoleManagementContext(
                subject=current_user,
                target_role=role,
            ),
        )
        email = Email(request.email)
        password = RawPassword(request.password)
        organization_id = OrganizationId(request.organization_id)
        branch_id = BranchId(request.branch_id) if request.branch_id else None

        user = await self._user_service.create_user_with_raw_password(
            user_id=create_user_id(),
            organization_id=organization_id,
            email=email,
            raw_password=password,
            first_name=request.first_name,
            last_name=request.last_name,
            now=self._utc_timer.now,
            role=role,
            phone=request.phone,
            branch_id=branch_id,
        )
        self._user_tx_storage.add(user)
        try:
            await self._flusher.flush()
        except EmailAlreadyExistsError:
            raise

        await self._transaction_manager.commit()

        logger.info("Create user: done.")
        return CreateUserResponse(
            id=user.id_,
            created_at=user.created_at.value,
        )
