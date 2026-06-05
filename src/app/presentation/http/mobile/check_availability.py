from datetime import datetime
from typing import Annotated
from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Query, status
from fastapi_error_map import ErrorAwareRouter

from app.core.common.authorization.exceptions import AuthorizationError
from app.core.queries.get_vehicle_availability import GetVehicleAvailability, GetVehicleAvailabilityRequest
from app.core.queries.ports.mobile_vehicle_reader import VehicleAvailabilityQm
from app.infrastructure.auth_ctx.exceptions import AuthenticationError
from app.infrastructure.exceptions import ReaderError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE


def make_check_availability_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.get(
        "/vehicles/{vehicle_id}/availability",
        error_map={
            AuthenticationError: status.HTTP_401_UNAUTHORIZED,
            AuthorizationError: status.HTTP_403_FORBIDDEN,
            ReaderError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
        },
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def check_availability(
        vehicle_id: UUID,
        interactor: FromDishka[GetVehicleAvailability],
        scheduled_start: Annotated[datetime, Query(...)],
        scheduled_end: Annotated[datetime, Query(...)],
    ) -> VehicleAvailabilityQm:
        return await interactor.execute(
            GetVehicleAvailabilityRequest(
                vehicle_id=vehicle_id,
                scheduled_start=scheduled_start,
                scheduled_end=scheduled_end,
            )
        )

    return router
