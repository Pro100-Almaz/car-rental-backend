"""Add client_documents table.

Revision ID: c1d0c5d0c5u1
Revises: r3j3c7i0n001
Create Date: 2026-06-15 01:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c1d0c5d0c5u1"
down_revision: str | None = "r3j3c7i0n001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "client_documents",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "client_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("clients.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", sa.String(20), nullable=False, server_default="required"),
        sa.Column("document_type", sa.String(50), nullable=False),
        sa.Column("name", sa.String(50), nullable=False),
        sa.Column("description", sa.String(255), nullable=True, comment="Description of the document"),
        sa.Column("url", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()")),
    )
    op.create_index("ix_client_documents_client_id", "client_documents", ["client_id"])


def downgrade() -> None:
    op.drop_index("ix_client_documents_client_id", table_name="client_documents")
    op.drop_table("client_documents")
