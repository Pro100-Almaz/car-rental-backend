from typing import Annotated
from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Query, status
from fastapi_error_map import ErrorAwareRouter

from app.core.queries.list_investor_payouts import ListInvestorPayouts, ListInvestorPayoutsRequest
from app.core.queries.ports.investor_reader import ListInvestorPayoutsQm
from app.infrastructure.exceptions import StorageError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE


def make_list_payouts_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.get(
        "/{investor_id}/payouts",
        error_map={
            StorageError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
        },
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def list_payouts(
        investor_id: UUID,
        payout_status: Annotated[str | None, Query(alias="status")] = None,
        interactor: FromDishka[ListInvestorPayouts] = ...,  # type: ignore[assignment]
    ) -> ListInvestorPayoutsQm:
        request = ListInvestorPayoutsRequest(
            investor_id=investor_id,
            status=payout_status,
        )
        return await interactor.execute(request)

    return router
