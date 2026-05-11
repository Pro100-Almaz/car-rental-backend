import logging
from dataclasses import dataclass
from uuid import UUID

from app.core.commands.exceptions import EmailAlreadyExistsError
from app.core.commands.ports.flusher import Flusher
from app.core.commands.ports.transaction_manager import TransactionManager
from app.core.commands.ports.utc_timer import UtcTimer
from app.core.common.authorization.current_user_service import CurrentUserService
from app.core.common.entities.types_ import OrganizationId
from app.core.common.factories.id_factory import create_user_id
from app.core.common.services.user import UserService
from app.core.common.value_objects.email import Email
from app.core.common.value_objects.raw_password import RawPassword
from app.infrastructure.auth_ctx.exceptions import (
    AlreadyAuthenticatedError,
    AuthenticationError,
)
from app.infrastructure.auth_ctx.sqla_user_tx_storage import AuthSqlaUserTxStorage

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class SignUpRequest:
    organization_id: UUID
    email: str
    password: str
    first_name: str
    last_name: str
    phone: str | None = None


class SignUp:
    def __init__(
        self,
        current_user_service: CurrentUserService,
        utc_timer: UtcTimer,
        user_service: UserService,
        user_tx_storage: AuthSqlaUserTxStorage,
        flusher: Flusher,
        transaction_manager: TransactionManager,
    ) -> None:
        self._current_user_service = current_user_service
        self._utc_timer = utc_timer
        self._user_service = user_service
        self._user_tx_storage = user_tx_storage
        self._flusher = flusher
        self._transaction_manager = transaction_manager

    async def execute(self, request: SignUpRequest) -> None:
        logger.info("Sign up: started.")

        try:
            await self._current_user_service.get_current_user()
            raise AlreadyAuthenticatedError
        except AuthenticationError:
            pass

        email = Email(request.email)
        password = RawPassword(request.password)
        organization_id = OrganizationId(request.organization_id)
        now = self._utc_timer.now
        user = await self._user_service.create_user_with_raw_password(
            user_id=create_user_id(),
            organization_id=organization_id,
            email=email,
            raw_password=password,
            first_name=request.first_name,
            last_name=request.last_name,
            now=now,
            phone=request.phone,
        )
        self._user_tx_storage.add(user)
        try:
            await self._flusher.flush()
        except EmailAlreadyExistsError:
            raise

        await self._transaction_manager.commit()

        logger.info("Sign up: done.")
