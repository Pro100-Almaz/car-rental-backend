import logging

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.main.config.logging_ import DATEFMT, FMT, LoggingLevel
from app.main.config.settings import CookieSettings, CorsSettings
from app.presentation.http.auth_cookie_middleware import AuthCookieMiddleware

logger = logging.getLogger(__name__)


def setup_logging(*, level: LoggingLevel = LoggingLevel.INFO) -> None:
    logging.basicConfig(
        level=level,
        datefmt=DATEFMT,
        format=FMT,
        force=True,
    )
    logger.info("Logging is set up")


def setup_middlewares(app: FastAPI, cookie_settings: CookieSettings, cors_settings: CorsSettings) -> None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(
        AuthCookieMiddleware,
        cookie_name=cookie_settings.NAME,
        cookie_path=cookie_settings.PATH,
        cookie_httponly=cookie_settings.HTTPONLY,
        cookie_secure=cookie_settings.SECURE,
        cookie_samesite=cookie_settings.SAMESITE,
    )
    logger.info("Middlewares are set up")


def setup_global_exception_handlers(_app: FastAPI) -> None:
    # A place to register global exception handlers
    logger.info("Global exception handlers are set up")
