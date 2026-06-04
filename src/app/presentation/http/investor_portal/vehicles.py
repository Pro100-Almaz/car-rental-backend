from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, status
from fastapi_error_map import ErrorAwareRouter

from app.core.commands.exceptions import InvestorNotFoundError
from app.core.queries.investor_portal_vehicles import InvestorPortalVehicles
from app.core.queries.ports.investor_reader import ListVehicleInvestorsQm
from app.infrastructure.exceptions import ReaderError
from app.infrastructure.auth_ctx.exceptions import AuthenticationError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE


def make_portal_vehicles_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.get(
        "/vehicles",
        error_map={
            AuthenticationError: status.HTTP_401_UNAUTHORIZED,
            ReaderError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
            InvestorNotFoundError: status.HTTP_404_NOT_FOUND,
        },
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def portal_vehicles(
        interactor: FromDishka[InvestorPortalVehicles] = ...,  # type: ignore[assignment]
    ) -> ListVehicleInvestorsQm:
        return await interactor.execute()

    return router
