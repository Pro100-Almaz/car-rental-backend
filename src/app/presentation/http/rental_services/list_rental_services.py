from typing import Annotated
from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Query, status
from fastapi_error_map import ErrorAwareRouter

from app.core.queries.list_rental_services import ListRentalServices, ListRentalServicesRequest
from app.core.queries.ports.rental_service_reader import ListRentalServicesQm
from app.infrastructure.exceptions import ReaderError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE


def make_list_rental_services_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.get(
        "/",
        error_map={
            ReaderError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
        },
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def list_rental_services(
        rental_id: Annotated[UUID, Query(...)],
        interactor: FromDishka[ListRentalServices] = ...,  # type: ignore[assignment]
    ) -> ListRentalServicesQm:
        request = ListRentalServicesRequest(
            rental_id=rental_id,
        )
        return await interactor.execute(request)

    return router
