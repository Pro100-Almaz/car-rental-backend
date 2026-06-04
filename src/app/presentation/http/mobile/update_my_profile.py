from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, status
from fastapi_error_map import ErrorAwareRouter

from app.core.commands.exceptions import ClientNotFoundError
from app.core.commands.update_client_profile import UpdateClientProfile, UpdateClientProfileRequest
from app.infrastructure.auth_ctx.exceptions import AuthenticationError
from app.core.common.authorization.exceptions import AuthorizationError
from app.infrastructure.exceptions import StorageError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE


def make_update_my_profile_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.patch(
        "/clients/me",
        error_map={
            AuthenticationError: status.HTTP_401_UNAUTHORIZED,
            AuthorizationError: status.HTTP_403_FORBIDDEN,
            ClientNotFoundError: status.HTTP_404_NOT_FOUND,
            StorageError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
        },
        default_on_error=log_info,
        status_code=status.HTTP_204_NO_CONTENT,
    )
    @inject
    async def update_my_profile(
        request: UpdateClientProfileRequest,
        interactor: FromDishka[UpdateClientProfile],
    ) -> None:
        await interactor.execute(request)

    return router
