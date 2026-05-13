import logging
from dataclasses import dataclass
from uuid import UUID

from app.core.commands.exceptions import CashJournalEntryNotFoundError
from app.core.commands.ports.cash_journal_tx_storage import CashJournalTxStorage
from app.core.commands.ports.transaction_manager import TransactionManager
from app.core.commands.ports.utc_timer import UtcTimer
from app.core.common.authorization.authorize import authorize
from app.core.common.authorization.current_user_service import CurrentUserService
from app.core.common.authorization.rbac import HasPermission, PermissionCheckContext
from app.core.common.entities.types_ import CashJournalEntryId, UserId

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class ConfirmCashJournalEntryRequest:
    entry_id: UUID


class ConfirmCashJournalEntry:
    def __init__(
        self,
        current_user_service: CurrentUserService,
        utc_timer: UtcTimer,
        cash_journal_tx_storage: CashJournalTxStorage,
        transaction_manager: TransactionManager,
    ) -> None:
        self._current_user_service = current_user_service
        self._utc_timer = utc_timer
        self._cash_journal_tx_storage = cash_journal_tx_storage
        self._transaction_manager = transaction_manager

    async def execute(self, request: ConfirmCashJournalEntryRequest) -> None:
        logger.info("Confirm cash journal entry: started.")

        current_user = await self._current_user_service.get_current_user()
        authorize(
            HasPermission(),
            context=PermissionCheckContext(
                subject=current_user,
                required_permission="finance.update",
            ),
        )

        entry_id = CashJournalEntryId(request.entry_id)
        entry = await self._cash_journal_tx_storage.get_by_id(entry_id, for_update=True)
        if entry is None:
            raise CashJournalEntryNotFoundError

        entry.confirmed_by = UserId(current_user.id_)
        entry.confirmed_at = self._utc_timer.now.value
        await self._transaction_manager.commit()

        logger.info("Confirm cash journal entry: done.")
