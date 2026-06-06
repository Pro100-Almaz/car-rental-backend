import logging
from dataclasses import dataclass

from app.core.commands.ports.flusher import Flusher
from app.core.commands.ports.transaction_manager import TransactionManager
from app.core.commands.ports.utc_timer import UtcTimer
from app.core.common.services.user import UserService
from app.core.common.value_objects.email import Email
from app.core.common.value_objects.raw_password import RawPassword
from app.infrastructure.auth_ctx.audit_log import emit as audit
from app.infrastructure.auth_ctx.exceptions import InvalidVerificationCodeError
from app.infrastructure.auth_ctx.service import AuthService
from app.infrastructure.auth_ctx.sqla_user_tx_storage import AuthSqlaUserTxStorage
from app.infrastructure.auth_ctx.sqla_verification_code_tx_storage import EmailVerificationCodeSqlaTxStorage

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class ResetPasswordRequest:
    email: str
    code: str
    new_password: str


class ResetPassword:
    def __init__(
        self,
        utc_timer: UtcTimer,
        user_tx_storage: AuthSqlaUserTxStorage,
        verification_code_tx_storage: EmailVerificationCodeSqlaTxStorage,
        user_service: UserService,
        flusher: Flusher,
        transaction_manager: TransactionManager,
        auth_service: AuthService,
    ) -> None:
        self._utc_timer = utc_timer
        self._user_tx_storage = user_tx_storage
        self._verification_code_tx_storage = verification_code_tx_storage
        self._user_service = user_service
        self._flusher = flusher
        self._transaction_manager = transaction_manager
        self._auth_service = auth_service

    async def execute(self, request: ResetPasswordRequest) -> None:
        logger.info("Reset password: started.")

        email = Email(request.email)
        user = await self._user_tx_storage.get_by_email(email)
        if user is None:
            raise InvalidVerificationCodeError

        verification = await self._verification_code_tx_storage.get_latest_for_user(user.id_)
        if verification is None:
            raise InvalidVerificationCodeError

        now = self._utc_timer.now
        if verification.expires_at.value < now.value:
            raise InvalidVerificationCodeError

        if verification.code != request.code:
            raise InvalidVerificationCodeError

        new_password = RawPassword(request.new_password)
        await self._user_service.change_password(user, new_password, now=now)
        await self._verification_code_tx_storage.delete_all_for_user(user.id_)
        await self._flusher.flush()
        await self._transaction_manager.commit()

        # Revoke all sessions so stolen tokens are invalidated
        await self._auth_service.revoke_all_and_denylist_for_user(
            user.id_,
            reason="password_reset",
        )

        audit("auth.password_reset", user_id=user.id_)

        logger.info("Reset password: done.")
