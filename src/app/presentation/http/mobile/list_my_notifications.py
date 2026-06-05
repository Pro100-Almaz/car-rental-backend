from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, status
from fastapi_error_map import ErrorAwareRouter

from app.core.common.authorization.exceptions import AuthorizationError
from app.core.queries.list_my_notifications import ListMyNotifications, ListMyNotificationsRequest
from app.core.queries.ports.notification_reader import ListNotificationsQm
from app.infrastructure.auth_ctx.exceptions import AuthenticationError
from app.infrastructure.exceptions import ReaderError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE


def make_list_my_notifications_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.get(
        "/notifications/",
        error_map={
            AuthenticationError: status.HTTP_401_UNAUTHORIZED,
            AuthorizationError: status.HTTP_403_FORBIDDEN,
            ReaderError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
        },
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def list_my_notifications(
        interactor: FromDishka[ListMyNotifications],
        limit: int = 20,
        offset: int = 0,
    ) -> ListNotificationsQm:
        return await interactor.execute(
            ListMyNotificationsRequest(limit=limit, offset=offset),
        )

    return router
