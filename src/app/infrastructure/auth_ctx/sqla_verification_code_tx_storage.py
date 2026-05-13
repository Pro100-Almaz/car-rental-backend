from uuid import UUID

from sqlalchemy import delete
from sqlalchemy.exc import SQLAlchemyError

from app.infrastructure.auth_ctx.types_ import AuthAsyncSession
from app.infrastructure.auth_ctx.verification_code import EmailVerificationCode
from app.infrastructure.exceptions import StorageError
from app.infrastructure.persistence_sqla.mappings.email_verification_code import (
    email_verification_codes_table,
)


class EmailVerificationCodeSqlaTxStorage:
    def __init__(self, session: AuthAsyncSession) -> None:
        self._session = session

    def add(self, code: EmailVerificationCode) -> None:
        try:
            self._session.add(code)
        except SQLAlchemyError as e:
            raise StorageError from e

    async def get_latest_for_user(self, user_id: UUID) -> EmailVerificationCode | None:
        from sqlalchemy import select

        stmt = (
            select(EmailVerificationCode)
            .where(email_verification_codes_table.c.user_id == user_id)
            .order_by(email_verification_codes_table.c.created_at.desc())
            .limit(1)
        )
        try:
            result = await self._session.execute(stmt)
        except SQLAlchemyError as e:
            raise StorageError from e
        return result.scalar_one_or_none()

    async def delete_all_for_user(self, user_id: UUID) -> None:
        stmt = delete(email_verification_codes_table).where(
            email_verification_codes_table.c.user_id == user_id,
        )
        try:
            await self._session.execute(stmt)
        except SQLAlchemyError as e:
            raise StorageError from e
