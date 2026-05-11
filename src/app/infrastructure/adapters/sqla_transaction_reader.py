from typing import Any
from uuid import UUID

from sqlalchemy import Row, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.queries.models.transaction import TransactionQm
from app.core.queries.ports.transaction_reader import ListTransactionsQm, TransactionReader
from app.infrastructure.exceptions import ReaderError
from app.infrastructure.persistence_sqla.mappings.transaction import transactions_table


class SqlaTransactionReader(TransactionReader):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _base_columns(self) -> tuple[Any, ...]:
        return (
            transactions_table.c.id,
            transactions_table.c.organization_id,
            transactions_table.c.rental_id,
            transactions_table.c.client_id,
            transactions_table.c.type,
            transactions_table.c.amount,
            transactions_table.c.currency,
            transactions_table.c.payment_method,
            transactions_table.c.status,
            transactions_table.c.external_id,
            transactions_table.c.metadata,
            transactions_table.c.created_at,
            transactions_table.c.updated_at,
        )

    def _row_to_qm(self, row: Row[Any]) -> TransactionQm:
        return TransactionQm(
            id=row.id,
            organization_id=row.organization_id,
            rental_id=row.rental_id,
            client_id=row.client_id,
            type=row.type,
            amount=row.amount,
            currency=row.currency,
            payment_method=row.payment_method,
            status=row.status,
            external_id=row.external_id,
            metadata=row.metadata,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    async def get_by_id(
        self,
        *,
        transaction_id: UUID,
    ) -> TransactionQm | None:
        stmt = select(*self._base_columns()).where(
            transactions_table.c.id == transaction_id,
        )
        try:
            result = await self._session.execute(stmt)
            row = result.one_or_none()
        except SQLAlchemyError as e:
            raise ReaderError from e
        if row is None:
            return None
        return self._row_to_qm(row)

    async def list_transactions(
        self,
        *,
        organization_id: UUID,
        rental_id: UUID | None = None,
        client_id: UUID | None = None,
        type_: str | None = None,
        status: str | None = None,
    ) -> ListTransactionsQm:
        stmt = (
            select(*self._base_columns())
            .where(transactions_table.c.organization_id == organization_id)
            .order_by(transactions_table.c.created_at.desc())
        )
        if rental_id is not None:
            stmt = stmt.where(transactions_table.c.rental_id == rental_id)
        if client_id is not None:
            stmt = stmt.where(transactions_table.c.client_id == client_id)
        if type_ is not None:
            stmt = stmt.where(transactions_table.c.type == type_)
        if status is not None:
            stmt = stmt.where(transactions_table.c.status == status)
        try:
            result = await self._session.execute(stmt)
            rows = result.all()
        except SQLAlchemyError as e:
            raise ReaderError from e
        transactions = [self._row_to_qm(row) for row in rows]
        return ListTransactionsQm(
            transactions=transactions,
            total=len(transactions),
        )
