from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.common.entities.user import User
from app.core.common.value_objects.email import Email
from app.infrastructure.exceptions import StorageError
from app.infrastructure.persistence_sqla.mappings.user import users_table


class AuthSqlaUserTxStorage:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def add(self, user: User) -> None:
        try:
            self._session.add(user)
        except SQLAlchemyError as e:
            raise StorageError from e

    async def get_by_email(
        self,
        email: Email,
        *,
        for_update: bool = False,
    ) -> User | None:
        stmt = select(User).where(users_table.c.email == email.value)
        if for_update:
            stmt = stmt.with_for_update()
        try:
            result = await self._session.execute(stmt)
        except SQLAlchemyError as e:
            raise StorageError from e
        return result.scalar_one_or_none()
