from sqlalchemy import UUID, Column, DateTime, ForeignKey, String, Table

from app.core.common.entities.client_documents import ClientDocument
from app.infrastructure.persistence_sqla.registry import mapper_registry

client_document_table = Table(
    "client_documents",
    mapper_registry.metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column("client_id", UUID(as_uuid=True), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False),
    Column("status", String(20), nullable=False, server_default="required"),
    Column("document_type", String(50), nullable=False),
    Column("name", String(50), nullable=False),
    Column("description", String(255), nullable=True, comment="Description of the document"),
    Column("url", String(500), nullable=True),
    Column("created_at", DateTime, server_default="now()"),
    Column("updated_at", DateTime, server_default="now()", onupdate="now()"),
)


def map_client_document_table() -> None:
    mapper_registry.map_imperatively(
        ClientDocument,
        client_document_table,
        properties={
            "id_": client_document_table.c.id,
            "client_id": client_document_table.c.client_id,
            "status": client_document_table.c.status,
            "document_type": client_document_table.c.document_type,
            "name": client_document_table.c.name,
            "description": client_document_table.c.description,
            "url": client_document_table.c.url,
            "created_at": client_document_table.c.created_at,
            "updated_at": client_document_table.c.updated_at,
        },
        column_prefix="__",
    )
