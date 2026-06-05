import calendar
import datetime
from typing import Annotated
from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, HTTPException, Query, status
from fastapi_error_map import ErrorAwareRouter

from app.core.queries.get_dashboard_revenue_chart import (
    GetDashboardRevenueChart,
    GetDashboardRevenueChartRequest,
)
from app.core.queries.models.dashboard_revenue_chart import DashboardRevenueChartQm
from app.infrastructure.auth_ctx.exceptions import AuthenticationError
from app.infrastructure.exceptions import ReaderError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE


def _parse_period(period: str | None) -> tuple[datetime.date, datetime.date]:
    if period is not None:
        year, month = int(period[:4]), int(period[5:7])
        return datetime.date(year, month, 1), datetime.date(year, month, calendar.monthrange(year, month)[1])
    today = datetime.datetime.now(tz=datetime.UTC).date()
    return (
        datetime.date(today.year, today.month, 1),
        datetime.date(today.year, today.month, calendar.monthrange(today.year, today.month)[1]),
    )


def _parse_week(
    week_start: datetime.date,
    week_end: datetime.date,
) -> tuple[datetime.date, datetime.date]:
    if week_start.weekday() != 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="week_start must be a Monday",
        )
    if week_end != week_start + datetime.timedelta(days=6):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="week_end must be the Sunday following week_start (exactly 6 days later)",
        )
    return week_start, week_end


def make_revenue_chart_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.get(
        "/revenue-chart",
        error_map={
            AuthenticationError: status.HTTP_401_UNAUTHORIZED,
            ReaderError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
        },
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def get_revenue_chart(
        organization_id: Annotated[UUID, Query(...)],
        period: Annotated[str | None, Query()] = None,
        week_start: Annotated[datetime.date | None, Query()] = None,
        week_end: Annotated[datetime.date | None, Query()] = None,
        interactor: FromDishka[GetDashboardRevenueChart] = ...,  # type: ignore[assignment]
    ) -> DashboardRevenueChartQm:
        if week_start is not None and week_end is not None:
            d_from, d_to = _parse_week(week_start, week_end)
        elif week_start is not None or week_end is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Both week_start and week_end must be provided together",
            )
        else:
            d_from, d_to = _parse_period(period)

        request = GetDashboardRevenueChartRequest(
            organization_id=organization_id,
            date_from=d_from,
            date_to=d_to,
        )
        return await interactor.execute(request)

    return router
