from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, status
from fastapi_error_map import ErrorAwareRouter
from pydantic import BaseModel, ConfigDict

from app.infrastructure.auth_ctx.exceptions import VerificationCodeRateLimitError
from app.infrastructure.auth_ctx.handlers.forgot_password import ForgotPassword, ForgotPasswordRequest
from app.infrastructure.exceptions import EmailSendError, StorageError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE


class ForgotPasswordBody(BaseModel):
    model_config = ConfigDict(frozen=True)

    email: str


def make_forgot_password_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.post(
        "/forgot-password/",
        error_map={
            VerificationCodeRateLimitError: status.HTTP_429_TOO_MANY_REQUESTS,
            EmailSendError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
            StorageError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
        },
        default_on_error=log_info,
        status_code=status.HTTP_204_NO_CONTENT,
    )
    @inject
    async def forgot_password(
        body: ForgotPasswordBody,
        handler: FromDishka[ForgotPassword],
    ) -> None:
        await handler.execute(ForgotPasswordRequest(email=body.email))

    return router
