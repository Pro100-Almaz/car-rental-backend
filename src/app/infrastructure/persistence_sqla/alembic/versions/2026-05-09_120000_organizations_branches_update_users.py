"""add organizations, branches, update users schema

Revision ID: a1b2c3d4e5f6
Revises: c025baa8044e
Create Date: 2026-05-09 12:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "c025baa8044e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "organizations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=63), nullable=False),
        sa.Column("settings", sa.JSON(), nullable=True),
        sa.Column("subscription_plan", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_organizations")),
        sa.UniqueConstraint("slug", name=op.f("uq_organizations_slug")),
    )

    op.create_table(
        "branches",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("address", sa.String(length=500), nullable=False),
        sa.Column("latitude", sa.Numeric(precision=10, scale=7), nullable=True),
        sa.Column("longitude", sa.Numeric(precision=10, scale=7), nullable=True),
        sa.Column("timezone", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_branches_organization_id_organizations"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_branches")),
    )

    op.drop_constraint(op.f("uq_users_username"), "users", type_="unique")
    op.drop_column("users", "username")

    op.add_column("users", sa.Column("organization_id", sa.UUID(), nullable=True))
    op.add_column("users", sa.Column("email", sa.String(length=254), nullable=True))
    op.add_column("users", sa.Column("phone", sa.String(length=20), nullable=True))
    op.add_column("users", sa.Column("first_name", sa.String(length=100), nullable=True))
    op.add_column("users", sa.Column("last_name", sa.String(length=100), nullable=True))
    op.add_column("users", sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("users", sa.Column("branch_id", sa.UUID(), nullable=True))

    op.execute("UPDATE users SET first_name = 'Unknown', last_name = 'Unknown' WHERE first_name IS NULL")

    op.alter_column("users", "first_name", nullable=False)
    op.alter_column("users", "last_name", nullable=False)

    op.alter_column("users", "role", type_=sa.String(20), existing_nullable=False)

    op.execute("UPDATE users SET role = 'branch_manager' WHERE role = 'admin'")
    op.execute("UPDATE users SET role = 'dispatcher' WHERE role = 'user'")

    op.create_unique_constraint(op.f("uq_users_email"), "users", ["email"])

    op.create_foreign_key(
        op.f("fk_users_organization_id_organizations"),
        "users",
        "organizations",
        ["organization_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        op.f("fk_users_branch_id_branches"),
        "users",
        "branches",
        ["branch_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(op.f("fk_users_branch_id_branches"), "users", type_="foreignkey")
    op.drop_constraint(op.f("fk_users_organization_id_organizations"), "users", type_="foreignkey")
    op.drop_constraint(op.f("uq_users_email"), "users", type_="unique")

    op.drop_column("users", "branch_id")
    op.drop_column("users", "last_login_at")
    op.drop_column("users", "last_name")
    op.drop_column("users", "first_name")
    op.drop_column("users", "phone")
    op.drop_column("users", "email")
    op.drop_column("users", "organization_id")

    op.add_column("users", sa.Column("username", sa.String(length=20), nullable=True))
    op.create_unique_constraint(op.f("uq_users_username"), "users", ["username"])

    op.execute("UPDATE users SET role = 'admin' WHERE role = 'branch_manager'")
    op.execute("UPDATE users SET role = 'user' WHERE role IN ('dispatcher', 'finance', 'field_staff')")

    op.drop_table("branches")
    op.drop_table("organizations")
