from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, status
from fastapi_error_map import ErrorAwareRouter

from app.core.commands.confirm_cash_journal_entry import ConfirmCashJournalEntry, ConfirmCashJournalEntryRequest
from app.core.commands.exceptions import CashJournalEntryNotFoundError
from app.core.common.exceptions import BusinessTypeError
from app.infrastructure.exceptions import StorageError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE


def make_confirm_entry_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.post(
        "/{entry_id}/confirm",
        error_map={
            StorageError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
            BusinessTypeError: status.HTTP_400_BAD_REQUEST,
            CashJournalEntryNotFoundError: status.HTTP_404_NOT_FOUND,
        },
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def confirm_entry(
        entry_id: UUID,
        interactor: FromDishka[ConfirmCashJournalEntry],
    ) -> None:
        await interactor.execute(ConfirmCashJournalEntryRequest(entry_id=entry_id))

    return router
