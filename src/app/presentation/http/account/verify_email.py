from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, status
from fastapi_error_map import ErrorAwareRouter

from app.core.common.exceptions import BusinessTypeError
from app.infrastructure.auth_ctx.exceptions import (
    EmailAlreadyVerifiedError,
    InvalidVerificationCodeError,
)
from app.infrastructure.auth_ctx.handlers.verify_email import VerifyEmail, VerifyEmailRequest
from app.infrastructure.exceptions import StorageError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE


def make_verify_email_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.post(
        "/verify-email/",
        error_map={
            StorageError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
            BusinessTypeError: status.HTTP_400_BAD_REQUEST,
            InvalidVerificationCodeError: status.HTTP_400_BAD_REQUEST,
            EmailAlreadyVerifiedError: status.HTTP_409_CONFLICT,
        },
        default_on_error=log_info,
        status_code=status.HTTP_204_NO_CONTENT,
    )
    @inject
    async def verify_email(
        request: VerifyEmailRequest,
        handler: FromDishka[VerifyEmail],
    ) -> None:
        await handler.execute(request)

    return router
