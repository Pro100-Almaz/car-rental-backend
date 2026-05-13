from datetime import date
from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, status
from fastapi_error_map import ErrorAwareRouter

from app.core.queries.get_vehicle_financials import GetVehicleFinancials, GetVehicleFinancialsRequest
from app.core.queries.models.vehicle_financials import VehicleFinancialsQm
from app.infrastructure.exceptions import ReaderError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE


def make_get_vehicle_financials_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.get(
        "/{vehicle_id}/financials",
        error_map={
            ReaderError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
        },
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def get_vehicle_financials(
        vehicle_id: UUID,
        date_from: date,
        date_to: date,
        interactor: FromDishka[GetVehicleFinancials],
    ) -> VehicleFinancialsQm:
        return await interactor.execute(
            GetVehicleFinancialsRequest(
                vehicle_id=vehicle_id,
                date_from=date_from,
                date_to=date_to,
            )
        )

    return router
