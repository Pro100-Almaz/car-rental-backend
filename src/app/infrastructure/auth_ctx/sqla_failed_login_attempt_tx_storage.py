from datetime import datetime

from sqlalchemy import delete, func, select
from sqlalchemy.exc import SQLAlchemyError

from app.infrastructure.auth_ctx.failed_login_attempt import FailedLoginAttempt
from app.infrastructure.auth_ctx.types_ import AuthAsyncSession
from app.infrastructure.exceptions import StorageError
from app.infrastructure.persistence_sqla.mappings.failed_login_attempt import failed_login_attempts_table


class SqlaFailedLoginAttemptTxStorage:
    def __init__(self, session: AuthAsyncSession) -> None:
        self._session = session

    def add(self, record: FailedLoginAttempt) -> None:
        try:
            self._session.add(record)
        except SQLAlchemyError as e:
            raise StorageError from e

    async def count_for_email_within(self, email_lower: str, since: datetime) -> int:
        stmt = (
            select(func.count())
            .select_from(failed_login_attempts_table)
            .where(failed_login_attempts_table.c.email_lower == email_lower)
            .where(failed_login_attempts_table.c.attempted_at >= since)
        )
        try:
            result = await self._session.execute(stmt)
        except SQLAlchemyError as e:
            raise StorageError from e
        return result.scalar_one()

    async def count_for_ip_within(self, ip: str, since: datetime) -> int:
        """Count failed attempts from an IP across *any* email in the window."""
        stmt = (
            select(func.count())
            .select_from(failed_login_attempts_table)
            .where(failed_login_attempts_table.c.ip == ip)
            .where(failed_login_attempts_table.c.attempted_at >= since)
        )
        try:
            result = await self._session.execute(stmt)
        except SQLAlchemyError as e:
            raise StorageError from e
        return result.scalar_one()

    async def delete_for_email(self, email_lower: str) -> None:
        """Remove all failed-attempt records for an email after a successful login."""
        stmt = delete(failed_login_attempts_table).where(failed_login_attempts_table.c.email_lower == email_lower)
        try:
            await self._session.execute(stmt)
        except SQLAlchemyError as e:
            raise StorageError from e
