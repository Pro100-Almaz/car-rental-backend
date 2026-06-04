from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, status
from fastapi_error_map import ErrorAwareRouter
from pydantic import BaseModel

from app.core.commands.exceptions import ClientNotFoundError
from app.core.commands.send_debt_reminder import SendDebtReminder, SendDebtReminderRequest
from app.core.common.authorization.exceptions import AuthorizationError
from app.infrastructure.auth_ctx.exceptions import AuthenticationError
from app.infrastructure.exceptions import StorageError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE


class SendDebtReminderBody(BaseModel):
    message: str | None = None


def make_send_debt_reminder_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.post(
        "/{client_id}/send-reminder",
        error_map={
            AuthenticationError: status.HTTP_401_UNAUTHORIZED,
            AuthorizationError: status.HTTP_403_FORBIDDEN,
            ClientNotFoundError: status.HTTP_404_NOT_FOUND,
            StorageError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
        },
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def send_debt_reminder(
        client_id: UUID,
        body: SendDebtReminderBody,
        interactor: FromDishka[SendDebtReminder],
    ) -> None:
        return await interactor.execute(
            SendDebtReminderRequest(
                client_id=client_id,
                message=body.message,
            )
        )

    return router
