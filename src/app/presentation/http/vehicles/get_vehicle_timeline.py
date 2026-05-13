from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, status
from fastapi_error_map import ErrorAwareRouter

from app.core.queries.get_vehicle_timeline import GetVehicleTimeline, GetVehicleTimelineRequest
from app.core.queries.models.vehicle_timeline import VehicleTimelineQm
from app.infrastructure.exceptions import ReaderError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE


def make_get_vehicle_timeline_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.get(
        "/{vehicle_id}/timeline",
        error_map={
            ReaderError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
        },
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def get_vehicle_timeline(
        vehicle_id: UUID,
        interactor: FromDishka[GetVehicleTimeline],
    ) -> VehicleTimelineQm:
        return await interactor.execute(
            GetVehicleTimelineRequest(vehicle_id=vehicle_id)
        )

    return router
