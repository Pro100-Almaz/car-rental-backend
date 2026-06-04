import logging
from dataclasses import dataclass
from datetime import date
from uuid import UUID

from app.core.queries.ports.cash_journal_reader import CashJournalBalanceQm, CashJournalReader

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class GetCashJournalBalanceRequest:
    organization_id: UUID
    date_from: date | None = None
    date_to: date | None = None


class GetCashJournalBalance:
    def __init__(
        self,
        cash_journal_reader: CashJournalReader,
    ) -> None:
        self._cash_journal_reader = cash_journal_reader

    async def execute(self, request: GetCashJournalBalanceRequest) -> CashJournalBalanceQm:
        logger.info("Get cash journal balance: started.")

        result = await self._cash_journal_reader.get_balance(
            organization_id=request.organization_id,
            date_from=request.date_from,
            date_to=request.date_to,
        )

        logger.info("Get cash journal balance: done.")
        return result
