from typing import Annotated
from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Depends, status
from fastapi_error_map import ErrorAwareRouter
from pydantic import BaseModel, ConfigDict

from app.core.queries.list_rentals import ListRentals, ListRentalsRequest
from app.core.queries.ports.rental_reader import ListRentalsQm
from app.infrastructure.exceptions import ReaderError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE


class ListRentalsRequestSchema(BaseModel):
    model_config = ConfigDict(frozen=True)

    organization_id: UUID
    status: str | None = None
    vehicle_id: UUID | None = None
    client_id: UUID | None = None


def make_list_rentals_router() -> APIRouter:
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
    async def list_rentals(
        request_schema: Annotated[ListRentalsRequestSchema, Depends()],
        interactor: FromDishka[ListRentals],
    ) -> ListRentalsQm:
        request = ListRentalsRequest(
            organization_id=request_schema.organization_id,
            status=request_schema.status,
            vehicle_id=request_schema.vehicle_id,
            client_id=request_schema.client_id,
        )
        return await interactor.execute(request)

    return router
