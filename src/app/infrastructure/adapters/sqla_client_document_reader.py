from typing import Any
from uuid import UUID

from sqlalchemy import Row, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.queries.models.client_documents import ClientDocumentListItemQm, ClientDocumentQm, GetClientDocumentsQm
from app.core.queries.ports.client_document_reader import ClientDocumentReader
from app.infrastructure.exceptions import ReaderError
from app.infrastructure.persistence_sqla.mappings.client_documents import client_document_table


class SqlaClientDocumentReader(ClientDocumentReader):
    def __init__(self, session: AsyncSession):
        self._session = session

    def base_columns(self) -> tuple[Any, ...]:
        return (
            client_document_table.c.id,
            client_document_table.c.client_id,
            client_document_table.c.document_type,
            client_document_table.c.status,
            client_document_table.c.name,
            client_document_table.c.description,
            client_document_table.c.url,
            client_document_table.c.created_at,
            client_document_table.c.updated_at,
        )

    def row_to_qm(self, row: Row[Any]) -> ClientDocumentQm:
        return ClientDocumentQm(
            id=row.id,
            client_id=row.client_id,
            document_type=row.document_type,
            status=row.status,
            name=row.name,
            description=row.description,
            url=row.url,
            _created_at=row.created_at,
            _updated_at=row.updated_at,
        )

    def _row_to_item_qm(self, row: Row[Any]) -> ClientDocumentListItemQm:
        return ClientDocumentListItemQm(
            id=row.id, document_type=row.document_type, name=row.name, description=row.description, status=row.status
        )

    def _default_national_id_qm(self) -> ClientDocumentListItemQm:
        return ClientDocumentListItemQm(
            id=None, document_type="national_id", name="National ID", description="National ID", status="required"
        )

    def _default_driver_license_qm(self) -> ClientDocumentListItemQm:
        return ClientDocumentListItemQm(
            id=None,
            document_type="driver_licence",
            name="Driver License",
            description="Driver License",
            status="required",
        )

    async def list_client_documents(self, *, client_id: UUID) -> GetClientDocumentsQm:
        stmt = (
            select(*self.base_columns())
            .where(client_document_table.c.client_id == client_id)
            .order_by(client_document_table.c.created_at.desc())
        )

        try:
            result = await self._session.execute(stmt)
            rows = result.all()
        except SQLAlchemyError as e:
            raise ReaderError from e

        documents = {row.document_type: self._row_to_item_qm(row) for row in rows}
        return GetClientDocumentsQm(
            national_id=documents.get("national_id", self._default_national_id_qm()),
            driver_licence=documents.get("driver_licence", self._default_driver_license_qm()),
        )
