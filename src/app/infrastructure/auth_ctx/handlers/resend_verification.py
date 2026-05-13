import logging
from dataclasses import dataclass
from uuid import uuid4

from app.core.commands.ports.transaction_manager import TransactionManager
from app.core.commands.ports.utc_timer import UtcTimer
from app.core.common.ports.email_sender import EmailSender
from app.core.common.value_objects.email import Email
from app.core.common.value_objects.utc_datetime import UtcDatetime
from app.infrastructure.auth_ctx.code_generator import generate_verification_code
from app.infrastructure.auth_ctx.exceptions import (
    EmailAlreadyVerifiedError,
    InvalidVerificationCodeError,
    VerificationCodeRateLimitError,
)
from app.infrastructure.auth_ctx.sqla_user_tx_storage import AuthSqlaUserTxStorage
from app.infrastructure.auth_ctx.sqla_verification_code_tx_storage import EmailVerificationCodeSqlaTxStorage
from app.infrastructure.auth_ctx.verification_code import EmailVerificationCode
from app.infrastructure.auth_ctx.verification_types import ResendCooldown, VerificationCodeTtl

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class ResendVerificationRequest:
    email: str


class ResendVerification:
    def __init__(
        self,
        utc_timer: UtcTimer,
        user_tx_storage: AuthSqlaUserTxStorage,
        verification_code_tx_storage: EmailVerificationCodeSqlaTxStorage,
        transaction_manager: TransactionManager,
        email_sender: EmailSender,
        code_ttl: VerificationCodeTtl,
        resend_cooldown: ResendCooldown,
    ) -> None:
        self._utc_timer = utc_timer
        self._user_tx_storage = user_tx_storage
        self._verification_code_tx_storage = verification_code_tx_storage
        self._transaction_manager = transaction_manager
        self._email_sender = email_sender
        self._code_ttl = code_ttl
        self._resend_cooldown = resend_cooldown

    async def execute(self, request: ResendVerificationRequest) -> None:
        logger.info("Resend verification: started.")

        email = Email(request.email)
        user = await self._user_tx_storage.get_by_email(email)
        if user is None:
            raise InvalidVerificationCodeError

        if user.email_verified:
            raise EmailAlreadyVerifiedError

        now = self._utc_timer.now
        latest = await self._verification_code_tx_storage.get_latest_for_user(user.id_)
        if latest is not None:
            elapsed = now.value - latest.created_at.value
            if elapsed < self._resend_cooldown:
                raise VerificationCodeRateLimitError

        await self._verification_code_tx_storage.delete_all_for_user(user.id_)

        code = generate_verification_code()
        verification = EmailVerificationCode(
            id_=uuid4(),
            user_id=user.id_,
            code=code,
            expires_at=UtcDatetime(now.value + self._code_ttl),
            created_at=now,
        )
        self._verification_code_tx_storage.add(verification)
        await self._transaction_manager.commit()

        await self._email_sender.send(
            to=email.value,
            subject="Email Verification Code",
            body=f"Your verification code is: {code}\n\nThis code expires in {self._code_ttl.total_seconds() // 60:.0f} minutes.",
        )

        logger.info("Resend verification: done.")
