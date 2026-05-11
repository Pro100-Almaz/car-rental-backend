from typing import Any
from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, status
from fastapi_error_map import ErrorAwareRouter
from pydantic import BaseModel, ConfigDict

from app.core.commands.exceptions import VehicleNotFoundError
from app.core.commands.update_vehicle import UpdateVehicle, UpdateVehicleRequest
from app.core.common.exceptions import BusinessTypeError
from app.infrastructure.exceptions import StorageError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE

_UNSET = object()


class UpdateVehicleBody(BaseModel):
    model_config = ConfigDict(frozen=True)

    nickname: str | None = None
    make: str | None = None
    model: str | None = None
    year: int | None = None
    vin: str | None = None
    license_plate: str | None = None
    color: str | None = None
    category: str | None = None
    fuel_type: str | None = None
    transmission: str | None = None
    current_mileage: int | None = None
    purchase_price: float | None = None
    purchase_date: str | None = None
    insurance_expiry: str | None = None
    inspection_expiry: str | None = None
    gps_device_id: str | None = None
    branch_id: UUID | None = None
    photos: list[str] | None = None
    features: dict[str, Any] | None = None
    pricing_override: dict[str, Any] | None = None


def make_update_vehicle_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.patch(
        "/{vehicle_id}",
        error_map={
            StorageError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
            BusinessTypeError: status.HTTP_400_BAD_REQUEST,
            VehicleNotFoundError: status.HTTP_404_NOT_FOUND,
        },
        default_on_error=log_info,
        status_code=status.HTTP_204_NO_CONTENT,
    )
    @inject
    async def update_vehicle(
        vehicle_id: UUID,
        body: UpdateVehicleBody,
        interactor: FromDishka[UpdateVehicle],
    ) -> None:
        fields_set = body.model_fields_set
        kwargs: dict[str, Any] = {"vehicle_id": vehicle_id}
        for field_name in UpdateVehicleBody.model_fields:
            if field_name in fields_set:
                kwargs[field_name] = getattr(body, field_name)
        request = UpdateVehicleRequest(**kwargs)
        await interactor.execute(request)

    return router
