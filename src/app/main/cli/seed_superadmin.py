"""
Idempotent CLI command to seed the super_admin user and platform organization.

Usage:
    python -m app.main.cli.seed_superadmin

Environment variables required:
    PASSWORD_PEPPER — bcrypt pepper (same as app uses)
    POSTGRES_DB, POSTGRES_HOST, POSTGRES_PORT, POSTGRES_USER, POSTGRES_PASSWORD
"""

import asyncio
import logging
import sys
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.core.common.entities.types_ import UserRole
from app.core.common.value_objects.raw_password import RawPassword
from app.infrastructure.adapters.bcrypt_password_hasher import (
    BcryptPasswordHasher,
    HasherSemaphore,
    HasherThreadPoolExecutor,
)
from app.infrastructure.persistence_sqla.mappings.all import map_tables
from app.infrastructure.persistence_sqla.mappings.organization import organizations_table
from app.infrastructure.persistence_sqla.mappings.user import users_table
from app.main.config.loader import load_password_hasher_settings, load_postgres_settings

logger = logging.getLogger(__name__)

PLATFORM_ORG_ID = UUID("00000000-0000-0000-0000-000000000001")
SUPER_ADMIN_ID = UUID("00000000-0000-0000-0000-000000000002")
SUPER_ADMIN_EMAIL = "admin@platform.local"
SUPER_ADMIN_PASSWORD = "ChangeMe123!"


async def seed_superadmin() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    postgres = load_postgres_settings()
    password_settings = load_password_hasher_settings()

    engine = create_async_engine(url=postgres.dsn)
    map_tables()

    async with engine.begin() as conn:
        async with AsyncSession(bind=conn) as session:
            existing_org = await session.execute(
                select(organizations_table.c.id).where(
                    organizations_table.c.id == PLATFORM_ORG_ID,
                )
            )
            if existing_org.scalar_one_or_none() is not None:
                logger.info("Platform organization already exists — skipping org creation.")
            else:
                now = datetime.now(UTC)
                await session.execute(
                    organizations_table.insert().values(
                        id=PLATFORM_ORG_ID,
                        name="Platform",
                        slug="platform",
                        settings=None,
                        subscription_plan="platform",
                        created_at=now,
                        updated_at=now,
                    )
                )
                logger.info("Platform organization created.")

            existing_user = await session.execute(
                select(users_table.c.id).where(
                    users_table.c.id == SUPER_ADMIN_ID,
                )
            )
            if existing_user.scalar_one_or_none() is not None:
                logger.info("Super admin user already exists — skipping user creation.")
            else:
                hasher = BcryptPasswordHasher(
                    pepper=password_settings.PEPPER.encode(),
                    work_factor=password_settings.WORK_FACTOR,
                    executor=HasherThreadPoolExecutor(None),  # type: ignore[arg-type]
                    semaphore=HasherSemaphore(asyncio.Semaphore(1)),
                    semaphore_wait_timeout_s=10.0,
                )
                password_hash = hasher.hash_sync(RawPassword(SUPER_ADMIN_PASSWORD))

                now = datetime.now(UTC)
                await session.execute(
                    users_table.insert().values(
                        id=SUPER_ADMIN_ID,
                        organization_id=PLATFORM_ORG_ID,
                        email=SUPER_ADMIN_EMAIL,
                        phone=None,
                        password_hash=password_hash,
                        role=UserRole.SUPER_ADMIN.value,
                        first_name="Super",
                        last_name="Admin",
                        is_active=True,
                        email_verified=True,
                        last_login_at=None,
                        branch_id=None,
                        created_at=now,
                        updated_at=now,
                    )
                )
                logger.info("Super admin user created (email: %s).", SUPER_ADMIN_EMAIL)

        await conn.commit()

    await engine.dispose()
    logger.info("Seed complete.")


def main() -> None:
    asyncio.run(seed_superadmin())


if __name__ == "__main__":
    main()
