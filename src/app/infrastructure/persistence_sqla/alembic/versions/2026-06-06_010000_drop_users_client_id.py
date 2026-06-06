"""Drop users.client_id (redundant back-reference; use clients.user_id instead).

Revision ID: d7r7o7p7c7i7
Revises: m6u6l6t6i6o6
Create Date: 2026-06-06 01:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d7r7o7p7c7i7"
down_revision: str | None = "m6u6l6t6i6o6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint("uq_users_client_id", "users", type_="unique")
    op.drop_constraint("fk_users_client_id_clients", "users", type_="foreignkey")
    op.drop_column("users", "client_id")


def downgrade() -> None:
    op.add_column(
        "users",
        sa.Column("client_id", sa.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_users_client_id_clients",
        "users",
        "clients",
        ["client_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_unique_constraint("uq_users_client_id", "users", ["client_id"])
