import datetime
from typing import Annotated
from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Query, status
from fastapi_error_map import ErrorAwareRouter

from app.core.queries.get_cash_flow import GetCashFlow, GetCashFlowRequest
from app.core.queries.models.report_cash_flow import CashFlowQm
from app.infrastructure.auth_ctx.exceptions import AuthenticationError
from app.infrastructure.exceptions import ReaderError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE


def make_cash_flow_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.get(
        "/cash-flow",
        error_map={
            AuthenticationError: status.HTTP_401_UNAUTHORIZED,
            ReaderError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
        },
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def get_cash_flow(
        organization_id: Annotated[UUID, Query(...)],
        date_from: Annotated[datetime.date, Query(alias="from")],
        date_to: Annotated[datetime.date, Query(alias="to")],
        interactor: FromDishka[GetCashFlow] = ...,  # type: ignore[assignment]
    ) -> CashFlowQm:
        request = GetCashFlowRequest(
            organization_id=organization_id,
            date_from=date_from,
            date_to=date_to,
        )
        return await interactor.execute(request)

    return router
