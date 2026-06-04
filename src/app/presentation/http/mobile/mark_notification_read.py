from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, status
from fastapi_error_map import ErrorAwareRouter

from app.core.commands.mark_notification_read import (
    MarkNotificationRead,
    MarkNotificationReadRequest,
    NotificationNotFoundError,
)
from app.infrastructure.auth_ctx.exceptions import AuthenticationError
from app.core.common.authorization.exceptions import AuthorizationError
from app.infrastructure.exceptions import StorageError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE


def make_mark_notification_read_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.post(
        "/notifications/{notification_id}/read",
        error_map={
            AuthenticationError: status.HTTP_401_UNAUTHORIZED,
            AuthorizationError: status.HTTP_403_FORBIDDEN,
            NotificationNotFoundError: status.HTTP_404_NOT_FOUND,
            StorageError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
        },
        default_on_error=log_info,
        status_code=status.HTTP_204_NO_CONTENT,
    )
    @inject
    async def mark_notification_read(
        notification_id: UUID,
        interactor: FromDishka[MarkNotificationRead],
    ) -> None:
        await interactor.execute(
            MarkNotificationReadRequest(notification_id=notification_id),
        )

    return router
