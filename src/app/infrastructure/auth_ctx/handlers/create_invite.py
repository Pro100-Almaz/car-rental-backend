import logging
import secrets
from dataclasses import dataclass
from datetime import timedelta
from typing import TypedDict
from uuid import UUID, uuid4

from app.core.commands.ports.transaction_manager import TransactionManager
from app.core.commands.ports.utc_timer import UtcTimer
from app.core.common.authorization.authorize import authorize
from app.core.common.authorization.current_user_service import CurrentUserService
from app.core.common.authorization.permissions import CanManageRole, RoleManagementContext
from app.core.common.authorization.rbac import HasPermission, PermissionCheckContext
from app.core.common.entities.types_ import UserRole
from app.core.common.ports.email_sender import EmailSender
from app.core.common.value_objects.utc_datetime import UtcDatetime
from app.infrastructure.auth_ctx.invite import Invite
from app.infrastructure.auth_ctx.sqla_invite_tx_storage import InviteSqlaTxStorage

logger = logging.getLogger(__name__)

INVITE_TTL = timedelta(days=7)


@dataclass(frozen=True, slots=True, kw_only=True)
class CreateInviteRequest:
    email: str
    role: str
    frontend_base_url: str


class CreateInviteResponse(TypedDict):
    id: UUID
    token: str
    invite_url: str


class CreateInvite:
    def __init__(
        self,
        current_user_service: CurrentUserService,
        utc_timer: UtcTimer,
        invite_tx_storage: InviteSqlaTxStorage,
        transaction_manager: TransactionManager,
        email_sender: EmailSender,
    ) -> None:
        self._current_user_service = current_user_service
        self._utc_timer = utc_timer
        self._invite_tx_storage = invite_tx_storage
        self._transaction_manager = transaction_manager
        self._email_sender = email_sender

    async def execute(self, request: CreateInviteRequest) -> CreateInviteResponse:
        logger.info("Create invite: started.")

        current_user = await self._current_user_service.get_current_user()
        authorize(
            HasPermission(),
            context=PermissionCheckContext(
                subject=current_user,
                required_permission="invites.create",
            ),
        )

        target_role = UserRole(request.role)
        authorize(
            CanManageRole(),
            context=RoleManagementContext(
                subject=current_user,
                target_role=target_role,
            ),
        )

        now = self._utc_timer.now
        token = secrets.token_urlsafe(48)
        invite = Invite(
            id_=uuid4(),
            organization_id=current_user.organization_id,
            email=request.email,
            role=target_role,
            token=token,
            invited_by=current_user.id_,
            expires_at=UtcDatetime(now.value + INVITE_TTL),
            used_at=None,
            created_at=now,
        )
        self._invite_tx_storage.add(invite)
        await self._transaction_manager.commit()

        invite_url = f"{request.frontend_base_url.rstrip('/')}/signup?invite={token}"

        await self._email_sender.send(
            to=request.email,
            subject="You've been invited to join the platform",
            body=(
                f"You have been invited to join as {target_role.value.replace('_', ' ')}.\n\n"
                f"Click the link below to create your account:\n{invite_url}\n\n"
                "This invite expires in 7 days."
            ),
        )

        logger.info("Create invite: done. Email sent to %s.", request.email)
        return CreateInviteResponse(
            id=invite.id_,
            token=token,
            invite_url=invite_url,
        )
