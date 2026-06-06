"""Rate-limiter factory and FastAPI wiring helpers.

Uses slowapi (a Starlette/FastAPI wrapper around limits) backed by Redis so
that limits are shared across all Uvicorn workers.

Key design decisions
--------------------
- A single module-level :class:`slowapi.Limiter` instance is used for both
  the ``@limiter.limit()`` decorators (applied at import time) and the
  ``app.state.limiter`` (used by SlowAPIMiddleware at request time).
- The default ``key_func`` returns the client IP address.  Per-endpoint
  overrides pass a custom callable to ``@limiter.limit()``.
- ``configure_limiter`` reconfigures the module-level instance's storage to
  the Redis backend at app startup, so the decorators and the middleware share
  the same ``Limiter`` object and its ``_route_limits`` registry.
- Email-based throttling for login / forgot-password is NOT wired via
  slowapi key_func (reading async request body from a sync callable is
  fragile).  Instead those handlers implement their own per-email gate via the
  ``failed_login_attempts`` DB table (see lockout logic in LogIn handler).
"""

import base64
import json
import logging

from limits.storage import storage_from_string
from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request

logger = logging.getLogger(__name__)

_BASE64_PAD_BLOCK = 4

# Module-level singleton — imported by route modules for @limiter.limit() decorators.
# Starts with in-memory storage; reconfigured with Redis via make_limiter().
limiter: Limiter = Limiter(
    key_func=get_remote_address,
    in_memory_fallback_enabled=True,
)


def make_limiter(redis_url: str) -> Limiter:
    """Reconfigure the module-level limiter to use Redis storage and return it.

    Mutates the existing instance so that ``@limiter.limit()`` route decorators
    (applied at import time) and ``app.state.limiter`` (set by
    ``setup_rate_limiter``) share the same object and its ``_route_limits``
    registry.
    """
    try:
        new_storage = storage_from_string(redis_url)
        limiter._storage = new_storage  # noqa: SLF001 — slowapi exposes no public storage setter
        limiter._storage_uri = redis_url  # noqa: SLF001
        limiter._storage_dead = False  # noqa: SLF001
        logger.info("Rate limiter reconfigured with storage_uri=%s", redis_url)
    except Exception:
        logger.exception("Failed to configure Redis storage for rate limiter; falling back to in-memory storage.")
    return limiter


def get_user_id_or_ip(request: Request) -> str:
    """Key function: use bearer user_id if present, fall back to IP."""
    auth = request.headers.get("authorization", "")
    if auth.lower().startswith("bearer "):
        token = auth.split(None, 1)[1].strip()
        # Decode without verifying signature — we only need the sub claim for bucketing;
        # actual token validation happens in the handler.
        try:
            payload_part = token.split(".")[1]
            padding = _BASE64_PAD_BLOCK - len(payload_part) % _BASE64_PAD_BLOCK
            if padding != _BASE64_PAD_BLOCK:
                payload_part += "=" * padding
            payload = json.loads(base64.urlsafe_b64decode(payload_part))
            sub = payload.get("sub")
            if sub:
                return f"user:{sub}"
        except (IndexError, ValueError, json.JSONDecodeError):
            logger.debug("rate_limit key decode failed; falling back to IP", exc_info=True)
    return get_remote_address(request)
