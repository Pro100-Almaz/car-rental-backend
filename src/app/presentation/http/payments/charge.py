from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, status
from fastapi_error_map import ErrorAwareRouter

from app.core.commands.charge_client import ChargeClient, ChargeClientRequest, ChargeClientResponse
from app.core.common.exceptions import BusinessTypeError
from app.infrastructure.exceptions import StorageError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE


def make_charge_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.post(
        "/charge",
        error_map={
            StorageError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
            BusinessTypeError: status.HTTP_400_BAD_REQUEST,
        },
        default_on_error=log_info,
        status_code=status.HTTP_201_CREATED,
    )
    @inject
    async def charge_client(
        request: ChargeClientRequest,
        interactor: FromDishka[ChargeClient],
    ) -> ChargeClientResponse:
        return await interactor.execute(request)

    return router
