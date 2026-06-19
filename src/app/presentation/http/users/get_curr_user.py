from inspect import getdoc

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter
from fastapi_error_map import ErrorAwareRouter
from starlette import status

from app.core.common.authorization.exceptions import AuthorizationError
from app.core.queries.list_users import ListUsers
from app.core.queries.models.user import UserQm
from app.core.queries.query_support.exceptions import PaginationError
from app.core.queries.query_support.get_current_user import GetCurrentUser
from app.infrastructure.auth_ctx.exceptions import AuthenticationError
from app.infrastructure.exceptions import ReaderError, StorageError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE


def make_current_user_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.get(
        "/current/",
        error_map={
            AuthenticationError: status.HTTP_401_UNAUTHORIZED,
            StorageError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
            AuthorizationError: status.HTTP_403_FORBIDDEN,
            PaginationError: status.HTTP_400_BAD_REQUEST,
            ReaderError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
        },
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
        description=getdoc(ListUsers),
    )
    @inject
    async def get_curr_user(interactor: FromDishka[GetCurrentUser]) -> UserQm:

        return await interactor.execute()

    return router
