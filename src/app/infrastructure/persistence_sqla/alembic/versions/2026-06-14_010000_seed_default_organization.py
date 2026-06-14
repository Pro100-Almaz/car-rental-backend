"""Seed the default signup organization.

The signup handler reads `APP_DEFAULT_ORGANIZATION_ID` from settings and
inserts every uninvited new client into that organization. Without a matching
row in `organizations`, signup fails at the FK on `clients.organization_id`
with a generic 503. This migration ensures the row exists so a fresh stack
can accept signups immediately after `make migrate`, with no extra steps.

The UUID is hardcoded (immutability matters for migrations). The env var
`APP_DEFAULT_ORGANIZATION_ID` must match this value; a startup-time check
to assert that is a separate, optional follow-up.

Idempotent: re-running is a no-op via ON CONFLICT DO NOTHING.

Revision ID: d3f4u170r6r1
Revises: r3j3c7i0n001
Create Date: 2026-06-14
"""

from collections.abc import Sequence
from uuid import UUID

import sqlalchemy as sa
from alembic import op

revision: str = "d3f4u170r6r1"
down_revision: str | None = "r3j3c7i0n001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

DEFAULT_ORGANIZATION_ID: UUID = UUID("019e549b-5ab4-71d1-9290-17de7937b9e3")
DEFAULT_ORGANIZATION_NAME: str = "Default"
DEFAULT_ORGANIZATION_SLUG: str = "default"
DEFAULT_ORGANIZATION_SUBSCRIPTION_PLAN: str = "free"


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            INSERT INTO organizations (
                id, name, slug, settings, subscription_plan, created_at, updated_at
            ) VALUES (
                :id, :name, :slug, NULL, :plan, NOW(), NOW()
            )
            ON CONFLICT (id) DO NOTHING
            """
        ).bindparams(
            sa.bindparam("id", value=DEFAULT_ORGANIZATION_ID, type_=sa.UUID(as_uuid=True)),
            sa.bindparam("name", value=DEFAULT_ORGANIZATION_NAME),
            sa.bindparam("slug", value=DEFAULT_ORGANIZATION_SLUG),
            sa.bindparam("plan", value=DEFAULT_ORGANIZATION_SUBSCRIPTION_PLAN),
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text("DELETE FROM organizations WHERE id = :id").bindparams(
            sa.bindparam("id", value=DEFAULT_ORGANIZATION_ID, type_=sa.UUID(as_uuid=True)),
        )
    )
