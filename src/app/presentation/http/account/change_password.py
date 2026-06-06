from inspect import getdoc

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Request, status
from fastapi_error_map import ErrorAwareRouter
from pydantic import BaseModel, ConfigDict
from slowapi.errors import RateLimitExceeded

from app.core.common.authorization.exceptions import AuthorizationError
from app.core.common.exceptions import BusinessTypeError
from app.infrastructure.adapters.exceptions import PasswordHasherBusyError
from app.infrastructure.auth_ctx.exceptions import AuthenticationChangeError, AuthenticationError, ReAuthenticationError
from app.infrastructure.auth_ctx.handlers.change_password import ChangePassword, ChangePasswordRequest
from app.infrastructure.exceptions import StorageError
from app.infrastructure.rate_limit import get_user_id_or_ip, limiter
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_429_RATE_LIMITED_RULE, HTTP_503_SERVICE_UNAVAILABLE_RULE


class ChangePasswordRequestSchema(BaseModel):
    """
    Using Pydantic model here is generally unnecessary.
    It's only implemented to render specific Swagger UI.
    """

    model_config = ConfigDict(frozen=True)

    current_password: str
    new_password: str


def make_change_password_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.put(
        "/password/",
        error_map={
            AuthenticationError: status.HTTP_401_UNAUTHORIZED,
            StorageError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
            AuthorizationError: status.HTTP_403_FORBIDDEN,
            BusinessTypeError: status.HTTP_400_BAD_REQUEST,
            AuthenticationChangeError: status.HTTP_400_BAD_REQUEST,
            ReAuthenticationError: status.HTTP_403_FORBIDDEN,
            PasswordHasherBusyError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
            RateLimitExceeded: HTTP_429_RATE_LIMITED_RULE,
        },
        default_on_error=log_info,
        status_code=status.HTTP_204_NO_CONTENT,
        description=getdoc(ChangePassword),
    )
    @limiter.limit("10/hour", key_func=get_user_id_or_ip)
    @inject
    async def change_password(
        request_schema: ChangePasswordRequestSchema,
        request: Request,
        handler: FromDishka[ChangePassword],
    ) -> None:
        cmd = ChangePasswordRequest(
            current_password=request_schema.current_password,
            new_password=request_schema.new_password,
        )
        await handler.execute(cmd)

    return router
