"""mobile sprint 4 — extension_requests table

Revision ID: s4p4r4i4n4t4
Revises: s3p3r3i3n3t3
Create Date: 2026-05-23 04:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "s4p4r4i4n4t4"
down_revision = "s3p3r3i3n3t3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "extension_requests",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "rental_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("rentals.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "client_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("clients.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("new_end_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("additional_cost", sa.Numeric(12, 2), nullable=False),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("rejection_reason", sa.String(2000), nullable=True),
        sa.Column(
            "reviewed_by",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "idx_extension_requests_rental_status",
        "extension_requests",
        ["rental_id", "status"],
    )
    op.create_index(
        "idx_extension_requests_org_status",
        "extension_requests",
        ["organization_id", "status"],
    )


def downgrade() -> None:
    op.drop_index("idx_extension_requests_org_status", table_name="extension_requests")
    op.drop_index("idx_extension_requests_rental_status", table_name="extension_requests")
    op.drop_table("extension_requests")
