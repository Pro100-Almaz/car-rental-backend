from typing import Annotated
from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Query, status
from fastapi_error_map import ErrorAwareRouter

from app.core.common.authorization.exceptions import AuthorizationError
from app.core.queries.get_mobile_metrics import GetMobileMetrics, GetMobileMetricsRequest
from app.core.queries.models.mobile_metrics import MobileMetricsQm
from app.infrastructure.auth_ctx.exceptions import AuthenticationError
from app.infrastructure.exceptions import ReaderError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE


def make_mobile_metrics_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.get(
        "/mobile-metrics",
        error_map={
            AuthenticationError: status.HTTP_401_UNAUTHORIZED,
            AuthorizationError: status.HTTP_403_FORBIDDEN,
            ReaderError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
        },
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def get_mobile_metrics(
        interactor: FromDishka[GetMobileMetrics],
        organization_id: Annotated[UUID, Query(...)],
    ) -> MobileMetricsQm:
        return await interactor.execute(GetMobileMetricsRequest(organization_id=organization_id))

    return router
