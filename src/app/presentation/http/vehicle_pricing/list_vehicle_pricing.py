from typing import Annotated
from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Depends, status
from fastapi_error_map import ErrorAwareRouter
from pydantic import BaseModel, ConfigDict

from app.core.queries.list_vehicle_pricing import ListVehiclePricing, ListVehiclePricingRequest
from app.core.queries.ports.vehicle_pricing_reader import ListVehiclePricingQm
from app.infrastructure.exceptions import ReaderError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE


class ListVehiclePricingRequestSchema(BaseModel):
    model_config = ConfigDict(frozen=True)

    vehicle_id: UUID
    is_active: bool | None = None


def make_list_vehicle_pricing_router() -> APIRouter:
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
    async def list_vehicle_pricing(
        request_schema: Annotated[ListVehiclePricingRequestSchema, Depends()],
        interactor: FromDishka[ListVehiclePricing],
    ) -> ListVehiclePricingQm:
        request = ListVehiclePricingRequest(
            vehicle_id=request_schema.vehicle_id,
            is_active=request_schema.is_active,
        )
        return await interactor.execute(request)

    return router
