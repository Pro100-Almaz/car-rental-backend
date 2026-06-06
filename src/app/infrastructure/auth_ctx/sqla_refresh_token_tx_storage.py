from datetime import datetime

from sqlalchemy import and_, select, update
from sqlalchemy.exc import SQLAlchemyError

from app.core.common.entities.types_ import AccessTokenJti, RefreshTokenFamilyId, RefreshTokenId, UserId
from app.infrastructure.auth_ctx.refresh_token import RefreshToken
from app.infrastructure.auth_ctx.types_ import AuthAsyncSession
from app.infrastructure.exceptions import StorageError
from app.infrastructure.persistence_sqla.mappings.refresh_token import refresh_tokens_table


class SqlaRefreshTokenTxStorage:
    def __init__(self, session: AuthAsyncSession) -> None:
        self._session = session

    def add(self, token: RefreshToken) -> None:
        try:
            self._session.add(token)
        except SQLAlchemyError as e:
            raise StorageError from e

    async def get_by_token_hash(self, token_hash: str) -> RefreshToken | None:
        stmt = select(RefreshToken).where(refresh_tokens_table.c.token_hash == token_hash)
        try:
            result = await self._session.execute(stmt)
        except SQLAlchemyError as e:
            raise StorageError from e
        return result.scalar_one_or_none()

    async def get_by_id(self, id_: RefreshTokenId) -> RefreshToken | None:
        try:
            return await self._session.get(RefreshToken, id_)
        except SQLAlchemyError as e:
            raise StorageError from e

    async def revoke_family(self, family_id: RefreshTokenFamilyId, *, now: datetime) -> None:
        stmt = (
            update(refresh_tokens_table)
            .where(refresh_tokens_table.c.family_id == family_id)
            .where(refresh_tokens_table.c.revoked_at.is_(None))
            .values(revoked_at=now)
        )
        try:
            await self._session.execute(stmt)
        except SQLAlchemyError as e:
            raise StorageError from e

    async def revoke_all_for_user(self, user_id: UserId, *, now: datetime) -> None:
        stmt = (
            update(refresh_tokens_table)
            .where(refresh_tokens_table.c.user_id == user_id)
            .where(refresh_tokens_table.c.revoked_at.is_(None))
            .values(revoked_at=now)
        )
        try:
            await self._session.execute(stmt)
        except SQLAlchemyError as e:
            raise StorageError from e

    async def get_active_access_jtis_for_user(self, user_id: UserId) -> list[tuple[AccessTokenJti, datetime]]:
        """Return (jti, expires_at) for all non-revoked refresh tokens of a user.

        Used by logout-all to pre-populate the JTI denylist before revoking.
        """
        stmt = select(
            refresh_tokens_table.c.issued_access_jti,
            refresh_tokens_table.c.expires_at,
        ).where(
            and_(
                refresh_tokens_table.c.user_id == user_id,
                refresh_tokens_table.c.revoked_at.is_(None),
                refresh_tokens_table.c.issued_access_jti.isnot(None),
            )
        )
        try:
            result = await self._session.execute(stmt)
        except SQLAlchemyError as e:
            raise StorageError from e
        return [(AccessTokenJti(row[0]), row[1]) for row in result.fetchall()]
