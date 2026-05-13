import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, status
from fastapi_error_map import ErrorAwareRouter
from pydantic import BaseModel, ConfigDict

from app.core.commands.exceptions import VehiclePricingNotFoundError
from app.core.commands.update_vehicle_pricing import UpdateVehiclePricing, UpdateVehiclePricingRequest
from app.core.common.exceptions import BusinessTypeError
from app.infrastructure.exceptions import StorageError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE


class UpdateVehiclePricingBody(BaseModel):
    model_config = ConfigDict(frozen=True)

    base_daily_rate: Decimal | None = None
    name: str | None = None
    multiplier: Decimal | None = None
    valid_from: datetime.date | None = None
    valid_to: datetime.date | None = None
    is_active: bool | None = None


def make_update_vehicle_pricing_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.patch(
        "/{vehicle_pricing_id}",
        error_map={
            StorageError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
            BusinessTypeError: status.HTTP_400_BAD_REQUEST,
            VehiclePricingNotFoundError: status.HTTP_404_NOT_FOUND,
        },
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def update_vehicle_pricing(
        vehicle_pricing_id: UUID,
        body: UpdateVehiclePricingBody,
        interactor: FromDishka[UpdateVehiclePricing],
    ) -> None:
        kwargs: dict[str, Any] = {"vehicle_pricing_id": vehicle_pricing_id}
        for field_name in body.model_fields_set:
            kwargs[field_name] = getattr(body, field_name)
        request = UpdateVehiclePricingRequest(**kwargs)
        await interactor.execute(request)

    return router
