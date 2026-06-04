from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, status
from fastapi_error_map import ErrorAwareRouter
from pydantic import BaseModel, ConfigDict

from app.infrastructure.adapters.exceptions import PasswordHasherBusyError
from app.infrastructure.auth_ctx.exceptions import InvalidVerificationCodeError
from app.infrastructure.auth_ctx.handlers.reset_password import ResetPassword, ResetPasswordRequest
from app.infrastructure.exceptions import StorageError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE


class ResetPasswordBody(BaseModel):
    model_config = ConfigDict(frozen=True)

    email: str
    code: str
    new_password: str


def make_reset_password_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.post(
        "/reset-password/",
        error_map={
            InvalidVerificationCodeError: status.HTTP_400_BAD_REQUEST,
            PasswordHasherBusyError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
            StorageError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
        },
        default_on_error=log_info,
        status_code=status.HTTP_204_NO_CONTENT,
    )
    @inject
    async def reset_password(
        body: ResetPasswordBody,
        handler: FromDishka[ResetPassword],
    ) -> None:
        await handler.execute(
            ResetPasswordRequest(
                email=body.email,
                code=body.code,
                new_password=body.new_password,
            )
        )

    return router
