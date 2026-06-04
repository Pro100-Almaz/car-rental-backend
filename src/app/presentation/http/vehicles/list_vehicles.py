from typing import Annotated
from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Depends, status
from fastapi_error_map import ErrorAwareRouter
from pydantic import BaseModel, ConfigDict

from app.core.queries.list_vehicles import ListVehicles, ListVehiclesRequest
from app.core.queries.ports.vehicle_reader import ListVehiclesQm
from app.infrastructure.exceptions import ReaderError
from app.infrastructure.auth_ctx.exceptions import AuthenticationError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE


class ListVehiclesRequestSchema(BaseModel):
    model_config = ConfigDict(frozen=True)

    organization_id: UUID
    status: str | None = None
    branch_id: UUID | None = None
    category: str | None = None
    investor_id: UUID | None = None
    search: str | None = None
    fuel_type: str | None = None
    mileage_from: int | None = None
    mileage_to: int | None = None


def make_list_vehicles_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.get(
        "/",
        error_map={
            AuthenticationError: status.HTTP_401_UNAUTHORIZED,
            ReaderError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
        },
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def list_vehicles(
        request_schema: Annotated[ListVehiclesRequestSchema, Depends()],
        interactor: FromDishka[ListVehicles],
    ) -> ListVehiclesQm:
        request = ListVehiclesRequest(
            organization_id=request_schema.organization_id,
            status=request_schema.status,
            branch_id=request_schema.branch_id,
            category=request_schema.category,
            investor_id=request_schema.investor_id,
            search=request_schema.search,
            fuel_type=request_schema.fuel_type,
            mileage_from=request_schema.mileage_from,
            mileage_to=request_schema.mileage_to,
        )
        return await interactor.execute(request)

    return router
