import datetime
from typing import Annotated

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Query, status
from fastapi_error_map import ErrorAwareRouter

from app.core.commands.exceptions import InvestorNotFoundError
from app.core.queries.investor_portal_dashboard import InvestorPortalDashboard, InvestorPortalDashboardRequest
from app.core.queries.models.investor_pnl import InvestorPnlQm
from app.infrastructure.auth_ctx.exceptions import AuthenticationError
from app.infrastructure.exceptions import ReaderError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE


def make_portal_dashboard_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.get(
        "/dashboard",
        error_map={
            AuthenticationError: status.HTTP_401_UNAUTHORIZED,
            ReaderError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
            InvestorNotFoundError: status.HTTP_404_NOT_FOUND,
        },
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def portal_dashboard(
        date_from: Annotated[datetime.date | None, Query()] = None,
        date_to: Annotated[datetime.date | None, Query()] = None,
        interactor: FromDishka[InvestorPortalDashboard] = ...,  # type: ignore[assignment]
    ) -> InvestorPnlQm:
        request = InvestorPortalDashboardRequest(
            date_from=date_from,
            date_to=date_to,
        )
        return await interactor.execute(request)

    return router
