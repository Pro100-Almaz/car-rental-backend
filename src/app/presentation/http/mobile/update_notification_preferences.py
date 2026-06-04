from typing import Any

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, status
from fastapi_error_map import ErrorAwareRouter
from pydantic import BaseModel

from app.core.commands.exceptions import UserNotFoundError
from app.core.commands.update_notification_preferences import (
    UpdateNotificationPreferences,
    UpdateNotificationPreferencesRequest,
)
from app.core.common.authorization.exceptions import AuthorizationError
from app.infrastructure.auth_ctx.exceptions import AuthenticationError
from app.infrastructure.exceptions import StorageError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE


class UpdateNotificationPreferencesBody(BaseModel):
    preferences: dict[str, Any]


def make_update_notification_preferences_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.patch(
        "/clients/me/notification-preferences",
        error_map={
            AuthenticationError: status.HTTP_401_UNAUTHORIZED,
            AuthorizationError: status.HTTP_403_FORBIDDEN,
            UserNotFoundError: status.HTTP_404_NOT_FOUND,
            StorageError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
        },
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def update_notification_preferences(
        body: UpdateNotificationPreferencesBody,
        interactor: FromDishka[UpdateNotificationPreferences],
    ) -> dict[str, Any]:
        return await interactor.execute(
            UpdateNotificationPreferencesRequest(
                preferences=body.preferences,
            )
        )

    return router
