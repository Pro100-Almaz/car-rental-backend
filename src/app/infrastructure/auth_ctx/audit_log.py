"""Structured audit log helper for the auth context.

All auth security events are emitted to the ``audit.auth`` logger using a
structured key=value format so that log-shippers (Loki, ELK, CloudWatch
Insights) can parse them without regex gymnastics.

Usage::

    from app.infrastructure.auth_ctx.audit_log import emit
    emit("auth.login.success", user_id=user_id, ip=ip, user_agent=ua)
"""

import logging

_logger = logging.getLogger("audit.auth")


def emit(event: str, level: int = logging.INFO, **fields: object) -> None:
    """Emit a structured audit event.

    Parameters
    ----------
    event:
        Dot-separated event name, e.g. ``auth.login.success``.
    level:
        Python logging level (default: INFO).
    **fields:
        Arbitrary key=value pairs appended after the event name.
    """
    _logger.log(
        level,
        "%s %s",
        event,
        " ".join(f"{k}={v}" for k, v in fields.items()),
    )
