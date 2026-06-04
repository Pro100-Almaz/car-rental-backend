"""Update user roles to match ТЗ spec: 6 roles replacing old 7.

Revision ID: k1l2m3n4o5p6
Revises: j0k1l2m3n4o5
Create Date: 2026-05-13 13:00:00.000000
"""

from alembic import op

revision = "k1l2m3n4o5p6"
down_revision = "j0k1l2m3n4o5"
branch_labels = None
depends_on = None

ROLE_MAPPING_UP = {
    "owner": "admin",
    "branch_manager": "booking_manager",
    "dispatcher": "booking_manager",
    "finance": "financial_manager",
    "field_staff": "technician",
    "client": "investor",
}

ROLE_MAPPING_DOWN = {
    "admin": "owner",
    "booking_manager": "branch_manager",
    "financial_manager": "finance",
    "investor": "client",
    "technician": "field_staff",
}


def upgrade() -> None:
    for old_role, new_role in ROLE_MAPPING_UP.items():
        op.execute(
            f"UPDATE users SET role = '{new_role}' WHERE role = '{old_role}'"
        )


def downgrade() -> None:
    for new_role, old_role in ROLE_MAPPING_DOWN.items():
        op.execute(
            f"UPDATE users SET role = '{old_role}' WHERE role = '{new_role}'"
        )
