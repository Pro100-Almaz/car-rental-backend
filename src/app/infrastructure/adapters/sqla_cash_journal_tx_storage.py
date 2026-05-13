from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.commands.ports.cash_journal_tx_storage import CashJournalTxStorage
from app.core.common.entities.cash_journal_entry import CashJournalEntry
from app.core.common.entities.types_ import CashJournalEntryId
from app.infrastructure.exceptions import StorageError


class SqlaCashJournalTxStorage(CashJournalTxStorage):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def add(self, entry: CashJournalEntry) -> None:
        try:
            self._session.add(entry)
        except SQLAlchemyError as e:
            raise StorageError from e

    async def get_by_id(
        self,
        entry_id: CashJournalEntryId,
        *,
        for_update: bool = False,
    ) -> CashJournalEntry | None:
        try:
            return await self._session.get(
                CashJournalEntry,
                entry_id,
                with_for_update=for_update,
            )
        except SQLAlchemyError as e:
            raise StorageError from e
