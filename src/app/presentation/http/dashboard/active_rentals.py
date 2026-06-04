import datetime
from typing import Annotated
from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Query, status
from fastapi_error_map import ErrorAwareRouter

from app.core.queries.get_dashboard_active_rentals import (
    GetDashboardActiveRentals,
    GetDashboardActiveRentalsRequest,
)
from app.core.queries.models.dashboard_active_rentals import DashboardActiveRentalsQm
from app.infrastructure.exceptions import ReaderError
from app.infrastructure.auth_ctx.exceptions import AuthenticationError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE


def make_active_rentals_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.get(
        "/active-rentals",
        error_map={
            AuthenticationError: status.HTTP_401_UNAUTHORIZED,
            ReaderError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
        },
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def get_active_rentals(
        organization_id: Annotated[UUID, Query(...)],
        limit: Annotated[int, Query(ge=1, le=50)] = 5,
        interactor: FromDishka[GetDashboardActiveRentals] = ...,  # type: ignore[assignment]
    ) -> DashboardActiveRentalsQm:
        now = datetime.datetime.now(tz=datetime.timezone.utc)
        request = GetDashboardActiveRentalsRequest(
            organization_id=organization_id,
            limit=limit,
            now=now,
        )
        return await interactor.execute(request)

    return router
