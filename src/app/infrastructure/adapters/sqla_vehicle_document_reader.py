from typing import Any
from uuid import UUID

from sqlalchemy import Row, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.queries.models.vehicle_document import ListVehicleDocumentsQm, VehicleDocumentQm
from app.core.queries.ports.vehicle_document_reader import VehicleDocumentReader
from app.infrastructure.exceptions import ReaderError
from app.infrastructure.persistence_sqla.mappings.vehicle_document import vehicle_documents_table


class SqlaVehicleDocumentReader(VehicleDocumentReader):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _base_columns(self) -> tuple[Any, ...]:
        return (
            vehicle_documents_table.c.id,
            vehicle_documents_table.c.vehicle_id,
            vehicle_documents_table.c.document_type,
            vehicle_documents_table.c.name,
            vehicle_documents_table.c.url,
            vehicle_documents_table.c.expiry_date,
            vehicle_documents_table.c.created_at,
        )

    def _row_to_qm(self, row: Row[Any]) -> VehicleDocumentQm:
        return VehicleDocumentQm(
            id=row.id,
            vehicle_id=row.vehicle_id,
            document_type=row.document_type,
            name=row.name,
            url=row.url,
            expiry_date=row.expiry_date,
            created_at=row.created_at,
        )

    async def list_documents(
        self,
        *,
        vehicle_id: UUID,
    ) -> ListVehicleDocumentsQm:
        stmt = (
            select(*self._base_columns())
            .where(vehicle_documents_table.c.vehicle_id == vehicle_id)
            .order_by(vehicle_documents_table.c.created_at.desc())
        )
        try:
            result = await self._session.execute(stmt)
            rows = result.all()
        except SQLAlchemyError as e:
            raise ReaderError from e
        documents = [self._row_to_qm(row) for row in rows]
        return ListVehicleDocumentsQm(documents=documents, total=len(documents))
