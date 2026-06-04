from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.queries.models.extension_request import ExtensionRequestQm, ListExtensionRequestsQm
from app.core.queries.ports.extension_request_reader import ExtensionRequestReader
from app.infrastructure.exceptions import ReaderError
from app.infrastructure.persistence_sqla.mappings.extension_request import extension_requests_table


class SqlaExtensionRequestReader(ExtensionRequestReader):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _base_columns(self) -> list:
        t = extension_requests_table
        return [
            t.c.id,
            t.c.organization_id,
            t.c.rental_id,
            t.c.client_id,
            t.c.new_end_date,
            t.c.additional_cost,
            t.c.status,
            t.c.rejection_reason,
            t.c.reviewed_by,
            t.c.reviewed_at,
            t.c.created_at,
        ]

    def _row_to_qm(self, row) -> ExtensionRequestQm:
        return ExtensionRequestQm(
            id=row.id,
            organization_id=row.organization_id,
            rental_id=row.rental_id,
            client_id=row.client_id,
            new_end_date=row.new_end_date,
            additional_cost=row.additional_cost,
            status=row.status,
            rejection_reason=row.rejection_reason,
            reviewed_by=row.reviewed_by,
            reviewed_at=row.reviewed_at,
            created_at=row.created_at,
        )

    async def list_pending(
        self,
        *,
        organization_id: UUID,
    ) -> ListExtensionRequestsQm:
        try:
            t = extension_requests_table
            stmt = (
                select(*self._base_columns())
                .where(t.c.organization_id == organization_id)
                .where(t.c.status == "pending")
                .order_by(t.c.created_at.asc())
            )
            result = await self._session.execute(stmt)
            rows = result.all()
            items = [self._row_to_qm(row) for row in rows]
            return ListExtensionRequestsQm(items=items, total=len(items))
        except SQLAlchemyError as e:
            raise ReaderError from e

    async def count_pending(
        self,
        *,
        organization_id: UUID,
    ) -> int:
        try:
            t = extension_requests_table
            stmt = (
                select(func.count())
                .select_from(t)
                .where(t.c.organization_id == organization_id)
                .where(t.c.status == "pending")
            )
            result = await self._session.execute(stmt)
            return result.scalar_one()
        except SQLAlchemyError as e:
            raise ReaderError from e
