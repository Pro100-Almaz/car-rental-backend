import calendar
import datetime
from typing import Annotated
from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Query, status
from fastapi_error_map import ErrorAwareRouter

from app.core.queries.get_company_pnl import GetCompanyPnl, GetCompanyPnlRequest
from app.core.queries.models.report_pnl import CompanyPnlQm
from app.infrastructure.auth_ctx.exceptions import AuthenticationError
from app.infrastructure.exceptions import ReaderError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE


def make_pnl_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.get(
        "/pnl",
        error_map={
            AuthenticationError: status.HTTP_401_UNAUTHORIZED,
            ReaderError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
        },
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def get_pnl(
        organization_id: Annotated[UUID, Query(...)],
        period: Annotated[str | None, Query(description="YYYY-MM format")] = None,
        date_from: Annotated[datetime.date | None, Query()] = None,
        date_to: Annotated[datetime.date | None, Query()] = None,
        interactor: FromDishka[GetCompanyPnl] = ...,  # type: ignore[assignment]
    ) -> CompanyPnlQm:
        if period is not None:
            year, month = int(period[:4]), int(period[5:7])
            date_from = datetime.date(year, month, 1)
            date_to = datetime.date(year, month, calendar.monthrange(year, month)[1])
        elif date_from is None or date_to is None:
            today = datetime.datetime.now(tz=datetime.UTC).date()
            date_from = datetime.date(today.year, today.month, 1)
            date_to = datetime.date(today.year, today.month, calendar.monthrange(today.year, today.month)[1])

        request = GetCompanyPnlRequest(
            organization_id=organization_id,
            date_from=date_from,
            date_to=date_to,
        )
        return await interactor.execute(request)

    return router
