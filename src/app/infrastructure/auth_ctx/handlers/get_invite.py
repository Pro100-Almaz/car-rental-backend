import logging
from dataclasses import dataclass
from typing import TypedDict

from app.core.commands.ports.utc_timer import UtcTimer
from app.infrastructure.auth_ctx.exceptions import InvalidInviteError, InviteAlreadyUsedError
from app.infrastructure.auth_ctx.sqla_invite_tx_storage import InviteSqlaTxStorage

logger = logging.getLogger(__name__)


class GetInviteResponse(TypedDict):
    email: str
    role: str
    organization_id: str


class GetInvite:
    def __init__(
        self,
        utc_timer: UtcTimer,
        invite_tx_storage: InviteSqlaTxStorage,
    ) -> None:
        self._utc_timer = utc_timer
        self._invite_tx_storage = invite_tx_storage

    async def execute(self, token: str) -> GetInviteResponse:
        logger.info("Get invite: started.")

        invite = await self._invite_tx_storage.get_by_token(token)
        if invite is None:
            raise InvalidInviteError

        if invite.used_at is not None:
            raise InviteAlreadyUsedError

        now = self._utc_timer.now
        if invite.expires_at.value < now.value:
            raise InvalidInviteError

        logger.info("Get invite: done.")
        return GetInviteResponse(
            email=invite.email,
            role=invite.role.value,
            organization_id=str(invite.organization_id),
        )
