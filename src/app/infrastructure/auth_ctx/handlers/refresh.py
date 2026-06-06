import logging
from dataclasses import dataclass

from app.infrastructure.auth_ctx.service import AuthService, TokenPair

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class RefreshTokenInput:
    refresh_token: str
    ip: str | None = None
    user_agent: str | None = None


class RefreshTokenHandler:
    """Exchange a valid refresh token for a new token pair (rotation)."""

    def __init__(self, auth_service: AuthService) -> None:
        self._auth_service = auth_service

    async def execute(self, request: RefreshTokenInput) -> TokenPair:
        logger.info("Refresh token: started.")
        pair = await self._auth_service.rotate_refresh(
            request.refresh_token,
            request.ip,
            request.user_agent,
        )
        logger.info("Refresh token: done.")
        return pair
