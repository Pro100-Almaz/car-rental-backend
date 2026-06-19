from inspect import getdoc

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Request, Response, status
from fastapi_error_map import ErrorAwareRouter
from slowapi.errors import RateLimitExceeded

from app.infrastructure.auth_ctx.exceptions import AuthenticationError
from app.infrastructure.auth_ctx.handlers.log_out import LogOut
from app.infrastructure.exceptions import StorageError
from app.infrastructure.rate_limit import get_user_id_or_ip, limiter
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_429_RATE_LIMITED_RULE, HTTP_503_SERVICE_UNAVAILABLE_RULE


def make_log_out_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.post(
        "/logout/",
        error_map={
            AuthenticationError: status.HTTP_401_UNAUTHORIZED,
            StorageError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
            RateLimitExceeded: HTTP_429_RATE_LIMITED_RULE,
        },
        default_on_error=log_info,
        status_code=status.HTTP_204_NO_CONTENT,
        description=getdoc(LogOut),
    )
    @limiter.limit("30/minute", key_func=get_user_id_or_ip)
    @inject
    async def log_out(request: Request, handler: FromDishka[LogOut], response: Response) -> None:
        refresh_token = request.cookies.get("refresh_token")
        await handler.execute(refresh_token)

        response.delete_cookie(key="refresh_token", path="/")

    return router
