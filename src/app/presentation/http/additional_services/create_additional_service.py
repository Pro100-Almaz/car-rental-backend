from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, status
from fastapi_error_map import ErrorAwareRouter

from app.core.commands.create_additional_service import (
    CreateAdditionalService,
    CreateAdditionalServiceRequest,
    CreateAdditionalServiceResponse,
)
from app.core.common.exceptions import BusinessTypeError
from app.infrastructure.exceptions import StorageError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE


def make_create_additional_service_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.post(
        "/",
        error_map={
            StorageError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
            BusinessTypeError: status.HTTP_400_BAD_REQUEST,
        },
        default_on_error=log_info,
        status_code=status.HTTP_201_CREATED,
    )
    @inject
    async def create_additional_service(
        request: CreateAdditionalServiceRequest,
        interactor: FromDishka[CreateAdditionalService],
    ) -> CreateAdditionalServiceResponse:
        return await interactor.execute(request)

    return router
