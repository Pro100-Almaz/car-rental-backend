"""Make idx_clients_phone a partial unique index (only enforces when phone <> '').

Revision ID: d8r8o8p8d8u8
Revises: d7r7o7p7c7i7
Create Date: 2026-06-06 02:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d8r8o8p8d8u8"
down_revision: str | None = "d7r7o7p7c7i7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_index("idx_clients_phone", table_name="clients")
    op.create_index(
        "idx_clients_phone",
        "clients",
        ["organization_id", "phone"],
        unique=True,
        postgresql_where=sa.text("phone <> ''"),
    )


def downgrade() -> None:
    op.drop_index("idx_clients_phone", table_name="clients")
    op.create_index(
        "idx_clients_phone",
        "clients",
        ["organization_id", "phone"],
        unique=True,
    )
