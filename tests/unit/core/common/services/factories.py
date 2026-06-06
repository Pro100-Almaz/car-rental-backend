"""Lightweight test factories shared across unit tests.

Survives the user-management → car-rental rewrite and only exposes helpers
still used by current tests (`test_stubs`, `test_bcrypt_password_hasher`).
"""

import secrets

from app.core.common.value_objects.raw_password import RawPassword


def create_raw_password(value: str | None = None) -> RawPassword:
    """Return a RawPassword. When `value` is omitted, generate a random one
    so callers asking for two passwords get distinct objects."""
    return RawPassword(value if value is not None else secrets.token_urlsafe(12))
