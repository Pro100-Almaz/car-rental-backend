from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from uuid import UUID

from app.core.commands.exceptions import CashJournalEntryNotFoundError
from app.core.commands.ports.cash_journal_tx_storage import CashJournalTxStorage
from app.core.commands.ports.transaction_manager import TransactionManager
from app.core.common.authorization.authorize import authorize
from app.core.common.authorization.current_user_service import CurrentUserService
from app.core.common.authorization.rbac import HasPermission, PermissionCheckContext
from app.core.common.entities.cash_journal_entry import CashJournalEntry
from app.core.common.entities.types_ import (
    CashJournalEntryId,
    ExpenseCategoryId,
    OperationType,
    PaymentMethod,
    RentalId,
    VehicleId,
)

logger = logging.getLogger(__name__)

_UNSET = object()


@dataclass(frozen=True, slots=True, kw_only=True)
class UpdateCashJournalEntryRequest:
    entry_id: UUID
    date: date | object = _UNSET
    operation_type: OperationType | object = _UNSET
    vehicle_id: UUID | None | object = _UNSET
    rental_id: UUID | None | object = _UNSET
    expense_category_id: UUID | None | object = _UNSET
    payment_method: PaymentMethod | object = _UNSET
    amount: Decimal | object = _UNSET
    description: str | None | object = _UNSET
    receipt_url: str | None | object = _UNSET


class UpdateCashJournalEntry:
    def __init__(
        self,
        current_user_service: CurrentUserService,
        cash_journal_tx_storage: CashJournalTxStorage,
        transaction_manager: TransactionManager,
    ) -> None:
        self._current_user_service = current_user_service
        self._cash_journal_tx_storage = cash_journal_tx_storage
        self._transaction_manager = transaction_manager

    async def execute(self, request: UpdateCashJournalEntryRequest) -> None:
        logger.info("Update cash journal entry: started.")

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

        if self._apply_fields(request, entry):
            await self._transaction_manager.commit()

        logger.info("Update cash journal entry: done.")

    @staticmethod
    def _apply_fields(
        request: UpdateCashJournalEntryRequest,
        entry: CashJournalEntry,
    ) -> bool:
        changed = False
        for attr in ("date", "operation_type", "payment_method", "amount", "description", "receipt_url"):
            val = getattr(request, attr)
            if val is not _UNSET and val != getattr(entry, attr):
                setattr(entry, attr, val)
                changed = True

        vehicle_val = request.vehicle_id
        if vehicle_val is not _UNSET:
            new_vehicle_id = VehicleId(vehicle_val) if vehicle_val is not None else None  # type: ignore[arg-type]
            if new_vehicle_id != entry.vehicle_id:
                entry.vehicle_id = new_vehicle_id
                changed = True

        rental_val = request.rental_id
        if rental_val is not _UNSET:
            new_rental_id = RentalId(rental_val) if rental_val is not None else None  # type: ignore[arg-type]
            if new_rental_id != entry.rental_id:
                entry.rental_id = new_rental_id
                changed = True

        category_val = request.expense_category_id
        if category_val is not _UNSET:
            new_category_id = ExpenseCategoryId(category_val) if category_val is not None else None  # type: ignore[arg-type]
            if new_category_id != entry.expense_category_id:
                entry.expense_category_id = new_category_id
                changed = True

        return changed
