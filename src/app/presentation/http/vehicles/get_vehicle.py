from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, HTTPException, status
from fastapi_error_map import ErrorAwareRouter

from app.core.queries.get_vehicle import GetVehicle, GetVehicleRequest
from app.core.queries.models.vehicle import VehicleQm
from app.infrastructure.exceptions import ReaderError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE


def make_get_vehicle_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.get(
        "/{vehicle_id}",
        error_map={
            ReaderError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
        },
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
        responses={404: {"description": "Vehicle not found"}},
    )
    @inject
    async def get_vehicle(
        vehicle_id: UUID,
        interactor: FromDishka[GetVehicle],
    ) -> VehicleQm:
        result = await interactor.execute(GetVehicleRequest(vehicle_id=vehicle_id))
        if result is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found.")
        return result

    return router
