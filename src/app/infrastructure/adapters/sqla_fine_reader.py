from typing import Any
from uuid import UUID

from sqlalchemy import Row, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.queries.models.fine import FineQm
from app.core.queries.ports.fine_reader import FineReader, ListFinesQm
from app.infrastructure.exceptions import ReaderError
from app.infrastructure.persistence_sqla.mappings.fine import fines_table


class SqlaFineReader(FineReader):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _base_columns(self) -> tuple[Any, ...]:
        return (
            fines_table.c.id,
            fines_table.c.organization_id,
            fines_table.c.vehicle_id,
            fines_table.c.rental_id,
            fines_table.c.client_id,
            fines_table.c.fine_type,
            fines_table.c.amount,
            fines_table.c.description,
            fines_table.c.fine_date,
            fines_table.c.document_url,
            fines_table.c.status,
            fines_table.c.created_at,
            fines_table.c.updated_at,
        )

    def _row_to_qm(self, row: Row[Any]) -> FineQm:
        return FineQm(
            id=row.id,
            organization_id=row.organization_id,
            vehicle_id=row.vehicle_id,
            rental_id=row.rental_id,
            client_id=row.client_id,
            fine_type=row.fine_type,
            amount=row.amount,
            description=row.description,
            fine_date=row.fine_date,
            document_url=row.document_url,
            status=row.status,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    async def get_by_id(
        self,
        *,
        fine_id: UUID,
    ) -> FineQm | None:
        stmt = select(*self._base_columns()).where(
            fines_table.c.id == fine_id,
        )
        try:
            result = await self._session.execute(stmt)
            row = result.one_or_none()
        except SQLAlchemyError as e:
            raise ReaderError from e
        if row is None:
            return None
        return self._row_to_qm(row)

    async def list_fines(
        self,
        *,
        organization_id: UUID,
        vehicle_id: UUID | None = None,
        client_id: UUID | None = None,
        status: str | None = None,
    ) -> ListFinesQm:
        stmt = (
            select(*self._base_columns())
            .where(fines_table.c.organization_id == organization_id)
            .order_by(fines_table.c.fine_date.desc())
        )
        if vehicle_id is not None:
            stmt = stmt.where(fines_table.c.vehicle_id == vehicle_id)
        if client_id is not None:
            stmt = stmt.where(fines_table.c.client_id == client_id)
        if status is not None:
            stmt = stmt.where(fines_table.c.status == status)
        try:
            result = await self._session.execute(stmt)
            rows = result.all()
        except SQLAlchemyError as e:
            raise ReaderError from e
        fines = [self._row_to_qm(row) for row in rows]
        return ListFinesQm(
            fines=fines,
            total=len(fines),
        )
