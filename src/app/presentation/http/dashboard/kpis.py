import calendar
import datetime
from typing import Annotated
from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Query, status
from fastapi_error_map import ErrorAwareRouter

from app.core.queries.get_dashboard_kpis import GetDashboardKpis, GetDashboardKpisRequest
from app.core.queries.models.dashboard_kpis import DashboardKpisQm
from app.infrastructure.exceptions import ReaderError
from app.infrastructure.auth_ctx.exceptions import AuthenticationError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE


def _parse_period(period: str | None) -> tuple[datetime.date, datetime.date]:
    if period is not None:
        year, month = int(period[:4]), int(period[5:7])
        return datetime.date(year, month, 1), datetime.date(year, month, calendar.monthrange(year, month)[1])
    today = datetime.date.today()
    return (
        datetime.date(today.year, today.month, 1),
        datetime.date(today.year, today.month, calendar.monthrange(today.year, today.month)[1]),
    )


def make_kpis_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.get(
        "/kpis",
        error_map={
            AuthenticationError: status.HTTP_401_UNAUTHORIZED,
            ReaderError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
        },
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def get_kpis(
        organization_id: Annotated[UUID, Query(...)],
        period: Annotated[str | None, Query()] = None,
        interactor: FromDishka[GetDashboardKpis] = ...,  # type: ignore[assignment]
    ) -> DashboardKpisQm:
        d_from, d_to = _parse_period(period)
        now = datetime.datetime.now(tz=datetime.timezone.utc)
        request = GetDashboardKpisRequest(
            organization_id=organization_id,
            date_from=d_from,
            date_to=d_to,
            now=now,
        )
        return await interactor.execute(request)

    return router
