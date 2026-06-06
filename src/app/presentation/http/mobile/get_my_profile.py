from typing import ClassVar

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, status
from fastapi_error_map import ErrorAwareRouter

from app.core.common.authorization.exceptions import AuthorizationError
from app.core.common.exceptions import BaseError
from app.core.queries.get_my_profile import GetMyProfile
from app.core.queries.models.client import ClientQm
from app.infrastructure.auth_ctx.exceptions import AuthenticationError
from app.infrastructure.exceptions import ReaderError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE


class ClientProfileNotFoundError(BaseError):
    default_message: ClassVar[str] = "Client profile not found."


def make_get_my_profile_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.get(
        "/clients/me",
        error_map={
            AuthenticationError: status.HTTP_401_UNAUTHORIZED,
            AuthorizationError: status.HTTP_403_FORBIDDEN,
            ClientProfileNotFoundError: status.HTTP_404_NOT_FOUND,
            ReaderError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
        },
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
        responses={404: {"description": "Client profile not found"}},
    )
    @inject
    async def get_my_profile(
        interactor: FromDishka[GetMyProfile],
    ) -> ClientQm:
        result = await interactor.execute()
        if result is None:
            raise ClientProfileNotFoundError
        return result

    return router
