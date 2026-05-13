from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, status
from fastapi_error_map import ErrorAwareRouter

from app.core.common.exceptions import BusinessTypeError
from app.infrastructure.auth_ctx.exceptions import (
    EmailAlreadyVerifiedError,
    InvalidVerificationCodeError,
    VerificationCodeRateLimitError,
)
from app.infrastructure.auth_ctx.handlers.resend_verification import ResendVerification, ResendVerificationRequest
from app.infrastructure.exceptions import StorageError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE


def make_resend_verification_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.post(
        "/resend-verification/",
        error_map={
            StorageError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
            BusinessTypeError: status.HTTP_400_BAD_REQUEST,
            InvalidVerificationCodeError: status.HTTP_400_BAD_REQUEST,
            EmailAlreadyVerifiedError: status.HTTP_409_CONFLICT,
            VerificationCodeRateLimitError: status.HTTP_429_TOO_MANY_REQUESTS,
        },
        default_on_error=log_info,
        status_code=status.HTTP_204_NO_CONTENT,
    )
    @inject
    async def resend_verification(
        request: ResendVerificationRequest,
        handler: FromDishka[ResendVerification],
    ) -> None:
        await handler.execute(request)

    return router
