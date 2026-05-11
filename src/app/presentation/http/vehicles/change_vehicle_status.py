from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, status
from fastapi_error_map import ErrorAwareRouter
from pydantic import BaseModel, ConfigDict

from app.core.commands.change_vehicle_status import ChangeVehicleStatus, ChangeVehicleStatusRequest
from app.core.commands.exceptions import InvalidVehicleStatusTransitionError, VehicleNotFoundError
from app.core.common.entities.types_ import VehicleStatus
from app.infrastructure.exceptions import StorageError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE


class ChangeVehicleStatusBody(BaseModel):
    model_config = ConfigDict(frozen=True)

    status: VehicleStatus


def make_change_vehicle_status_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.patch(
        "/{vehicle_id}/status",
        error_map={
            StorageError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
            VehicleNotFoundError: status.HTTP_404_NOT_FOUND,
            InvalidVehicleStatusTransitionError: status.HTTP_409_CONFLICT,
        },
        default_on_error=log_info,
        status_code=status.HTTP_204_NO_CONTENT,
    )
    @inject
    async def change_vehicle_status(
        vehicle_id: UUID,
        body: ChangeVehicleStatusBody,
        interactor: FromDishka[ChangeVehicleStatus],
    ) -> None:
        request = ChangeVehicleStatusRequest(
            vehicle_id=vehicle_id,
            status=body.status,
        )
        await interactor.execute(request)

    return router
