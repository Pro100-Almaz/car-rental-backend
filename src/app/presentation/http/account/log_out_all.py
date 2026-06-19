"""POST /account/logout-all/ — revoke every active session for the caller."""

from inspect import getdoc

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Request, Response, status
from fastapi_error_map import ErrorAwareRouter
from slowapi.errors import RateLimitExceeded

from app.infrastructure.auth_ctx.exceptions import AuthenticationError
from app.infrastructure.auth_ctx.handlers.log_out_all import LogOutAll
from app.infrastructure.exceptions import StorageError
from app.infrastructure.rate_limit import get_user_id_or_ip, limiter
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_429_RATE_LIMITED_RULE, HTTP_503_SERVICE_UNAVAILABLE_RULE


def make_log_out_all_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.post(
        "/logout-all/",
        error_map={
            AuthenticationError: status.HTTP_401_UNAUTHORIZED,
            StorageError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
            RateLimitExceeded: HTTP_429_RATE_LIMITED_RULE,
        },
        default_on_error=log_info,
        status_code=status.HTTP_204_NO_CONTENT,
        description=getdoc(LogOutAll),
    )
    @limiter.limit("10/minute", key_func=get_user_id_or_ip)
    @inject
    async def log_out_all(
        request: Request,
        response: Response,
        handler: FromDishka[LogOutAll],
    ) -> None:
        auth = request.headers.get("authorization", "")
        raw_token: str | None = None
        if auth.lower().startswith("bearer "):
            raw_token = auth.split(None, 1)[1].strip() or None
        if raw_token is None:
            raise AuthenticationError("No bearer token.")
        await handler.execute(raw_token, reason="user_request")

        response.delete_cookie(key="refresh_token", path="/")

    return router
