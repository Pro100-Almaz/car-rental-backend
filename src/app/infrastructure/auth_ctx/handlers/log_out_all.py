"""LogOutAll handler — revokes every active session for the current user.

Combines two operations in a single auth-context transaction:
1. Revoke all non-expired refresh tokens for the user.
2. Insert every ``issued_access_jti`` from those tokens into
   ``revoked_access_jtis`` so that still-valid access tokens are immediately
   denied by the JTI denylist check.

This is also called internally by :class:`ChangePassword` and
:class:`ResetPassword` so that all existing sessions are terminated when
credentials change.
"""

import logging

from app.infrastructure.auth_ctx.exceptions import AuthenticationError
from app.infrastructure.auth_ctx.jwt_processor import JwtProcessor
from app.infrastructure.auth_ctx.service import AuthService

logger = logging.getLogger(__name__)


class LogOutAll:
    """
    - Revokes **all** active sessions for the authenticated user.
    - Each active refresh-token's ``issued_access_jti`` is also denylisted so
      that any outstanding access tokens are immediately rejected.
    - Bearer token required.
    """

    def __init__(
        self,
        jwt_processor: JwtProcessor,
        auth_service: AuthService,
    ) -> None:
        self._jwt_processor = jwt_processor
        self._auth_service = auth_service

    async def execute(self, raw_access_token: str, reason: str = "user_request") -> None:
        logger.info("Log out all: started (reason=%s).", reason)

        claims = self._jwt_processor.decode_access(raw_access_token)
        if claims is None:
            raise AuthenticationError("Invalid access token.")

        await self._auth_service.revoke_all_and_denylist_for_user(
            user_id=claims.sub,
            reason=reason,
        )

        logger.info("Log out all: done (reason=%s).", reason)
