from pathlib import Path
from typing import Final

from pydantic_settings import BaseSettings, SettingsConfigDict

from app.main.config.settings import (
    AppSettings,
    CookieSettings,
    CorsSettings,
    JwtSettings,
    PasswordHasherSettings,
    PostgresSettings,
    RedisSettings,
    SessionSettings,
    SmtpSettings,
    SqlaSettings,
    VerificationSettings,
)

BASE_DIR: Final[Path] = Path(__file__).resolve().parents[4]
_ENV_FILE: Final[Path] = BASE_DIR.joinpath(".env")
_DEFAULT_CONFIG_DICT: Final[SettingsConfigDict] = SettingsConfigDict(
    env_file=_ENV_FILE,
    env_file_encoding="utf-8",
    extra="ignore",
)


def _load_settings[E: BaseSettings](env_cls: type[E]) -> E:
    return env_cls()


class AppEnvConfig(BaseSettings, AppSettings):
    model_config = _DEFAULT_CONFIG_DICT | SettingsConfigDict(env_prefix="APP_")


class PostgresEnvConfig(BaseSettings, PostgresSettings):
    model_config = _DEFAULT_CONFIG_DICT | SettingsConfigDict(env_prefix="POSTGRES_")


class SqlaEnvConfig(BaseSettings, SqlaSettings):
    model_config = _DEFAULT_CONFIG_DICT | SettingsConfigDict(env_prefix="SQLA_")


class PasswordHasherEnvConfig(BaseSettings, PasswordHasherSettings):
    model_config = _DEFAULT_CONFIG_DICT | SettingsConfigDict(env_prefix="PASSWORD_")


class JwtEnvConfig(BaseSettings, JwtSettings):
    model_config = _DEFAULT_CONFIG_DICT | SettingsConfigDict(env_prefix="JWT_")


class SessionEnvConfig(BaseSettings, SessionSettings):
    model_config = _DEFAULT_CONFIG_DICT | SettingsConfigDict(env_prefix="SESSION_")


class CorsEnvConfig(BaseSettings):
    """Loads CORS config from env, accepting comma-separated origins.

    Declared as ``str`` so pydantic-settings doesn't try to JSON-decode it.
    The property converts to the ``list[str]`` expected by ``CorsSettings``.
    """

    model_config = _DEFAULT_CONFIG_DICT | SettingsConfigDict(env_prefix="CORS_")

    ALLOWED_ORIGINS: str = ""

    def to_cors_settings(self) -> CorsSettings:
        origins = [s.strip() for s in self.ALLOWED_ORIGINS.split(",") if s.strip()]
        return CorsSettings(ALLOWED_ORIGINS=origins)


class CookieEnvConfig(BaseSettings, CookieSettings):
    model_config = _DEFAULT_CONFIG_DICT | SettingsConfigDict(env_prefix="COOKIE_")


class SmtpEnvConfig(BaseSettings, SmtpSettings):
    model_config = _DEFAULT_CONFIG_DICT | SettingsConfigDict(env_prefix="SMTP_")


class VerificationEnvConfig(BaseSettings, VerificationSettings):
    model_config = _DEFAULT_CONFIG_DICT | SettingsConfigDict(env_prefix="VERIFICATION_")


class RedisEnvConfig(BaseSettings, RedisSettings):
    model_config = _DEFAULT_CONFIG_DICT | SettingsConfigDict(env_prefix="REDIS_")


def load_app_settings() -> AppSettings:
    return _load_settings(AppEnvConfig)


def load_postgres_settings() -> PostgresSettings:
    return _load_settings(PostgresEnvConfig)


def load_sqla_settings() -> SqlaSettings:
    return _load_settings(SqlaEnvConfig)


def load_password_hasher_settings() -> PasswordHasherSettings:
    return _load_settings(PasswordHasherEnvConfig)


def load_jwt_settings() -> JwtSettings:
    return _load_settings(JwtEnvConfig)


def load_session_settings() -> SessionSettings:
    return _load_settings(SessionEnvConfig)


def load_cors_settings() -> CorsSettings:
    return _load_settings(CorsEnvConfig).to_cors_settings()


def load_cookie_settings() -> CookieSettings:
    return _load_settings(CookieEnvConfig)


def load_smtp_settings() -> SmtpSettings:
    return _load_settings(SmtpEnvConfig)


def load_verification_settings() -> VerificationSettings:
    return _load_settings(VerificationEnvConfig)


def load_redis_settings() -> RedisSettings:
    return _load_settings(RedisEnvConfig)
