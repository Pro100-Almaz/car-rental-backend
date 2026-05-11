from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, status
from fastapi_error_map import ErrorAwareRouter
from pydantic import BaseModel, ConfigDict

from app.core.commands.blacklist_client import BlacklistClient, BlacklistClientRequest
from app.core.commands.exceptions import ClientNotFoundError
from app.infrastructure.exceptions import StorageError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE


class BlacklistClientBody(BaseModel):
    model_config = ConfigDict(frozen=True)

    reason: str


def make_blacklist_client_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.post(
        "/{client_id}/blacklist",
        error_map={
            StorageError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
            ClientNotFoundError: status.HTTP_404_NOT_FOUND,
        },
        default_on_error=log_info,
        status_code=status.HTTP_204_NO_CONTENT,
    )
    @inject
    async def blacklist_client(
        client_id: UUID,
        body: BlacklistClientBody,
        interactor: FromDishka[BlacklistClient],
    ) -> None:
        request = BlacklistClientRequest(
            client_id=client_id,
            reason=body.reason,
        )
        await interactor.execute(request)

    return router
