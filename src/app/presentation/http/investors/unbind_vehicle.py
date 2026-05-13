from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, status
from fastapi_error_map import ErrorAwareRouter

from app.core.commands.exceptions import VehicleInvestorNotFoundError
from app.core.commands.unbind_vehicle_investor import UnbindVehicleInvestor, UnbindVehicleInvestorRequest
from app.infrastructure.exceptions import StorageError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE


def make_unbind_vehicle_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.delete(
        "/{investor_id}/vehicles/{vehicle_investor_id}",
        error_map={
            StorageError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
            VehicleInvestorNotFoundError: status.HTTP_404_NOT_FOUND,
        },
        default_on_error=log_info,
        status_code=status.HTTP_204_NO_CONTENT,
    )
    @inject
    async def unbind_vehicle(
        vehicle_investor_id: UUID,
        interactor: FromDishka[UnbindVehicleInvestor],
    ) -> None:
        request = UnbindVehicleInvestorRequest(vehicle_investor_id=vehicle_investor_id)
        await interactor.execute(request)

    return router
