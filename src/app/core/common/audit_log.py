"""Structured audit log helper for domain events.

Emits structured key=value log lines to the ``audit.app`` logger so that
log-shippers (Loki, ELK, CloudWatch Insights) can parse them without regex.

Usage::

    from app.core.common.audit_log import emit
    emit("rental.booking.approved", rental_id=rental_id, manager_id=manager_id)
"""

import logging

_logger = logging.getLogger("audit.app")


def emit(event: str, level: int = logging.INFO, **fields: object) -> None:
    """Emit a structured audit event.

    Parameters
    ----------
    event:
        Dot-separated event name, e.g. ``rental.booking.approved``.
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
