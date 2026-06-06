import logging

from app.infrastructure.auth_ctx.bearer_token_reader import BearerTokenReader
from app.infrastructure.auth_ctx.exceptions import AuthenticationError
from app.infrastructure.auth_ctx.jwt_processor import JwtProcessor
from app.infrastructure.auth_ctx.service import AuthService

logger = logging.getLogger(__name__)


class LogOut:
    """
    - Open to authenticated users (bearer required).
    - Revokes the presented refresh token and denylists the access token jti.
    """

    def __init__(
        self,
        bearer_token_reader: BearerTokenReader,
        jwt_processor: JwtProcessor,
        auth_service: AuthService,
    ) -> None:
        self._bearer_token_reader = bearer_token_reader
        self._jwt_processor = jwt_processor
        self._auth_service = auth_service

    async def execute(self, raw_refresh: str | None) -> None:
        logger.info("Log out: started.")

        raw_token = self._bearer_token_reader.read()
        if raw_token is None:
            raise AuthenticationError("No bearer token.")

        claims = self._jwt_processor.decode_access(raw_token)
        if claims is None:
            raise AuthenticationError("Invalid access token.")

        await self._auth_service.logout_current(
            user_id=claims.sub,
            raw_refresh=raw_refresh,
            current_access_jti=claims.jti,
            current_access_exp=claims.exp,
        )

        logger.info("Log out: done.")
