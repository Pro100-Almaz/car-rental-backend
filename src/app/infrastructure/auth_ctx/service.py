from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime

from app.core.commands.ports.utc_timer import UtcTimer
from app.core.common.entities.types_ import AccessTokenJti, UserId
from app.infrastructure.auth_ctx.audit_log import emit as audit
from app.infrastructure.auth_ctx.bearer_token_reader import BearerTokenReader
from app.infrastructure.auth_ctx.exceptions import AuthenticationError
from app.infrastructure.auth_ctx.jwt_processor import JwtProcessor
from app.infrastructure.auth_ctx.refresh_token import (
    RefreshToken,
    create_access_token_jti,
    create_refresh_token_family_id,
    create_refresh_token_id,
    generate_refresh_token_raw,
    hash_refresh_token,
)
from app.infrastructure.auth_ctx.revoked_access_jti import RevokedAccessJti
from app.infrastructure.auth_ctx.sqla_refresh_token_tx_storage import SqlaRefreshTokenTxStorage
from app.infrastructure.auth_ctx.sqla_revoked_access_jti_tx_storage import SqlaRevokedAccessJtiTxStorage
from app.infrastructure.auth_ctx.sqla_transaction_manager import AuthSqlaTransactionManager
from app.main.config.settings import JwtSettings

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class TokenPair:
    access_token: str
    refresh_token: str
    access_expires_at: datetime
    refresh_expires_at: datetime
    access_jti: AccessTokenJti


class AuthService:
    def __init__(
        self,
        bearer_token_reader: BearerTokenReader,
        jwt_processor: JwtProcessor,
        jwt_settings: JwtSettings,
        utc_timer: UtcTimer,
        refresh_token_tx_storage: SqlaRefreshTokenTxStorage,
        revoked_access_jti_tx_storage: SqlaRevokedAccessJtiTxStorage,
        transaction_manager: AuthSqlaTransactionManager,
    ) -> None:
        self._bearer_token_reader = bearer_token_reader
        self._jwt_processor = jwt_processor
        self._jwt_settings = jwt_settings
        self._utc_timer = utc_timer
        self._refresh_token_tx_storage = refresh_token_tx_storage
        self._revoked_access_jti_tx_storage = revoked_access_jti_tx_storage
        self._transaction_manager = transaction_manager

    async def issue_token_pair(
        self,
        user_id: UserId,
        ip: str | None,
        user_agent: str | None,
    ) -> TokenPair:
        now = self._utc_timer.now.value
        jti = create_access_token_jti()
        access_expires_at = now + self._jwt_settings.access_ttl
        refresh_expires_at = now + self._jwt_settings.refresh_ttl

        raw_refresh = generate_refresh_token_raw()
        token_hash = hash_refresh_token(raw_refresh)

        refresh_token = RefreshToken(
            id_=create_refresh_token_id(),
            user_id=user_id,
            family_id=create_refresh_token_family_id(),
            token_hash=token_hash,
            issued_access_jti=jti,
            expires_at=refresh_expires_at,
            revoked_at=None,
            replaced_by=None,
            created_at=now,
            last_used_at=None,
            ip=ip,
            user_agent=user_agent[:512] if user_agent else None,
        )
        self._refresh_token_tx_storage.add(refresh_token)
        await self._transaction_manager.commit()

        access_token = self._jwt_processor.encode_access(
            user_id=user_id,
            jti=jti,
            issued_at=now,
            expires_at=access_expires_at,
        )

        return TokenPair(
            access_token=access_token,
            refresh_token=raw_refresh,
            access_expires_at=access_expires_at,
            refresh_expires_at=refresh_expires_at,
            access_jti=jti,
        )

    async def rotate_refresh(
        self,
        raw_refresh: str,
        ip: str | None,
        user_agent: str | None,
    ) -> TokenPair:
        token_hash = hash_refresh_token(raw_refresh)
        stored = await self._refresh_token_tx_storage.get_by_token_hash(token_hash)

        if stored is None:
            raise AuthenticationError("Refresh token not found.")

        now = self._utc_timer.now.value

        # Expired (and not yet revoked) — reject without family kill
        if stored.expires_at.replace(tzinfo=UTC) < now:
            raise AuthenticationError("Refresh token expired.")

        # Revoked — replay detected; kill the whole family
        if stored.revoked_at is not None:
            audit(
                "auth.refresh.replay_detected",
                level=logging.WARNING,
                user_id=stored.user_id,
                family_id=stored.family_id,
                ip=ip,
                user_agent=user_agent,
            )
            await self._refresh_token_tx_storage.revoke_family(stored.family_id, now=now)
            await self._transaction_manager.commit()
            raise AuthenticationError("Refresh token replayed — family revoked.")

        # Valid — rotate
        new_jti = create_access_token_jti()
        access_expires_at = now + self._jwt_settings.access_ttl
        refresh_expires_at = now + self._jwt_settings.refresh_ttl

        new_raw = generate_refresh_token_raw()
        new_hash = hash_refresh_token(new_raw)

        new_refresh = RefreshToken(
            id_=create_refresh_token_id(),
            user_id=stored.user_id,
            family_id=stored.family_id,
            token_hash=new_hash,
            issued_access_jti=new_jti,
            expires_at=refresh_expires_at,
            revoked_at=None,
            replaced_by=None,
            created_at=now,
            last_used_at=None,
            ip=ip,
            user_agent=user_agent[:512] if user_agent else None,
        )

        # Insert new refresh first so the FK on replaced_by can resolve
        self._refresh_token_tx_storage.add(new_refresh)
        await self._transaction_manager.flush()

        # Mark old token revoked and link to successor
        stored.revoked_at = now
        stored.replaced_by = new_refresh.id_
        stored.last_used_at = now

        await self._transaction_manager.commit()

        access_token = self._jwt_processor.encode_access(
            user_id=stored.user_id,
            jti=new_jti,
            issued_at=now,
            expires_at=access_expires_at,
        )

        return TokenPair(
            access_token=access_token,
            refresh_token=new_raw,
            access_expires_at=access_expires_at,
            refresh_expires_at=refresh_expires_at,
            access_jti=new_jti,
        )

    async def logout_current(
        self,
        user_id: UserId,
        raw_refresh: str | None,
        current_access_jti: AccessTokenJti | None,
        current_access_exp: datetime | None,
    ) -> None:
        now = self._utc_timer.now.value

        if raw_refresh is not None:
            token_hash = hash_refresh_token(raw_refresh)
            stored = await self._refresh_token_tx_storage.get_by_token_hash(token_hash)
            if stored is not None and stored.revoked_at is None:
                stored.revoked_at = now

        if current_access_jti is not None and current_access_exp is not None:
            jti_record = RevokedAccessJti(
                jti=current_access_jti,
                user_id=user_id,
                expires_at=current_access_exp,
            )
            self._revoked_access_jti_tx_storage.add(jti_record)

        await self._transaction_manager.commit()

    async def revoke_all_for_user(self, user_id: UserId) -> None:
        now = self._utc_timer.now.value
        await self._refresh_token_tx_storage.revoke_all_for_user(user_id, now=now)
        await self._transaction_manager.commit()

    async def revoke_all_and_denylist_for_user(
        self,
        user_id: UserId,
        reason: str = "user_request",
    ) -> None:
        """Revoke all active refresh tokens and denylist their access JTIs.

        Queries non-revoked refresh tokens *before* revoking so that their
        ``issued_access_jti`` values can be inserted into ``revoked_access_jtis``
        to immediately invalidate any outstanding access tokens.
        """
        now = self._utc_timer.now.value

        # Fetch active JTIs before revoking
        active_jtis = await self._refresh_token_tx_storage.get_active_access_jtis_for_user(user_id)

        # Denylist each access JTI
        for jti, expires_at in active_jtis:
            jti_record = RevokedAccessJti(
                jti=jti,
                user_id=user_id,
                expires_at=expires_at,
            )
            self._revoked_access_jti_tx_storage.add(jti_record)

        # Revoke all refresh tokens
        await self._refresh_token_tx_storage.revoke_all_for_user(user_id, now=now)
        await self._transaction_manager.commit()

        audit("auth.logout_all", user_id=user_id, reason=reason)

    async def get_current_user_id(self) -> UserId:
        raw_token = self._bearer_token_reader.read()
        if raw_token is None:
            raise AuthenticationError("No bearer token.")

        claims = self._jwt_processor.decode_access(raw_token)
        if claims is None:
            raise AuthenticationError("Invalid access token.")

        if await self._revoked_access_jti_tx_storage.is_revoked(claims.jti):
            raise AuthenticationError("Access token revoked.")

        return claims.sub
