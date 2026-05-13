from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, status
from fastapi_error_map import ErrorAwareRouter

from app.core.common.authorization.exceptions import AuthorizationError
from app.core.common.exceptions import BusinessTypeError
from app.infrastructure.auth_ctx.handlers.create_invite import CreateInvite, CreateInviteRequest, CreateInviteResponse
from app.infrastructure.exceptions import StorageError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE


def make_create_invite_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.post(
        "/",
        error_map={
            StorageError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
            AuthorizationError: status.HTTP_403_FORBIDDEN,
            BusinessTypeError: status.HTTP_400_BAD_REQUEST,
        },
        default_on_error=log_info,
        status_code=status.HTTP_201_CREATED,
    )
    @inject
    async def create_invite(
        request: CreateInviteRequest,
        handler: FromDishka[CreateInvite],
    ) -> CreateInviteResponse:
        return await handler.execute(request)

    return router
