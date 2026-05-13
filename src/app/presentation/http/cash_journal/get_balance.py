from typing import Annotated
from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Query, status
from fastapi_error_map import ErrorAwareRouter

from app.core.queries.get_cash_journal_balance import GetCashJournalBalance, GetCashJournalBalanceRequest
from app.core.queries.ports.cash_journal_reader import CashJournalBalanceQm
from app.infrastructure.exceptions import ReaderError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE


def make_get_balance_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.get(
        "/balance",
        error_map={
            ReaderError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
        },
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def get_balance(
        organization_id: Annotated[UUID, Query(...)],
        interactor: FromDishka[GetCashJournalBalance] = ...,  # type: ignore[assignment]
    ) -> CashJournalBalanceQm:
        request = GetCashJournalBalanceRequest(organization_id=organization_id)
        return await interactor.execute(request)

    return router
