import logging
from dataclasses import dataclass
from uuid import UUID

from app.core.queries.models.cash_journal_entry import CashJournalEntryQm
from app.core.queries.ports.cash_journal_reader import CashJournalReader

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class GetCashJournalEntryRequest:
    entry_id: UUID


class GetCashJournalEntry:
    def __init__(
        self,
        cash_journal_reader: CashJournalReader,
    ) -> None:
        self._cash_journal_reader = cash_journal_reader

    async def execute(self, request: GetCashJournalEntryRequest) -> CashJournalEntryQm | None:
        logger.info("Get cash journal entry: started.")

        result = await self._cash_journal_reader.get_by_id(entry_id=request.entry_id)

        logger.info("Get cash journal entry: done.")
        return result
