"""Refresh-token domain model + factory.

Refresh tokens are opaque random strings issued at login, stored hashed in the DB, and
rotated single-use on every `/account/refresh/` call. See `spec/AUTH_JWT_BACKEND.md`.
"""

from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4

from app.core.common.entities.types_ import (
    AccessTokenJti,
    RefreshTokenFamilyId,
    RefreshTokenId,
    UserId,
)

RAW_TOKEN_BYTES = 32  # 256 bits


def generate_refresh_token_raw() -> str:
    return secrets.token_urlsafe(RAW_TOKEN_BYTES)


def hash_refresh_token(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


@dataclass(eq=False, kw_only=True)
class RefreshToken:
    id_: RefreshTokenId
    user_id: UserId
    family_id: RefreshTokenFamilyId
    token_hash: str
    issued_access_jti: AccessTokenJti | None
    expires_at: datetime
    revoked_at: datetime | None
    replaced_by: RefreshTokenId | None
    created_at: datetime
    last_used_at: datetime | None
    ip: str | None
    user_agent: str | None


def create_refresh_token_id() -> RefreshTokenId:
    return RefreshTokenId(uuid4())


def create_refresh_token_family_id() -> RefreshTokenFamilyId:
    return RefreshTokenFamilyId(uuid4())


def create_access_token_jti() -> AccessTokenJti:
    return AccessTokenJti(uuid4())


__all__ = [
    "RAW_TOKEN_BYTES",
    "RefreshToken",
    "create_access_token_jti",
    "create_refresh_token_family_id",
    "create_refresh_token_id",
    "generate_refresh_token_raw",
    "hash_refresh_token",
]


# Silence unused-uuid import linter (UUID re-export for typing in adapters)
_ = UUID
