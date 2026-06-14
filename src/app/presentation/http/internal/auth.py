"""Shared-secret authorization dependency for internal job endpoints."""

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import Header, HTTPException, status

from app.infrastructure.job_types import JobRunnerSecret

_UNAUTHORIZED = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid or missing job token.",
)


@inject
async def require_internal_token(
    x_internal_job_token: str | None = Header(default=None),
    secret: FromDishka[JobRunnerSecret] = ...,  # type: ignore[assignment]
) -> None:
    """Raise 401 if the shared-secret header is missing or does not match."""
    if x_internal_job_token is None or x_internal_job_token != secret:
        raise _UNAUTHORIZED
