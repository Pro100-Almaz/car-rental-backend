import asyncio
import logging
from collections.abc import AsyncIterator, Iterator
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from typing import cast

from dishka import Provider, Scope, from_context, provide
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from starlette.requests import Request

from app.core.common.ports.email_sender import EmailSender
from app.infrastructure.adapters.bcrypt_password_hasher import HasherSemaphore, HasherThreadPoolExecutor
from app.infrastructure.adapters.smtp_email_sender import SmtpEmailSender
from app.infrastructure.auth_ctx.cookie_manager import CookieManager, CookieName
from app.infrastructure.auth_ctx.handlers.change_password import ChangePassword
from app.infrastructure.auth_ctx.handlers.log_in import LogIn
from app.infrastructure.auth_ctx.handlers.log_out import LogOut
from app.infrastructure.auth_ctx.handlers.create_invite import CreateInvite
from app.infrastructure.auth_ctx.handlers.get_invite import GetInvite
from app.infrastructure.auth_ctx.handlers.resend_verification import ResendVerification
from app.infrastructure.auth_ctx.handlers.sign_up import SignUp
from app.infrastructure.auth_ctx.handlers.verify_email import VerifyEmail
from app.infrastructure.auth_ctx.jwt_processor import JwtProcessor
from app.infrastructure.auth_ctx.service import AuthService
from app.infrastructure.auth_ctx.sqla_transaction_manager import AuthSqlaTransactionManager
from app.infrastructure.auth_ctx.sqla_tx_storage import AuthSessionSqlaTxStorage
from app.infrastructure.auth_ctx.sqla_invite_tx_storage import InviteSqlaTxStorage
from app.infrastructure.auth_ctx.sqla_user_tx_storage import AuthSqlaUserTxStorage
from app.infrastructure.auth_ctx.sqla_verification_code_tx_storage import EmailVerificationCodeSqlaTxStorage
from app.infrastructure.auth_ctx.types_ import AuthAsyncSession
from app.infrastructure.auth_ctx.utc_timer import AuthSessionUtcTimer
from app.infrastructure.auth_ctx.verification_types import ResendCooldown, VerificationCodeTtl
from app.main.config.settings import (
    CookieSettings,
    JwtSettings,
    PasswordHasherSettings,
    PostgresSettings,
    SessionSettings,
    SmtpSettings,
    SqlaSettings,
    VerificationSettings,
)

logger = logging.getLogger(__name__)


class HasherThreadPoolProvider(Provider):
    scope = Scope.APP

    @provide
    def provide_hasher_threadpool_executor(
        self,
        settings: PasswordHasherSettings,
    ) -> Iterator[HasherThreadPoolExecutor]:
        executor = HasherThreadPoolExecutor(
            ThreadPoolExecutor(
                max_workers=settings.MAX_THREADS,
                thread_name_prefix="bcrypt",
            )
        )
        yield executor
        logger.debug("Disposing hasher threadpool executor...")
        executor.shutdown(wait=True, cancel_futures=True)
        logger.debug("Hasher threadpool executor is disposed.")

    @provide
    def provide_hasher_semaphore(self, settings: PasswordHasherSettings) -> HasherSemaphore:
        return HasherSemaphore(asyncio.Semaphore(settings.MAX_THREADS))


class PersistenceSqlaProvider(Provider):
    @provide(scope=Scope.APP)
    async def provide_async_engine(
        self,
        postgres: PostgresSettings,
        sqla: SqlaSettings,
    ) -> AsyncIterator[AsyncEngine]:
        async_engine = create_async_engine(
            url=postgres.dsn,
            echo=sqla.ECHO,
            echo_pool=sqla.ECHO_POOL,
            pool_size=sqla.POOL_SIZE,
            max_overflow=sqla.MAX_OVERFLOW,
            connect_args={"connect_timeout": 5},
            pool_pre_ping=True,
        )
        logger.debug("Async engine created with DSN: %s", postgres.dsn)
        yield async_engine
        logger.debug("Disposing async engine...")
        await async_engine.dispose()
        logger.debug("Engine is disposed.")

    @provide(scope=Scope.APP)
    def provide_async_session_factory(
        self,
        engine: AsyncEngine,
    ) -> async_sessionmaker[AsyncSession]:
        async_session_factory = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            autoflush=False,
            expire_on_commit=False,
        )
        logger.debug("Async session maker initialized.")
        return async_session_factory

    @provide(scope=Scope.REQUEST)
    async def provide_primary_async_session(
        self,
        async_session_factory: async_sessionmaker[AsyncSession],
    ) -> AsyncIterator[AsyncSession]:
        """Provides UoW (AsyncSession) for the primary context"""
        logger.debug("Starting primary async session...")
        async with async_session_factory() as session:
            logger.debug("Primary async session started.")
            yield session
            logger.debug("Closing primary async session...")
        logger.debug("Primary async session closed.")

    @provide(scope=Scope.REQUEST)
    async def provide_auth_async_session(
        self,
        async_session_factory: async_sessionmaker[AsyncSession],
    ) -> AsyncIterator[AuthAsyncSession]:
        """Provides UoW (AsyncSession) for the auth context."""
        logger.debug("Starting auth async session...")
        async with async_session_factory() as session:
            logger.debug("Auth async session started.")
            yield cast(AuthAsyncSession, session)
            logger.debug("Closing auth async session...")
        logger.debug("Auth async session closed.")


class EmailProvider(Provider):
    scope = Scope.APP

    @provide
    def provide_email_sender(self, settings: SmtpSettings) -> EmailSender:
        return SmtpEmailSender(
            host=settings.HOST,
            port=settings.PORT,
            username=settings.USERNAME,
            password=settings.PASSWORD,
            from_email=settings.FROM_EMAIL,
            use_tls=settings.USE_TLS,
        )


class AuthProvider(Provider):
    scope = Scope.REQUEST

    auth_service = provide(AuthService)

    @provide(scope=Scope.APP)
    def provide_utc_auth_session_timer(
        self,
        settings: SessionSettings,
    ) -> AuthSessionUtcTimer:
        return AuthSessionUtcTimer(
            ttl=settings.ttl,
            refresh_threshold_ratio=settings.REFRESH_THRESHOLD_RATIO,
        )

    auth_session_tx_storage = provide(AuthSessionSqlaTxStorage)
    auth_tx_manager = provide(AuthSqlaTransactionManager)

    @provide(scope=Scope.APP)
    def provide_jwt_processor(
        self,
        settings: JwtSettings,
    ) -> JwtProcessor:
        return JwtProcessor(
            secret=settings.SECRET,
            algorithm=settings.ALGORITHM,
        )

    @provide(scope=Scope.APP)
    def provide_cookie_name(self, settings: CookieSettings) -> CookieName:
        return CookieName(settings.NAME)

    cookie_manager = provide(CookieManager)

    auth_sqla_user_tx_storage = provide(AuthSqlaUserTxStorage)
    verification_code_tx_storage = provide(EmailVerificationCodeSqlaTxStorage)
    invite_tx_storage = provide(InviteSqlaTxStorage)

    @provide(scope=Scope.APP)
    def provide_verification_code_ttl(self, settings: VerificationSettings) -> VerificationCodeTtl:
        return VerificationCodeTtl(settings.code_ttl)

    @provide(scope=Scope.APP)
    def provide_resend_cooldown(self, settings: VerificationSettings) -> ResendCooldown:
        return ResendCooldown(timedelta(seconds=settings.RESEND_COOLDOWN_SEC))

    # Account handlers
    sign_up = provide(SignUp)
    log_in = provide(LogIn)
    change_password = provide(ChangePassword)
    log_out = provide(LogOut)
    verify_email = provide(VerifyEmail)
    resend_verification = provide(ResendVerification)
    create_invite = provide(CreateInvite)
    get_invite = provide(GetInvite)


class RequestProvider(Provider):
    request = from_context(provides=Request, scope=Scope.REQUEST)


def infrastructure_providers() -> tuple[Provider, ...]:
    return (
        HasherThreadPoolProvider(),
        PersistenceSqlaProvider(),
        EmailProvider(),
        AuthProvider(),
        RequestProvider(),
    )
