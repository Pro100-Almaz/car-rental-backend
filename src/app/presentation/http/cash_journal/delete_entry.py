from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, status
from fastapi_error_map import ErrorAwareRouter

from app.core.commands.delete_cash_journal_entry import DeleteCashJournalEntry, DeleteCashJournalEntryRequest
from app.core.commands.exceptions import CashJournalEntryNotFoundError
from app.infrastructure.auth_ctx.exceptions import AuthenticationError
from app.infrastructure.exceptions import StorageError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE


def make_delete_entry_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.delete(
        "/{entry_id}",
        error_map={
            AuthenticationError: status.HTTP_401_UNAUTHORIZED,
            StorageError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
            CashJournalEntryNotFoundError: status.HTTP_404_NOT_FOUND,
        },
        default_on_error=log_info,
        status_code=status.HTTP_204_NO_CONTENT,
    )
    @inject
    async def delete_entry(
        entry_id: UUID,
        interactor: FromDishka[DeleteCashJournalEntry],
    ) -> None:
        request = DeleteCashJournalEntryRequest(entry_id=entry_id)
        await interactor.execute(request)

    return router
