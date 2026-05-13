import datetime
from typing import Annotated
from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Query, status
from fastapi_error_map import ErrorAwareRouter

from app.core.queries.list_cash_journal_entries import ListCashJournalEntries, ListCashJournalEntriesRequest
from app.core.queries.ports.cash_journal_reader import ListCashJournalEntriesQm
from app.infrastructure.exceptions import ReaderError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE


def make_list_entries_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.get(
        "/",
        error_map={
            ReaderError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
        },
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def list_entries(
        organization_id: Annotated[UUID, Query(...)],
        operation_type: Annotated[str | None, Query()] = None,
        vehicle_id: Annotated[UUID | None, Query()] = None,
        date_from: Annotated[datetime.date | None, Query()] = None,
        date_to: Annotated[datetime.date | None, Query()] = None,
        interactor: FromDishka[ListCashJournalEntries] = ...,  # type: ignore[assignment]
    ) -> ListCashJournalEntriesQm:
        request = ListCashJournalEntriesRequest(
            organization_id=organization_id,
            operation_type=operation_type,
            vehicle_id=vehicle_id,
            date_from=date_from,
            date_to=date_to,
        )
        return await interactor.execute(request)

    return router
