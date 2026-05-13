from decimal import Decimal
from typing import Any
from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, status
from fastapi_error_map import ErrorAwareRouter
from pydantic import BaseModel, ConfigDict

from app.core.commands.exceptions import AdditionalServiceNotFoundError
from app.core.commands.update_additional_service import (
    UpdateAdditionalService,
    UpdateAdditionalServiceRequest,
)
from app.infrastructure.exceptions import StorageError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE


class UpdateAdditionalServiceBody(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str | None = None
    price: Decimal | None = None
    is_active: bool | None = None


def make_update_additional_service_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.patch(
        "/{additional_service_id}",
        error_map={
            StorageError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
            AdditionalServiceNotFoundError: status.HTTP_404_NOT_FOUND,
        },
        default_on_error=log_info,
        status_code=status.HTTP_204_NO_CONTENT,
    )
    @inject
    async def update_additional_service(
        additional_service_id: UUID,
        body: UpdateAdditionalServiceBody,
        interactor: FromDishka[UpdateAdditionalService],
    ) -> None:
        fields_set = body.model_fields_set
        kwargs: dict[str, Any] = {"additional_service_id": additional_service_id}
        for field_name in UpdateAdditionalServiceBody.model_fields:
            if field_name in fields_set:
                kwargs[field_name] = getattr(body, field_name)
        request = UpdateAdditionalServiceRequest(**kwargs)
        await interactor.execute(request)

    return router
