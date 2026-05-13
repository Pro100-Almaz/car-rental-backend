from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, status
from fastapi_error_map import ErrorAwareRouter
from pydantic import BaseModel, ConfigDict

from app.core.commands.bulk_change_vehicle_status import (
    BulkChangeVehicleStatus,
    BulkChangeVehicleStatusRequest,
    BulkChangeVehicleStatusResponse,
)
from app.core.common.entities.types_ import VehicleStatus
from app.infrastructure.exceptions import StorageError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE


class BulkChangeStatusBody(BaseModel):
    model_config = ConfigDict(frozen=True)

    vehicle_ids: list[UUID]
    status: VehicleStatus


def make_bulk_change_status_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.post(
        "/bulk-status",
        error_map={
            StorageError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
        },
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def bulk_change_vehicle_status(
        body: BulkChangeStatusBody,
        interactor: FromDishka[BulkChangeVehicleStatus],
    ) -> BulkChangeVehicleStatusResponse:
        return await interactor.execute(
            BulkChangeVehicleStatusRequest(
                vehicle_ids=body.vehicle_ids,
                status=body.status,
            )
        )

    return router
