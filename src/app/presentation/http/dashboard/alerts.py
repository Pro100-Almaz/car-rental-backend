import datetime
from typing import Annotated
from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Query, status
from fastapi_error_map import ErrorAwareRouter

from app.core.queries.get_dashboard_alerts import GetDashboardAlerts, GetDashboardAlertsRequest
from app.core.queries.models.dashboard_alerts import DashboardAlertsQm
from app.infrastructure.auth_ctx.exceptions import AuthenticationError
from app.infrastructure.exceptions import ReaderError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE


def make_alerts_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.get(
        "/alerts",
        error_map={
            AuthenticationError: status.HTTP_401_UNAUTHORIZED,
            ReaderError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
        },
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def get_alerts(
        organization_id: Annotated[UUID, Query(...)],
        interactor: FromDishka[GetDashboardAlerts] = ...,  # type: ignore[assignment]
    ) -> DashboardAlertsQm:
        now = datetime.datetime.now(tz=datetime.UTC)
        request = GetDashboardAlertsRequest(
            organization_id=organization_id,
            now=now,
        )
        return await interactor.execute(request)

    return router
