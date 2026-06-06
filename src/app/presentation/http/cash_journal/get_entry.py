from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, status
from fastapi_error_map import ErrorAwareRouter

from app.core.commands.exceptions import CashJournalEntryNotFoundError
from app.core.queries.get_cash_journal_entry import GetCashJournalEntry, GetCashJournalEntryRequest
from app.core.queries.models.cash_journal_entry import CashJournalEntryQm
from app.infrastructure.auth_ctx.exceptions import AuthenticationError
from app.infrastructure.exceptions import ReaderError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE


def make_get_entry_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.get(
        "/{entry_id}",
        error_map={
            AuthenticationError: status.HTTP_401_UNAUTHORIZED,
            ReaderError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
            CashJournalEntryNotFoundError: status.HTTP_404_NOT_FOUND,
        },
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
        responses={404: {"description": "Cash journal entry not found"}},
    )
    @inject
    async def get_entry(
        entry_id: UUID,
        interactor: FromDishka[GetCashJournalEntry],
    ) -> CashJournalEntryQm:
        result = await interactor.execute(GetCashJournalEntryRequest(entry_id=entry_id))
        if result is None:
            raise CashJournalEntryNotFoundError
        return result

    return router
