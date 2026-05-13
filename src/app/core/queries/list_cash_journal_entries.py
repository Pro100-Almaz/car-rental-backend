from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date
from uuid import UUID

from app.core.queries.ports.cash_journal_reader import CashJournalReader, ListCashJournalEntriesQm

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class ListCashJournalEntriesRequest:
    organization_id: UUID
    operation_type: str | None = None
    vehicle_id: UUID | None = None
    date_from: date | None = None
    date_to: date | None = None


class ListCashJournalEntries:
    def __init__(
        self,
        cash_journal_reader: CashJournalReader,
    ) -> None:
        self._cash_journal_reader = cash_journal_reader

    async def execute(self, request: ListCashJournalEntriesRequest) -> ListCashJournalEntriesQm:
        logger.info("List cash journal entries: started.")

        result = await self._cash_journal_reader.list_entries(
            organization_id=request.organization_id,
            operation_type=request.operation_type,
            vehicle_id=request.vehicle_id,
            date_from=request.date_from,
            date_to=request.date_to,
        )

        logger.info("List cash journal entries: done.")
        return result
