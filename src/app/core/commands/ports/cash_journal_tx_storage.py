from typing import Protocol

from app.core.common.entities.cash_journal_entry import CashJournalEntry
from app.core.common.entities.types_ import CashJournalEntryId


class CashJournalTxStorage(Protocol):
    def add(self, entry: CashJournalEntry) -> None: ...

    async def get_by_id(
        self,
        entry_id: CashJournalEntryId,
        *,
        for_update: bool = False,
    ) -> CashJournalEntry | None: ...
