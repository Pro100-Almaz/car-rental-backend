from typing import Annotated
from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Path, status
from fastapi_error_map import ErrorAwareRouter

from app.core.commands.exceptions import UserNotFoundError
from app.core.commands.set_user_role import SetUserRole, SetUserRoleRequest
from app.core.common.authorization.exceptions import AuthorizationError
from app.core.common.exceptions import BusinessTypeError
from app.infrastructure.auth_ctx.exceptions import AuthenticationError
from app.infrastructure.exceptions import StorageError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE


def make_set_user_role_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.put(
        "/{user_id}/role/",
        error_map={
            AuthenticationError: status.HTTP_401_UNAUTHORIZED,
            StorageError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
            AuthorizationError: status.HTTP_403_FORBIDDEN,
            BusinessTypeError: status.HTTP_400_BAD_REQUEST,
            UserNotFoundError: status.HTTP_404_NOT_FOUND,
        },
        default_on_error=log_info,
        status_code=status.HTTP_204_NO_CONTENT,
    )
    @inject
    async def set_user_role(
        user_id: Annotated[UUID, Path()],
        request: SetUserRoleRequest,
        interactor: FromDishka[SetUserRole],
    ) -> None:
        await interactor.execute(SetUserRoleRequest(user_id=user_id, role=request.role))

    return router
