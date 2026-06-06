from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.core.common.entities.types_ import AccessTokenJti
from app.infrastructure.auth_ctx.revoked_access_jti import RevokedAccessJti
from app.infrastructure.auth_ctx.types_ import AuthAsyncSession
from app.infrastructure.exceptions import StorageError
from app.infrastructure.persistence_sqla.mappings.revoked_access_jti import revoked_access_jtis_table


class SqlaRevokedAccessJtiTxStorage:
    def __init__(self, session: AuthAsyncSession) -> None:
        self._session = session

    def add(self, jti_record: RevokedAccessJti) -> None:
        try:
            self._session.add(jti_record)
        except SQLAlchemyError as e:
            raise StorageError from e

    async def is_revoked(self, jti: AccessTokenJti) -> bool:
        stmt = select(revoked_access_jtis_table.c.jti).where(revoked_access_jtis_table.c.jti == jti)
        try:
            result = await self._session.execute(stmt)
        except SQLAlchemyError as e:
            raise StorageError from e
        return result.scalar_one_or_none() is not None
