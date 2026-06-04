import calendar
from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Depends, status
from fastapi_error_map import ErrorAwareRouter
from pydantic import BaseModel, ConfigDict

from app.core.queries.get_rental_calendar import GetRentalCalendar, GetRentalCalendarRequest
from app.core.queries.models.rental_calendar import RentalCalendarQm
from app.infrastructure.auth_ctx.exceptions import AuthenticationError
from app.infrastructure.exceptions import ReaderError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE


class CalendarRequestSchema(BaseModel):
    model_config = ConfigDict(frozen=True)
    organization_id: UUID
    month: str


def make_get_rental_calendar_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.get(
        "/calendar",
        error_map={
            AuthenticationError: status.HTTP_401_UNAUTHORIZED,
            ReaderError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
        },
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def get_rental_calendar(
        request_schema: Annotated[CalendarRequestSchema, Depends()],
        interactor: FromDishka[GetRentalCalendar],
    ) -> RentalCalendarQm:
        year, month_num = (int(x) for x in request_schema.month.split("-"))
        month_start = datetime(year, month_num, 1, tzinfo=timezone.utc)
        _, last_day = calendar.monthrange(year, month_num)
        if month_num == 12:
            month_end = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
        else:
            month_end = datetime(year, month_num + 1, 1, tzinfo=timezone.utc)
        request = GetRentalCalendarRequest(
            organization_id=request_schema.organization_id,
            month_start=month_start,
            month_end=month_end,
        )
        return await interactor.execute(request)

    return router
