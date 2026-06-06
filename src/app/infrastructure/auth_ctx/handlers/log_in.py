"""LogIn handler with account lockout and structured audit logging.

Lockout rules (sliding window):
- Email-based: >= 10 failed attempts in the last 15 minutes → 423 Locked.
- IP-based:    >= 5  failed attempts from the same IP in the last 5 minutes
               (across any email) → 423 Locked.

On failed attempt: a FailedLoginAttempt row is inserted (email + IP).
On success:        all FailedLoginAttempt rows for that email are deleted.

Constant-time defence: when the email is unknown we still run a dummy bcrypt
verify so that timing does not reveal whether an account exists.
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import bcrypt

from app.core.common.services.user import UserService
from app.core.common.value_objects.email import Email
from app.core.common.value_objects.raw_password import RawPassword
from app.infrastructure.auth_ctx.audit_log import emit as audit
from app.infrastructure.auth_ctx.exceptions import (
    AccountLockedError,
    AuthenticationError,
    EmailNotVerifiedError,
)
from app.infrastructure.auth_ctx.failed_login_attempt import FailedLoginAttempt
from app.infrastructure.auth_ctx.service import AuthService, TokenPair
from app.infrastructure.auth_ctx.sqla_failed_login_attempt_tx_storage import (
    SqlaFailedLoginAttemptTxStorage,
)
from app.infrastructure.auth_ctx.sqla_transaction_manager import AuthSqlaTransactionManager
from app.infrastructure.auth_ctx.sqla_user_tx_storage import AuthSqlaUserTxStorage

logger = logging.getLogger(__name__)

# Lockout thresholds
_EMAIL_WINDOW_MINUTES = 15
_EMAIL_MAX_ATTEMPTS = 10
_IP_WINDOW_MINUTES = 5
_IP_MAX_ATTEMPTS = 5

# A valid bcrypt hash (work factor 4) used for constant-time dummy verify when
# the email does not exist.  Work factor 4 is the minimum bcrypt supports;
# it's fast (~1 ms) but still forces bcrypt execution so timing side-channels
# don't reveal whether an account exists.
_DUMMY_HASH: bytes = b"$2b$04$BQVVZXVbRRphUH5K6Da.Gu0DxU7oBOmk1ihatF7wknq7rhB8AAP2W"


@dataclass(frozen=True, slots=True, kw_only=True)
class LogInRequest:
    email: str
    password: str
    ip: str | None = None
    user_agent: str | None = None


class LogIn:
    def __init__(
        self,
        user_tx_storage: AuthSqlaUserTxStorage,
        user_service: UserService,
        auth_service: AuthService,
        failed_attempt_storage: SqlaFailedLoginAttemptTxStorage,
        transaction_manager: AuthSqlaTransactionManager,
    ) -> None:
        self._user_tx_storage = user_tx_storage
        self._user_service = user_service
        self._auth_service = auth_service
        self._failed_attempt_storage = failed_attempt_storage
        self._transaction_manager = transaction_manager

    async def execute(self, request: LogInRequest) -> TokenPair:
        logger.info("Log in: started.")

        email_lower = request.email.strip().lower()
        ip = request.ip or "unknown"
        ua = request.user_agent

        now = datetime.now(tz=timezone.utc)

        # --- Pre-check: email-based lockout ---
        email_since = now - timedelta(minutes=_EMAIL_WINDOW_MINUTES)
        email_failures = await self._failed_attempt_storage.count_for_email_within(
            email_lower, email_since
        )
        if email_failures >= _EMAIL_MAX_ATTEMPTS:
            audit(
                "auth.login.locked",
                level=logging.WARNING,
                email_lower=email_lower,
                ip=ip,
            )
            raise AccountLockedError

        # --- Pre-check: IP-based lockout ---
        ip_since = now - timedelta(minutes=_IP_WINDOW_MINUTES)
        ip_failures = await self._failed_attempt_storage.count_for_ip_within(ip, ip_since)
        if ip_failures >= _IP_MAX_ATTEMPTS:
            audit(
                "auth.login.locked",
                level=logging.WARNING,
                email_lower=email_lower,
                ip=ip,
            )
            raise AccountLockedError

        email = Email(request.email)
        password = RawPassword(request.password)
        user = await self._user_tx_storage.get_by_email(email)

        if user is None:
            # Constant-time: run a real bcrypt.checkpw (work factor 4) in a thread
            # so timing doesn't reveal whether an account exists.
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(
                None,
                bcrypt.checkpw,
                password.value,
                _DUMMY_HASH,
            )
            await self._record_failure(email_lower, ip)
            audit(
                "auth.login.failure",
                email_lower=email_lower,
                ip=ip,
                user_agent=ua,
                reason="unknown_email",
            )
            raise AuthenticationError

        if not await self._user_service.is_password_valid(user, password):
            await self._record_failure(email_lower, ip)
            audit(
                "auth.login.failure",
                email_lower=email_lower,
                ip=ip,
                user_agent=ua,
                reason="bad_password",
            )
            raise AuthenticationError

        if not user.is_active:
            await self._record_failure(email_lower, ip)
            audit(
                "auth.login.failure",
                email_lower=email_lower,
                ip=ip,
                user_agent=ua,
                reason="inactive",
            )
            raise AuthenticationError

        if not user.email_verified:
            audit(
                "auth.login.failure",
                email_lower=email_lower,
                ip=ip,
                user_agent=ua,
                reason="not_verified",
            )
            raise EmailNotVerifiedError

        # Success — clear failed attempts and issue token pair
        await self._failed_attempt_storage.delete_for_email(email_lower)

        pair = await self._auth_service.issue_token_pair(
            user.id_,
            request.ip,
            request.user_agent,
        )

        audit(
            "auth.login.success",
            user_id=user.id_,
            ip=ip,
            user_agent=ua,
        )

        logger.info("Log in: done.")
        return pair

    async def _record_failure(self, email_lower: str, ip: str) -> None:
        now = datetime.now(tz=timezone.utc)
        record = FailedLoginAttempt(
            email_lower=email_lower,
            ip=ip,
            attempted_at=now,
        )
        self._failed_attempt_storage.add(record)
        await self._transaction_manager.commit()
