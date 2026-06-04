"""mobile sprint 5 — notification preferences + performance indexes

Revision ID: s5p5r5i5n5t5
Revises: s4p4r4i4n4t4
Create Date: 2026-05-23 05:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "s5p5r5i5n5t5"
down_revision = "s4p4r4i4n4t4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # notification_preferences on users
    op.add_column(
        "users",
        sa.Column(
            "notification_preferences",
            JSONB,
            nullable=True,
            server_default="{}",
        ),
    )

    # rentals indexes for mobile queries and scheduler jobs
    op.create_index(
        "idx_rentals_client_status",
        "rentals",
        ["client_id", "status"],
    )
    op.create_index(
        "idx_rentals_vehicle_dates",
        "rentals",
        ["vehicle_id", "scheduled_start", "scheduled_end"],
    )
    op.create_index(
        "idx_rentals_status_scheduled_start",
        "rentals",
        ["status", "scheduled_start"],
    )
    op.create_index(
        "idx_rentals_status_scheduled_end",
        "rentals",
        ["status", "scheduled_end"],
    )

    # notifications indexes
    op.create_index(
        "idx_notifications_user_created",
        "notifications",
        ["user_id", "created_at"],
    )

    # device_tokens index
    op.create_index(
        "idx_device_tokens_user_id",
        "device_tokens",
        ["user_id"],
    )

    # transactions indexes for mobile queries
    op.create_index(
        "idx_transactions_client_created",
        "transactions",
        ["client_id", "created_at"],
    )
    op.create_index(
        "idx_transactions_status_source",
        "transactions",
        ["status", "source"],
    )


def downgrade() -> None:
    op.drop_index("idx_transactions_status_source", table_name="transactions")
    op.drop_index("idx_transactions_client_created", table_name="transactions")
    op.drop_index("idx_device_tokens_user_id", table_name="device_tokens")
    op.drop_index("idx_notifications_user_created", table_name="notifications")
    op.drop_index("idx_rentals_status_scheduled_end", table_name="rentals")
    op.drop_index("idx_rentals_status_scheduled_start", table_name="rentals")
    op.drop_index("idx_rentals_vehicle_dates", table_name="rentals")
    op.drop_index("idx_rentals_client_status", table_name="rentals")
    op.drop_column("users", "notification_preferences")
