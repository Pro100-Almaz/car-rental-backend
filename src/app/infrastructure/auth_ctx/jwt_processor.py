"""JWT encoder/decoder for access tokens.

Refresh tokens are NOT JWTs — they are opaque random strings (see `refresh_token.py`).
Only access tokens flow through this module.

Claims:
    sub  — user id (UUID string)
    typ  — "access" (discriminates from refresh; future-proofs token-type validation)
    jti  — access-token UUID (denylist target on logout)
    iat  — issued-at, unix seconds
    exp  — expiry, unix seconds
    iss  — issuer string
    aud  — audience string
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, ClassVar
from uuid import UUID

import jwt

from app.core.common.entities.types_ import AccessTokenJti, UserId
from app.infrastructure.auth_ctx.jwt_types import JwtAlgorithm

ACCESS_TYP = "access"


@dataclass(frozen=True, slots=True)
class AccessClaims:
    sub: UserId
    jti: AccessTokenJti
    exp: datetime
    iat: datetime


class JwtProcessor:
    SUB_CLAIM: ClassVar[str] = "sub"
    TYP_CLAIM: ClassVar[str] = "typ"
    JTI_CLAIM: ClassVar[str] = "jti"
    IAT_CLAIM: ClassVar[str] = "iat"
    EXP_CLAIM: ClassVar[str] = "exp"
    ISS_CLAIM: ClassVar[str] = "iss"
    AUD_CLAIM: ClassVar[str] = "aud"

    def __init__(
        self,
        *,
        secret: str,
        algorithm: JwtAlgorithm,
        issuer: str,
        audience: str,
    ) -> None:
        self._secret = secret
        self._algorithm = algorithm
        self._issuer = issuer
        self._audience = audience

    def encode_access(
        self,
        *,
        user_id: UserId,
        jti: AccessTokenJti,
        issued_at: datetime,
        expires_at: datetime,
    ) -> str:
        payload: dict[str, Any] = {
            self.SUB_CLAIM: str(user_id),
            self.TYP_CLAIM: ACCESS_TYP,
            self.JTI_CLAIM: str(jti),
            self.IAT_CLAIM: int(issued_at.timestamp()),
            self.EXP_CLAIM: int(expires_at.timestamp()),
            self.ISS_CLAIM: self._issuer,
            self.AUD_CLAIM: self._audience,
        }
        return jwt.encode(payload, key=self._secret, algorithm=self._algorithm)

    def decode_access(self, token: str) -> AccessClaims | None:
        try:
            payload = jwt.decode(
                token,
                key=self._secret,
                algorithms=[self._algorithm],
                issuer=self._issuer,
                audience=self._audience,
                options={"require": ["sub", "typ", "jti", "exp", "iss", "aud"]},
            )
        except jwt.PyJWTError:
            return None

        if payload.get(self.TYP_CLAIM) != ACCESS_TYP:
            return None
        sub_raw = payload.get(self.SUB_CLAIM)
        jti_raw = payload.get(self.JTI_CLAIM)
        exp_raw = payload.get(self.EXP_CLAIM)
        iat_raw = payload.get(self.IAT_CLAIM)
        if not isinstance(sub_raw, str) or not isinstance(jti_raw, str):
            return None
        try:
            sub_uuid = UUID(sub_raw)
            jti_uuid = UUID(jti_raw)
        except (TypeError, ValueError):
            return None
        if not isinstance(exp_raw, (int, float)) or not isinstance(iat_raw, (int, float)):
            return None
        return AccessClaims(
            sub=UserId(sub_uuid),
            jti=AccessTokenJti(jti_uuid),
            exp=datetime.fromtimestamp(exp_raw, tz=UTC),
            iat=datetime.fromtimestamp(iat_raw, tz=UTC),
        )
