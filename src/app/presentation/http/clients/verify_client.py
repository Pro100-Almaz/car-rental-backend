from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, status
from fastapi_error_map import ErrorAwareRouter
from pydantic import BaseModel, ConfigDict

from app.core.commands.exceptions import ClientNotFoundError
from app.core.commands.verify_client import VerifyClient, VerifyClientRequest
from app.core.common.entities.types_ import VerificationStatus
from app.infrastructure.exceptions import StorageError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE


class VerifyClientBody(BaseModel):
    model_config = ConfigDict(frozen=True)

    status: VerificationStatus


def make_verify_client_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.post(
        "/{client_id}/verify",
        error_map={
            StorageError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
            ClientNotFoundError: status.HTTP_404_NOT_FOUND,
        },
        default_on_error=log_info,
        status_code=status.HTTP_204_NO_CONTENT,
    )
    @inject
    async def verify_client(
        client_id: UUID,
        body: VerifyClientBody,
        interactor: FromDishka[VerifyClient],
    ) -> None:
        request = VerifyClientRequest(
            client_id=client_id,
            status=body.status,
        )
        await interactor.execute(request)

    return router
