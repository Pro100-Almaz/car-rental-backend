import math
from datetime import UTC, datetime
from inspect import getdoc

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Request, Response, status
from fastapi_error_map import ErrorAwareRouter
from pydantic import BaseModel, ConfigDict
from slowapi.errors import RateLimitExceeded
from starlette.responses import JSONResponse

from app.core.common.authorization.exceptions import AuthorizationError
from app.core.common.exceptions import BusinessTypeError
from app.infrastructure.adapters.exceptions import PasswordHasherBusyError
from app.infrastructure.auth_ctx.exceptions import (
    AccountLockedError,
    AuthenticationError,
    EmailNotVerifiedError,
)
from app.infrastructure.auth_ctx.handlers.log_in import LogIn, LogInRequest
from app.infrastructure.auth_ctx.service import TokenPair
from app.infrastructure.exceptions import StorageError
from app.infrastructure.rate_limit import limiter
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_429_RATE_LIMITED_RULE, HTTP_503_SERVICE_UNAVAILABLE_RULE


class LogInRequestSchema(BaseModel):
    model_config = ConfigDict(frozen=True)
    email: str
    password: str


class LogInResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    access_token: str
    token_type: str = "Bearer"  # noqa: S105 — OAuth2 scheme name, not a credential
    expires_in: int


def _pair_access_to_response(pair: TokenPair) -> LogInResponse:
    now = datetime.now(tz=UTC)
    expires_in = max(0, math.floor((pair.access_expires_at.replace(tzinfo=UTC) - now).total_seconds()))
    return LogInResponse(access_token=pair.access_token, expires_in=expires_in)


def make_log_in_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.post(
        "/login/",
        error_map={
            StorageError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
            AuthorizationError: status.HTTP_403_FORBIDDEN,
            BusinessTypeError: status.HTTP_400_BAD_REQUEST,
            AuthenticationError: status.HTTP_401_UNAUTHORIZED,
            EmailNotVerifiedError: status.HTTP_403_FORBIDDEN,
            PasswordHasherBusyError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
            RateLimitExceeded: HTTP_429_RATE_LIMITED_RULE,
        },
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
        response_model=LogInResponse,
        description=getdoc(LogIn),
    )
    @limiter.limit("5/minute;30/hour")
    @inject
    async def log_in(
        request_schema: LogInRequestSchema,
        request: Request,
        response: Response,
        handler: FromDishka[LogIn],
    ) -> LogInResponse | JSONResponse:
        ip = request.client.host if request.client else None
        ua = request.headers.get("user-agent")
        try:
            pair = await handler.execute(
                LogInRequest(
                    email=request_schema.email,
                    password=request_schema.password,
                    ip=ip,
                    user_agent=ua,
                )
            )
        except AccountLockedError as exc:
            log_info(exc)
            return JSONResponse(
                status_code=status.HTTP_423_LOCKED,
                content={"error": str(exc)},
                headers={"Retry-After": "900"},
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
