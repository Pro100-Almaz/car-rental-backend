import math
from datetime import UTC, datetime

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Request, Response, status
from fastapi_error_map import ErrorAwareRouter
from slowapi.errors import RateLimitExceeded

from app.infrastructure.auth_ctx.exceptions import AuthenticationError
from app.infrastructure.auth_ctx.handlers.refresh import RefreshTokenHandler, RefreshTokenInput
from app.infrastructure.exceptions import StorageError
from app.infrastructure.rate_limit import limiter
from app.presentation.http.account.log_in import LogInResponse, _pair_access_to_response
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_429_RATE_LIMITED_RULE, HTTP_503_SERVICE_UNAVAILABLE_RULE


def make_refresh_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.post(
        "/refresh/",
        error_map={
            AuthenticationError: status.HTTP_401_UNAUTHORIZED,
            StorageError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
            RateLimitExceeded: HTTP_429_RATE_LIMITED_RULE,
        },
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
        description="Exchange a valid refresh token for a new token pair.",
    )
    @limiter.limit("30/minute")
    @inject
    async def refresh_token(
        request: Request,
        response: Response,
        handler: FromDishka[RefreshTokenHandler],
    ) -> LogInResponse:
        ip = request.client.host if request.client else None
        ua = request.headers.get("user-agent")
        refresh_token = request.cookies.get("refresh_token")

        if refresh_token is None:
            raise AuthenticationError("No refresh token.")

        pair = await handler.execute(
            RefreshTokenInput(
                refresh_token=refresh_token,
                ip=ip,
                user_agent=ua,
            )
        )

        refresh_max_age = max(
            0, math.floor((pair.refresh_expires_at.replace(tzinfo=UTC) - datetime.now(tz=UTC)).total_seconds())
        )

        response.set_cookie(
            key="refresh_token",
            value=pair.refresh_token,
            httponly=True,
            secure=False,
            samesite="lax",
            max_age=refresh_max_age,
            path="/",
        )
        return _pair_access_to_response(pair)

    return router
