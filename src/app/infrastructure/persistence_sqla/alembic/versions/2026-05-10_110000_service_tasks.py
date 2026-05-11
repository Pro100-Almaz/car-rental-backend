"""service_tasks

Revision ID: 9e8f7a6b5c4d
Revises: 8d7e6f5a4b3c
Create Date: 2026-05-10 11:00:00.000000+00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "9e8f7a6b5c4d"
down_revision: str | None = "8d7e6f5a4b3c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "service_tasks",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("vehicle_id", sa.UUID(), nullable=False),
        sa.Column("rental_id", sa.UUID(), nullable=True),
        sa.Column("assigned_to", sa.UUID(), nullable=True),
        sa.Column("task_type", sa.String(length=50), nullable=False),
        sa.Column("priority", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("estimated_cost", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("actual_cost", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("proof_photos", sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["vehicle_id"], ["vehicles.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["rental_id"], ["rentals.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["assigned_to"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("idx_service_tasks_vehicle_status", "service_tasks", ["vehicle_id", "status"])
    op.create_index("idx_service_tasks_assigned_status", "service_tasks", ["assigned_to", "status"])
    op.create_index("idx_service_tasks_org_status", "service_tasks", ["organization_id", "status"])


def downgrade() -> None:
    op.drop_index("idx_service_tasks_org_status", table_name="service_tasks")
    op.drop_index("idx_service_tasks_assigned_status", table_name="service_tasks")
    op.drop_index("idx_service_tasks_vehicle_status", table_name="service_tasks")
    op.drop_table("service_tasks")
