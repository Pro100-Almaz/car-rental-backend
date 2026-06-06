from inspect import getdoc

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Request, status
from fastapi_error_map import ErrorAwareRouter
from slowapi.errors import RateLimitExceeded

from app.core.commands.exceptions import EmailAlreadyExistsError
from app.core.common.authorization.exceptions import AuthorizationError
from app.core.common.exceptions import BusinessTypeError
from app.infrastructure.adapters.exceptions import PasswordHasherBusyError
from app.infrastructure.auth_ctx.exceptions import (
    AlreadyAuthenticatedError,
    AuthenticationError,
    InvalidInviteError,
    InviteAlreadyUsedError,
    OrganizationIdRequiredError,
)
from app.infrastructure.auth_ctx.handlers.sign_up import SignUp, SignUpRequest
from app.infrastructure.exceptions import EmailSendError, StorageError
from app.main.rate_limit import limiter
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_429_RATE_LIMITED_RULE, HTTP_503_SERVICE_UNAVAILABLE_RULE


def make_sign_up_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.post(
        "/signup/",
        error_map={
            AuthenticationError: status.HTTP_401_UNAUTHORIZED,
            StorageError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
            AuthorizationError: status.HTTP_403_FORBIDDEN,
            AlreadyAuthenticatedError: status.HTTP_403_FORBIDDEN,
            BusinessTypeError: status.HTTP_400_BAD_REQUEST,
            PasswordHasherBusyError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
            EmailAlreadyExistsError: status.HTTP_409_CONFLICT,
            InvalidInviteError: status.HTTP_400_BAD_REQUEST,
            InviteAlreadyUsedError: status.HTTP_409_CONFLICT,
            OrganizationIdRequiredError: status.HTTP_400_BAD_REQUEST,
            EmailSendError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
            RateLimitExceeded: HTTP_429_RATE_LIMITED_RULE,
        },
        default_on_error=log_info,
        status_code=status.HTTP_204_NO_CONTENT,
        description=getdoc(SignUp),
    )
    @limiter.limit("3/hour;10/day")
    @inject
    async def sign_up(
        body: SignUpRequest,
        request: Request,
        handler: FromDishka[SignUp],
    ) -> None:
        await handler.execute(body)

    return router
