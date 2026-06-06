from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Request, status
from fastapi_error_map import ErrorAwareRouter
from slowapi.errors import RateLimitExceeded

from app.core.common.exceptions import BusinessTypeError
from app.infrastructure.auth_ctx.exceptions import (
    AuthenticationError,
    EmailAlreadyVerifiedError,
    InvalidVerificationCodeError,
    VerificationCodeRateLimitError,
)
from app.infrastructure.auth_ctx.handlers.resend_verification import ResendVerification, ResendVerificationRequest
from app.infrastructure.exceptions import EmailSendError, StorageError
from app.main.rate_limit import limiter
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_429_RATE_LIMITED_RULE, HTTP_503_SERVICE_UNAVAILABLE_RULE


def make_resend_verification_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.post(
        "/resend-verification/",
        error_map={
            AuthenticationError: status.HTTP_401_UNAUTHORIZED,
            StorageError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
            BusinessTypeError: status.HTTP_400_BAD_REQUEST,
            InvalidVerificationCodeError: status.HTTP_400_BAD_REQUEST,
            EmailAlreadyVerifiedError: status.HTTP_409_CONFLICT,
            VerificationCodeRateLimitError: status.HTTP_429_TOO_MANY_REQUESTS,
            EmailSendError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
            RateLimitExceeded: HTTP_429_RATE_LIMITED_RULE,
        },
        default_on_error=log_info,
        status_code=status.HTTP_204_NO_CONTENT,
    )
    @limiter.limit("5/hour")
    @inject
    async def resend_verification(
        body: ResendVerificationRequest,
        request: Request,
        handler: FromDishka[ResendVerification],
    ) -> None:
        await handler.execute(body)

    return router
