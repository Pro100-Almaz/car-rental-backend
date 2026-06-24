import logging
from dataclasses import dataclass
from decimal import Decimal
from uuid import uuid4

from app.core.commands.exceptions import ClientPhoneAlreadyExistsError
from app.core.commands.ports.client_organization_tx_storage import ClientOrganizationTxStorage
from app.core.commands.ports.client_tx_storage import ClientTxStorage
from app.core.commands.ports.flusher import Flusher
from app.core.commands.ports.transaction_manager import TransactionManager
from app.core.commands.ports.user_tx_storage import UserTxStorage
from app.core.commands.ports.utc_timer import UtcTimer
from app.core.common.authorization.current_user_service import CurrentUserService
from app.core.common.authorization.exceptions import AuthorizationError
from app.core.common.entities.client import Client
from app.core.common.entities.client_organization import ClientOrganization
from app.core.common.entities.types_ import (
    ClientId,
    OrganizationId,
    RegistrationSource,
    TrustLevel,
    UserId,
    UserRole,
    VerificationStatus,
)
from app.core.common.factories.id_factory import create_client_id, create_client_organization_id, create_user_id
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
    OrganizationIdRequiredError,
)
from app.infrastructure.auth_ctx.invite import Invite
from app.infrastructure.auth_ctx.sqla_invite_tx_storage import InviteSqlaTxStorage
from app.infrastructure.auth_ctx.sqla_transaction_manager import AuthSqlaTransactionManager
from app.infrastructure.auth_ctx.sqla_verification_code_tx_storage import EmailVerificationCodeSqlaTxStorage
from app.infrastructure.auth_ctx.verification_code import EmailVerificationCode
from app.infrastructure.auth_ctx.verification_types import DefaultOrganizationId, VerificationCodeTtl

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class SignUpRequest:
    email: str
    password: str
    first_name: str
    last_name: str
    phone: str | None = None
    invite_token: str | None = None


class SignUp:
    def __init__(
        self,
        current_user_service: CurrentUserService,
        utc_timer: UtcTimer,
        user_service: UserService,
        user_tx_storage: UserTxStorage,
        client_tx_storage: ClientTxStorage,
        client_org_tx_storage: ClientOrganizationTxStorage,
        flusher: Flusher,
        transaction_manager: TransactionManager,
        auth_transaction_manager: AuthSqlaTransactionManager,
        email_sender: EmailSender,
        verification_code_tx_storage: EmailVerificationCodeSqlaTxStorage,
        code_ttl: VerificationCodeTtl,
        invite_tx_storage: InviteSqlaTxStorage,
        default_organization_id: DefaultOrganizationId,
    ) -> None:
        self._current_user_service = current_user_service
        self._utc_timer = utc_timer
        self._user_service = user_service
        self._user_tx_storage = user_tx_storage
        self._client_tx_storage = client_tx_storage
        self._client_org_tx_storage = client_org_tx_storage
        self._flusher = flusher
        self._transaction_manager = transaction_manager
        self._auth_transaction_manager = auth_transaction_manager
        self._email_sender = email_sender
        self._verification_code_tx_storage = verification_code_tx_storage
        self._code_ttl = code_ttl
        self._invite_tx_storage = invite_tx_storage
        self._default_organization_id = default_organization_id

    async def _resolve_invite(
        self,
        invite_token: str,
        email: Email,
        now: UtcDatetime,
    ) -> tuple[OrganizationId, UserRole, Invite]:
        invite = await self._invite_tx_storage.get_by_token(invite_token)
        if invite is None:
            raise InvalidInviteError
        if invite.expires_at.value < now.value:
            raise InvalidInviteError
        if invite.used_at is not None:
            raise InviteAlreadyUsedError
        if invite.email != email.value:
            raise InvalidInviteError
        return OrganizationId(invite.organization_id), invite.role, invite

    def _create_client_and_subscription(
        self,
        *,
        client_id: ClientId,
        organization_id: OrganizationId,
        user_id: UserId,
        request: SignUpRequest,
        email: Email,
        now: UtcDatetime,
    ) -> None:
        client = Client(
            id_=client_id,
            organization_id=organization_id,
            user_id=user_id,
            phone=request.phone or "",
            email=email.value,
            first_name=request.first_name,
            last_name=request.last_name,
            verification_status=VerificationStatus.PENDING,
            trust_score=0,
            trust_level=TrustLevel.NEW,
            is_blacklisted=False,
            blacklist_reason=None,
            wallet_balance=Decimal(0),
            debt_balance=Decimal(0),
            registration_source=RegistrationSource.MOBILE,
            rejection_reason=None,
            metadata=None,
            created_at=now,
            updated_at=now,
        )
        self._client_tx_storage.add(client)
        client_org = ClientOrganization(
            id_=create_client_organization_id(),
            client_id=client_id,
            organization_id=organization_id,
            joined_at=now,
        )
        self._client_org_tx_storage.add(client_org)

    async def execute(self, request: SignUpRequest) -> None:
        logger.info("Sign up: started.")

        try:
            await self._current_user_service.get_current_user()
        except (AuthenticationError, AuthorizationError):
            # No valid session (or a stale one that was just cleared). Signup is allowed.
            pass
        else:
            raise AlreadyAuthenticatedError

        email = Email(request.email)
        password = RawPassword(request.password)
        now = self._utc_timer.now

        invite: Invite | None = None
        if request.invite_token:
            organization_id, role, invite = await self._resolve_invite(request.invite_token, email, now)
        else:
            raw_org_id = self._default_organization_id
            if raw_org_id is None:
                raise OrganizationIdRequiredError
            organization_id = OrganizationId(raw_org_id)
            role = UserRole.CLIENT

        client_id: ClientId | None = None
        if role == UserRole.CLIENT:
            client_id = create_client_id()
            # Pre-check: the partial unique index `idx_clients_phone` only fires when
            # phone is non-empty. Reject early so we return 409 instead of letting the
            # downstream flush surface the same constraint as a race-safety net.
            if request.phone:
                existing = await self._client_tx_storage.get_by_org_and_phone(
                    organization_id,
                    request.phone,
                )
                if existing is not None:
                    raise ClientPhoneAlreadyExistsError

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
        await self._flusher.flush()

        if role == UserRole.CLIENT and client_id is not None:
            self._create_client_and_subscription(
                client_id=client_id,
                organization_id=organization_id,
                user_id=user.id_,
                request=request,
                email=email,
                now=now,
            )
            await self._flusher.flush()

        if invite is not None:
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

        # Email send happens BEFORE any commit. If SMTP fails, neither session commits and
        # PG rolls back — the user can retry without a stale "email already exists" block.
        await self._email_sender.send(
            to=email.value,
            subject="Email Verification Code",
            body=(
                f"Your verification code is: {code}\n\n"
                f"This code expires in {self._code_ttl.total_seconds() // 60:.0f} minutes."
            ),
        )

        # Commit primary first (user + client become visible), then auth (verification_code +
        # invite update). Order matters: auth-side FKs on email_verification_codes.user_id need
        # to see the committed user row.
        await self._transaction_manager.commit()
        await self._auth_transaction_manager.commit()

        logger.info("Sign up: done. Verification email sent.")
