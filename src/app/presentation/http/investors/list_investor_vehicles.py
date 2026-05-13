from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, status
from fastapi_error_map import ErrorAwareRouter

from app.core.queries.list_investor_vehicles import ListInvestorVehicles, ListInvestorVehiclesRequest
from app.core.queries.ports.investor_reader import ListVehicleInvestorsQm
from app.infrastructure.exceptions import StorageError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE


def make_list_investor_vehicles_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.get(
        "/{investor_id}/vehicles",
        error_map={
            StorageError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
        },
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def list_investor_vehicles(
        investor_id: UUID,
        interactor: FromDishka[ListInvestorVehicles],
    ) -> ListVehicleInvestorsQm:
        request = ListInvestorVehiclesRequest(investor_id=investor_id)
        return await interactor.execute(request)

    return router
