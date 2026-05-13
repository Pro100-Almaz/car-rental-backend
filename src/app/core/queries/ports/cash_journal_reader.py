from __future__ import annotations

from abc import abstractmethod
from datetime import date
from decimal import Decimal
from typing import Protocol, TypedDict
from uuid import UUID

from app.core.queries.models.cash_journal_entry import CashJournalEntryQm


class ListCashJournalEntriesQm(TypedDict):
    entries: list[CashJournalEntryQm]
    total: int


class CashJournalBalanceQm(TypedDict):
    total_income: Decimal
    total_expense: Decimal
    balance: Decimal


class CashJournalReader(Protocol):
    @abstractmethod
    async def get_by_id(
        self,
        *,
        entry_id: UUID,
    ) -> CashJournalEntryQm | None: ...

    @abstractmethod
    async def list_entries(
        self,
        *,
        organization_id: UUID,
        operation_type: str | None = None,
        vehicle_id: UUID | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> ListCashJournalEntriesQm: ...

    @abstractmethod
    async def get_balance(
        self,
        *,
        organization_id: UUID,
    ) -> CashJournalBalanceQm: ...
