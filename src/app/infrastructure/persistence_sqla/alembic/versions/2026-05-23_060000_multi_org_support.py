"""Add client_organizations table for multi-org subscriptions and default org support.

Revision ID: m6u6l6t6i6o6
Revises: s5p5r5i5n5t5
Create Date: 2026-05-23 06:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "m6u6l6t6i6o6"
down_revision: Union[str, None] = "s5p5r5i5n5t5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "client_organizations",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "client_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("clients.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "organization_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("client_id", "organization_id", name="uq_client_organization"),
    )
    op.create_index(
        "idx_client_organizations_client_id",
        "client_organizations",
        ["client_id"],
    )
    op.create_index(
        "idx_client_organizations_organization_id",
        "client_organizations",
        ["organization_id"],
    )

    # Seed existing clients into client_organizations with their home org
    op.execute(
        """
        INSERT INTO client_organizations (id, client_id, organization_id, joined_at)
        SELECT gen_random_uuid(), id, organization_id, created_at
        FROM clients
        """
    )


def downgrade() -> None:
    op.drop_index("idx_client_organizations_organization_id", table_name="client_organizations")
    op.drop_index("idx_client_organizations_client_id", table_name="client_organizations")
    op.drop_table("client_organizations")
