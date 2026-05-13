from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import Row, case, func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.queries.models.cash_journal_entry import CashJournalEntryQm
from app.core.queries.ports.cash_journal_reader import (
    CashJournalBalanceQm,
    CashJournalReader,
    ListCashJournalEntriesQm,
)
from app.infrastructure.exceptions import ReaderError
from app.infrastructure.persistence_sqla.mappings.cash_journal_entry import cash_journal_table


class SqlaCashJournalReader(CashJournalReader):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _base_columns(self) -> tuple[Any, ...]:
        return (
            cash_journal_table.c.id,
            cash_journal_table.c.organization_id,
            cash_journal_table.c.date,
            cash_journal_table.c.operation_type.label("operation_type"),
            cash_journal_table.c.vehicle_id,
            cash_journal_table.c.rental_id,
            cash_journal_table.c.expense_category_id,
            cash_journal_table.c.payment_method,
            cash_journal_table.c.amount,
            cash_journal_table.c.description,
            cash_journal_table.c.receipt_url,
            cash_journal_table.c.confirmed_by,
            cash_journal_table.c.confirmed_at,
            cash_journal_table.c.created_by,
            cash_journal_table.c.created_at,
        )

    def _row_to_qm(self, row: Row[Any]) -> CashJournalEntryQm:
        return CashJournalEntryQm(
            id=row.id,
            organization_id=row.organization_id,
            date=row.date,
            operation_type=row.operation_type,
            vehicle_id=row.vehicle_id,
            rental_id=row.rental_id,
            expense_category_id=row.expense_category_id,
            payment_method=row.payment_method,
            amount=row.amount,
            description=row.description,
            receipt_url=row.receipt_url,
            confirmed_by=row.confirmed_by,
            confirmed_at=row.confirmed_at,
            created_by=row.created_by,
            created_at=row.created_at,
        )

    async def get_by_id(
        self,
        *,
        entry_id: UUID,
    ) -> CashJournalEntryQm | None:
        stmt = select(*self._base_columns()).where(
            cash_journal_table.c.id == entry_id,
        )
        try:
            result = await self._session.execute(stmt)
            row = result.one_or_none()
        except SQLAlchemyError as e:
            raise ReaderError from e
        if row is None:
            return None
        return self._row_to_qm(row)

    async def list_entries(
        self,
        *,
        organization_id: UUID,
        operation_type: str | None = None,
        vehicle_id: UUID | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> ListCashJournalEntriesQm:
        stmt = (
            select(*self._base_columns())
            .where(cash_journal_table.c.organization_id == organization_id)
            .order_by(cash_journal_table.c.date.desc())
        )
        if operation_type is not None:
            stmt = stmt.where(cash_journal_table.c.operation_type == operation_type)
        if vehicle_id is not None:
            stmt = stmt.where(cash_journal_table.c.vehicle_id == vehicle_id)
        if date_from is not None:
            stmt = stmt.where(cash_journal_table.c.date >= date_from)
        if date_to is not None:
            stmt = stmt.where(cash_journal_table.c.date <= date_to)
        try:
            result = await self._session.execute(stmt)
            rows = result.all()
        except SQLAlchemyError as e:
            raise ReaderError from e
        entries = [self._row_to_qm(row) for row in rows]
        return ListCashJournalEntriesQm(
            entries=entries,
            total=len(entries),
        )

    async def get_balance(
        self,
        *,
        organization_id: UUID,
    ) -> CashJournalBalanceQm:
        income_sum = func.coalesce(
            func.sum(
                case(
                    (cash_journal_table.c.operation_type == "income", cash_journal_table.c.amount),
                    else_=Decimal(0),
                )
            ),
            Decimal(0),
        ).label("total_income")
        expense_sum = func.coalesce(
            func.sum(
                case(
                    (cash_journal_table.c.operation_type == "expense", cash_journal_table.c.amount),
                    else_=Decimal(0),
                )
            ),
            Decimal(0),
        ).label("total_expense")
        stmt = select(income_sum, expense_sum).where(
            cash_journal_table.c.organization_id == organization_id,
        )
        try:
            result = await self._session.execute(stmt)
            row = result.one()
        except SQLAlchemyError as e:
            raise ReaderError from e
        total_income = row.total_income or Decimal(0)
        total_expense = row.total_expense or Decimal(0)
        return CashJournalBalanceQm(
            total_income=total_income,
            total_expense=total_expense,
            balance=total_income - total_expense,
        )
