from typing import Any
from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, status
from fastapi_error_map import ErrorAwareRouter
from pydantic import BaseModel, ConfigDict

from app.core.commands.exceptions import ClientNotFoundError
from app.core.commands.update_client import UpdateClient, UpdateClientRequest
from app.core.common.exceptions import BusinessTypeError
from app.infrastructure.exceptions import StorageError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE


class UpdateClientBody(BaseModel):
    model_config = ConfigDict(frozen=True)

    phone: str | None = None
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    id_document_url: str | None = None
    license_front_url: str | None = None
    license_back_url: str | None = None
    metadata: dict[str, Any] | None = None


def make_update_client_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.patch(
        "/{client_id}",
        error_map={
            StorageError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
            BusinessTypeError: status.HTTP_400_BAD_REQUEST,
            ClientNotFoundError: status.HTTP_404_NOT_FOUND,
        },
        default_on_error=log_info,
        status_code=status.HTTP_204_NO_CONTENT,
    )
    @inject
    async def update_client(
        client_id: UUID,
        body: UpdateClientBody,
        interactor: FromDishka[UpdateClient],
    ) -> None:
        fields_set = body.model_fields_set
        kwargs: dict[str, Any] = {"client_id": client_id}
        for field_name in UpdateClientBody.model_fields:
            if field_name in fields_set:
                kwargs[field_name] = getattr(body, field_name)
        request = UpdateClientRequest(**kwargs)
        await interactor.execute(request)

    return router
