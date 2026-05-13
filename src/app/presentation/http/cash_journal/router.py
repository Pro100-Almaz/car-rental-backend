from fastapi import APIRouter

from app.presentation.http.cash_journal.confirm_entry import make_confirm_entry_router
from app.presentation.http.cash_journal.create_entry import make_create_entry_router
from app.presentation.http.cash_journal.get_balance import make_get_balance_router
from app.presentation.http.cash_journal.get_entry import make_get_entry_router
from app.presentation.http.cash_journal.list_entries import make_list_entries_router
from app.presentation.http.cash_journal.update_entry import make_update_entry_router


def make_cash_journal_router() -> APIRouter:
    router = APIRouter(
        prefix="/cash-journal",
        tags=["Cash Journal"],
    )
    router.include_router(make_get_balance_router())
    router.include_router(make_create_entry_router())
    router.include_router(make_list_entries_router())
    router.include_router(make_get_entry_router())
    router.include_router(make_update_entry_router())
    router.include_router(make_confirm_entry_router())
    return router
