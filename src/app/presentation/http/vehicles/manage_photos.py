from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, status
from fastapi_error_map import ErrorAwareRouter
from pydantic import BaseModel, ConfigDict

from app.core.commands.exceptions import VehicleNotFoundError
from app.core.commands.manage_vehicle_photos import (
    AddVehiclePhoto,
    AddVehiclePhotoRequest,
    PhotoLimitExceededError,
    PhotoNotFoundError,
    RemoveVehiclePhoto,
    RemoveVehiclePhotoRequest,
)
from app.infrastructure.exceptions import StorageError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE


class AddPhotoBody(BaseModel):
    model_config = ConfigDict(frozen=True)

    url: str


def make_manage_photos_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.post(
        "/{vehicle_id}/photos",
        error_map={
            StorageError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
            VehicleNotFoundError: status.HTTP_404_NOT_FOUND,
            PhotoLimitExceededError: status.HTTP_400_BAD_REQUEST,
        },
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def add_vehicle_photo(
        vehicle_id: UUID,
        body: AddPhotoBody,
        interactor: FromDishka[AddVehiclePhoto],
    ) -> list[str]:
        return await interactor.execute(
            AddVehiclePhotoRequest(vehicle_id=vehicle_id, url=body.url)
        )

    @router.delete(
        "/{vehicle_id}/photos/{photo_index}",
        error_map={
            StorageError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
            VehicleNotFoundError: status.HTTP_404_NOT_FOUND,
            PhotoNotFoundError: status.HTTP_404_NOT_FOUND,
        },
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def remove_vehicle_photo(
        vehicle_id: UUID,
        photo_index: int,
        interactor: FromDishka[RemoveVehiclePhoto],
    ) -> list[str]:
        return await interactor.execute(
            RemoveVehiclePhotoRequest(vehicle_id=vehicle_id, photo_index=photo_index)
        )

    return router
