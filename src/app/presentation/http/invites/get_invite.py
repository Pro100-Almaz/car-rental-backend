from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, status
from fastapi_error_map import ErrorAwareRouter

from app.infrastructure.auth_ctx.exceptions import InvalidInviteError, InviteAlreadyUsedError
from app.infrastructure.auth_ctx.handlers.get_invite import GetInvite, GetInviteResponse
from app.infrastructure.exceptions import StorageError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE


def make_get_invite_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.get(
        "/{token}",
        error_map={
            StorageError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
            InvalidInviteError: status.HTTP_404_NOT_FOUND,
            InviteAlreadyUsedError: status.HTTP_409_CONFLICT,
        },
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def get_invite(
        token: str,
        handler: FromDishka[GetInvite],
    ) -> GetInviteResponse:
        return await handler.execute(token)

    return router
