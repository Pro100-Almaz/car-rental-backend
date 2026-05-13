from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, status
from fastapi_error_map import ErrorAwareRouter

from app.core.commands.exceptions import RentalServiceNotFoundError
from app.core.commands.remove_rental_service import RemoveRentalService, RemoveRentalServiceRequest
from app.infrastructure.exceptions import StorageError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE


def make_remove_rental_service_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.delete(
        "/{rental_service_id}",
        error_map={
            StorageError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
            RentalServiceNotFoundError: status.HTTP_404_NOT_FOUND,
        },
        default_on_error=log_info,
        status_code=status.HTTP_204_NO_CONTENT,
    )
    @inject
    async def remove_rental_service(
        rental_service_id: UUID,
        interactor: FromDishka[RemoveRentalService],
    ) -> None:
        request = RemoveRentalServiceRequest(rental_service_id=rental_service_id)
        await interactor.execute(request)

    return router
