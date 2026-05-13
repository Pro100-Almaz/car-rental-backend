from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.infrastructure.auth_ctx.invite import Invite
from app.infrastructure.auth_ctx.types_ import AuthAsyncSession
from app.infrastructure.exceptions import StorageError
from app.infrastructure.persistence_sqla.mappings.invite import invites_table


class InviteSqlaTxStorage:
    def __init__(self, session: AuthAsyncSession) -> None:
        self._session = session

    def add(self, invite: Invite) -> None:
        try:
            self._session.add(invite)
        except SQLAlchemyError as e:
            raise StorageError from e

    async def get_by_token(self, token: str) -> Invite | None:
        stmt = select(Invite).where(invites_table.c.token == token)
        try:
            result = await self._session.execute(stmt)
        except SQLAlchemyError as e:
            raise StorageError from e
        return result.scalar_one_or_none()
