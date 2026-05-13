import logging
from dataclasses import dataclass
from uuid import UUID, uuid4

from app.core.commands.exceptions import EmailAlreadyExistsError
from app.core.commands.ports.flusher import Flusher
from app.core.commands.ports.transaction_manager import TransactionManager
from app.core.commands.ports.utc_timer import UtcTimer
from app.core.common.authorization.current_user_service import CurrentUserService
from app.core.common.entities.types_ import OrganizationId, UserRole
from app.core.common.factories.id_factory import create_user_id
from app.core.common.ports.email_sender import EmailSender
from app.core.common.services.user import UserService
from app.core.common.value_objects.email import Email
from app.core.common.value_objects.raw_password import RawPassword
from app.core.common.value_objects.utc_datetime import UtcDatetime
from app.infrastructure.auth_ctx.code_generator import generate_verification_code
from app.infrastructure.auth_ctx.exceptions import (
    AlreadyAuthenticatedError,
    AuthenticationError,
    InvalidInviteError,
    InviteAlreadyUsedError,
)
from app.infrastructure.auth_ctx.sqla_invite_tx_storage import InviteSqlaTxStorage
from app.infrastructure.auth_ctx.sqla_user_tx_storage import AuthSqlaUserTxStorage
from app.infrastructure.auth_ctx.sqla_verification_code_tx_storage import EmailVerificationCodeSqlaTxStorage
from app.infrastructure.auth_ctx.verification_code import EmailVerificationCode
from app.infrastructure.auth_ctx.verification_types import VerificationCodeTtl

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class SignUpRequest:
    email: str
    password: str
    first_name: str
    last_name: str
    phone: str | None = None
    organization_id: UUID | None = None
    invite_token: str | None = None


class SignUp:
    def __init__(
        self,
        current_user_service: CurrentUserService,
        utc_timer: UtcTimer,
        user_service: UserService,
        user_tx_storage: AuthSqlaUserTxStorage,
        flusher: Flusher,
        transaction_manager: TransactionManager,
        email_sender: EmailSender,
        verification_code_tx_storage: EmailVerificationCodeSqlaTxStorage,
        code_ttl: VerificationCodeTtl,
        invite_tx_storage: InviteSqlaTxStorage,
    ) -> None:
        self._current_user_service = current_user_service
        self._utc_timer = utc_timer
        self._user_service = user_service
        self._user_tx_storage = user_tx_storage
        self._flusher = flusher
        self._transaction_manager = transaction_manager
        self._email_sender = email_sender
        self._verification_code_tx_storage = verification_code_tx_storage
        self._code_ttl = code_ttl
        self._invite_tx_storage = invite_tx_storage

    async def execute(self, request: SignUpRequest) -> None:
        logger.info("Sign up: started.")

        try:
            await self._current_user_service.get_current_user()
            raise AlreadyAuthenticatedError
        except AuthenticationError:
            pass

        email = Email(request.email)
        password = RawPassword(request.password)
        now = self._utc_timer.now

        if request.invite_token:
            invite = await self._invite_tx_storage.get_by_token(request.invite_token)
            if invite is None:
                raise InvalidInviteError
            if invite.expires_at.value < now.value:
                raise InvalidInviteError
            if invite.used_at is not None:
                raise InviteAlreadyUsedError
            if invite.email != email.value:
                raise InvalidInviteError

            organization_id = OrganizationId(invite.organization_id)
            role = invite.role
        else:
            if request.organization_id is None:
                raise InvalidInviteError("Organization ID is required for client signup.")
            organization_id = OrganizationId(request.organization_id)
            role = UserRole.CLIENT

        user = await self._user_service.create_user_with_raw_password(
            user_id=create_user_id(),
            organization_id=organization_id,
            email=email,
            raw_password=password,
            first_name=request.first_name,
            last_name=request.last_name,
            now=now,
            phone=request.phone,
            role=role,
            email_verified=False,
        )
        self._user_tx_storage.add(user)
        try:
            await self._flusher.flush()
        except EmailAlreadyExistsError:
            raise

        if request.invite_token:
            invite.used_at = now

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

        logger.info("Sign up: done. Verification email sent.")
