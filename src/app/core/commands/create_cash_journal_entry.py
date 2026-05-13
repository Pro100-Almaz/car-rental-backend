import logging
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import TypedDict
from uuid import UUID

from app.core.commands.ports.cash_journal_tx_storage import CashJournalTxStorage
from app.core.commands.ports.flusher import Flusher
from app.core.commands.ports.transaction_manager import TransactionManager
from app.core.commands.ports.utc_timer import UtcTimer
from app.core.common.authorization.authorize import authorize
from app.core.common.authorization.current_user_service import CurrentUserService
from app.core.common.authorization.rbac import HasPermission, PermissionCheckContext
from app.core.common.entities.cash_journal_entry import CashJournalEntry
from app.core.common.entities.types_ import (
    ExpenseCategoryId,
    OperationType,
    OrganizationId,
    PaymentMethod,
    RentalId,
    UserId,
    VehicleId,
)
from app.core.common.factories.id_factory import create_cash_journal_entry_id
from app.core.common.value_objects.utc_datetime import UtcDatetime

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class CreateCashJournalEntryRequest:
    organization_id: UUID
    date: date
    operation_type: OperationType
    vehicle_id: UUID | None = None
    rental_id: UUID | None = None
    expense_category_id: UUID | None = None
    payment_method: PaymentMethod
    amount: Decimal
    description: str | None = None
    receipt_url: str | None = None
    created_by: UUID


class CreateCashJournalEntryResponse(TypedDict):
    id: UUID
    created_at: datetime


class CreateCashJournalEntry:
    def __init__(
        self,
        current_user_service: CurrentUserService,
        utc_timer: UtcTimer,
        cash_journal_tx_storage: CashJournalTxStorage,
        flusher: Flusher,
        transaction_manager: TransactionManager,
    ) -> None:
        self._current_user_service = current_user_service
        self._utc_timer = utc_timer
        self._cash_journal_tx_storage = cash_journal_tx_storage
        self._flusher = flusher
        self._transaction_manager = transaction_manager

    async def execute(self, request: CreateCashJournalEntryRequest) -> CreateCashJournalEntryResponse:
        logger.info("Create cash journal entry: started.")

        current_user = await self._current_user_service.get_current_user()
        authorize(
            HasPermission(),
            context=PermissionCheckContext(
                subject=current_user,
                required_permission="finance.create",
            ),
        )

        now = UtcDatetime(self._utc_timer.now.value)
        entry = CashJournalEntry(
            id_=create_cash_journal_entry_id(),
            organization_id=OrganizationId(request.organization_id),
            date=request.date,
            operation_type=request.operation_type,
            vehicle_id=VehicleId(request.vehicle_id) if request.vehicle_id else None,
            rental_id=RentalId(request.rental_id) if request.rental_id else None,
            expense_category_id=ExpenseCategoryId(request.expense_category_id) if request.expense_category_id else None,
            payment_method=request.payment_method,
            amount=request.amount,
            description=request.description,
            receipt_url=request.receipt_url,
            confirmed_by=None,
            confirmed_at=None,
            created_by=UserId(request.created_by),
            created_at=now,
        )
        self._cash_journal_tx_storage.add(entry)
        await self._flusher.flush()
        await self._transaction_manager.commit()

        logger.info("Create cash journal entry: done.")
        return CreateCashJournalEntryResponse(
            id=entry.id_,
            created_at=entry.created_at.value,
        )
