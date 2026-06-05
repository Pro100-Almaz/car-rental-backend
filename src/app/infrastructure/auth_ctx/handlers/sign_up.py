import logging
from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID, uuid4

from app.core.commands.exceptions import EmailAlreadyExistsError
from app.core.commands.ports.client_organization_tx_storage import ClientOrganizationTxStorage
from app.core.commands.ports.client_tx_storage import ClientTxStorage
from app.core.commands.ports.flusher import Flusher
from app.core.commands.ports.transaction_manager import TransactionManager
from app.core.commands.ports.utc_timer import UtcTimer
from app.core.common.authorization.current_user_service import CurrentUserService
from app.core.common.entities.client import Client
from app.core.common.entities.client_organization import ClientOrganization
from app.core.common.entities.types_ import (
    ClientId,
    OrganizationId,
    RegistrationSource,
    TrustLevel,
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
from app.infrastructure.auth_ctx.sqla_invite_tx_storage import InviteSqlaTxStorage
from app.infrastructure.auth_ctx.sqla_user_tx_storage import AuthSqlaUserTxStorage
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
    organization_id: UUID | None = None
    invite_token: str | None = None
    role: str | None = None


class SignUp:
    def __init__(
        self,
        current_user_service: CurrentUserService,
        utc_timer: UtcTimer,
        user_service: UserService,
        user_tx_storage: AuthSqlaUserTxStorage,
        client_tx_storage: ClientTxStorage,
        client_org_tx_storage: ClientOrganizationTxStorage,
        flusher: Flusher,
        transaction_manager: TransactionManager,
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
        self._email_sender = email_sender
        self._verification_code_tx_storage = verification_code_tx_storage
        self._code_ttl = code_ttl
        self._invite_tx_storage = invite_tx_storage
        self._default_organization_id = default_organization_id

    async def _resolve_invite(
        self,
        request: SignUpRequest,
        email: Email,
        now: UtcDatetime,
    ) -> tuple[OrganizationId, UserRole]:
        invite = await self._invite_tx_storage.get_by_token(request.invite_token)  # type: ignore[arg-type]
        if invite is None:
            raise InvalidInviteError
        if invite.expires_at.value < now.value:
            raise InvalidInviteError
        if invite.used_at is not None:
            raise InviteAlreadyUsedError
        if invite.email != email.value:
            raise InvalidInviteError
        return OrganizationId(invite.organization_id), invite.role

    def _create_client_and_subscription(
        self,
        *,
        client_id: ClientId,
        organization_id: OrganizationId,
        user_id: "UUID",
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
            id_document_url=None,
            license_front_url=None,
            license_back_url=None,
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
            raise AlreadyAuthenticatedError
        except AuthenticationError:
            pass

        email = Email(request.email)
        password = RawPassword(request.password)
        now = self._utc_timer.now

        if request.invite_token:
            organization_id, role = await self._resolve_invite(request, email, now)
        else:
            raw_org_id = request.organization_id or self._default_organization_id
            if raw_org_id is None:
                raise OrganizationIdRequiredError
            organization_id = OrganizationId(raw_org_id)
            role = UserRole.CLIENT if request.role == "client" else UserRole.INVESTOR

        client_id: ClientId | None = None
        if role == UserRole.CLIENT:
            client_id = create_client_id()

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
            client_id=client_id,
        )
        self._user_tx_storage.add(user)

        if role == UserRole.CLIENT and client_id is not None:
            self._create_client_and_subscription(
                client_id=client_id,
                organization_id=organization_id,
                user_id=user.id_,
                request=request,
                email=email,
                now=now,
            )

        try:
            await self._flusher.flush()
        except EmailAlreadyExistsError:
            raise

        if request.invite_token:
            invite = await self._invite_tx_storage.get_by_token(request.invite_token)
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
        await self._transaction_manager.commit()

        logger.debug("Verification code for %s: %s", email.value, code)

        await self._email_sender.send(
            to=email.value,
            subject="Email Verification Code",
            body=(
                f"Your verification code is: {code}\n\n"
                f"This code expires in {self._code_ttl.total_seconds() // 60:.0f} minutes."
            ),
        )

        logger.info("Sign up: done. Verification email sent.")
