from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, status
from fastapi_error_map import ErrorAwareRouter

from app.core.commands.register_device_token import (
    RegisterDeviceToken,
    RegisterDeviceTokenRequest,
    RegisterDeviceTokenResponse,
)
from app.core.common.authorization.exceptions import AuthorizationError
from app.infrastructure.auth_ctx.exceptions import AuthenticationError
from app.infrastructure.exceptions import StorageError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE


def make_register_device_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.post(
        "/devices/register",
        error_map={
            AuthenticationError: status.HTTP_401_UNAUTHORIZED,
            AuthorizationError: status.HTTP_403_FORBIDDEN,
            StorageError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
        },
        default_on_error=log_info,
        status_code=status.HTTP_201_CREATED,
    )
    @inject
    async def register_device(
        request: RegisterDeviceTokenRequest,
        interactor: FromDishka[RegisterDeviceToken],
    ) -> RegisterDeviceTokenResponse:
        return await interactor.execute(request)

    return router
