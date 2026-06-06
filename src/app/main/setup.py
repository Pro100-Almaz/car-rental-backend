import logging

from fastapi import FastAPI, Request
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from app.infrastructure.auth_ctx.audit_log import emit as audit
from app.main.config.logging_ import DATEFMT, FMT, LoggingLevel
from app.main.config.settings import CorsSettings

logger = logging.getLogger(__name__)


def setup_logging(*, level: LoggingLevel = LoggingLevel.INFO) -> None:
    logging.basicConfig(
        level=level,
        datefmt=DATEFMT,
        format=FMT,
        force=True,
    )
    logger.info("Logging is set up")


def setup_middlewares(app: FastAPI, cors_settings: CorsSettings) -> None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_settings.ALLOWED_ORIGINS,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    logger.info("Middlewares are set up")


def setup_rate_limiter(app: FastAPI, limiter: Limiter) -> None:
    """Attach the slowapi limiter to the app and register the 429 handler."""
    app.state.limiter = limiter
    app.add_middleware(SlowAPIMiddleware)

    @app.exception_handler(RateLimitExceeded)
    async def _rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
        # Determine key kind for audit
        key = getattr(exc, "detail", str(exc))
        endpoint = request.url.path
        audit(
            "auth.ratelimit.exceeded",
            level=logging.WARNING,
            endpoint=endpoint,
            key=key,
            key_kind="ip",
        )
        retry_after = "60"
        if hasattr(exc, "retry_after"):
            retry_after = str(exc.retry_after)
        return JSONResponse(
            status_code=429,
            content={"error": "Too many requests. Please slow down."},
            headers={"Retry-After": retry_after},
        )

    logger.info("Rate limiter is set up")


def setup_global_exception_handlers(_app: FastAPI) -> None:
    # A place to register global exception handlers
    logger.info("Global exception handlers are set up")
