from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, status
from fastapi_error_map import ErrorAwareRouter

from app.core.commands.charge_fine_to_client import ChargeFineToClient, ChargeFineToClientRequest
from app.core.commands.exceptions import FineNotFoundError
from app.infrastructure.exceptions import StorageError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE


def make_charge_fine_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.patch(
        "/{fine_id}/charge",
        error_map={
            StorageError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
            FineNotFoundError: status.HTTP_404_NOT_FOUND,
        },
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def charge_fine_to_client(
        fine_id: str,
        request: ChargeFineToClientRequest,
        interactor: FromDishka[ChargeFineToClient],
    ) -> None:
        await interactor.execute(request)

    return router
