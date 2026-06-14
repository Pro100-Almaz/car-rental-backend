from datetime import timedelta
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, PostgresDsn

from app.infrastructure.auth_ctx.jwt_types import JwtAlgorithm
from app.main.config.logging_ import LoggingLevel


class AppSettings(BaseModel):
    SERVICE_NAME: str = "clean-example"
    VERSION: str = "development"
    ROOT_PATH: str = "/"
    DEBUG_MODE: bool = False
    LOGGING_LEVEL: LoggingLevel = LoggingLevel.INFO
    DEFAULT_ORGANIZATION_ID: UUID | None = None


class PostgresSettings(BaseModel):
    DB: str
    HOST: str
    PORT: int
    USER: str
    PASSWORD: str

    @property
    def dsn(self) -> str:
        return str(
            PostgresDsn.build(
                scheme="postgresql+psycopg",
                username=self.USER,
                password=self.PASSWORD,
                host=self.HOST,
                port=self.PORT,
                path=self.DB,
            ),
        )


class SqlaSettings(BaseModel):
    ECHO: bool = False
    ECHO_POOL: bool = False
    POOL_SIZE: int = 15
    MAX_OVERFLOW: int = 0


class PasswordHasherSettings(BaseModel):
    # https://www.ietf.org/archive/id/draft-ietf-kitten-password-storage-04.html#section-4.2
    PEPPER: str = Field(min_length=32)

    # https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html#introduction
    WORK_FACTOR: int = 11
    # CPU-bound & GIL released: per-worker ≈ max(1, floor(effective vCPUs / workers))
    MAX_THREADS: int = 8
    # Fail-fast cap: max semaphore wait before timeout (start ~1 second, tune to peak)
    SEMAPHORE_WAIT_TIMEOUT_S: float = 1.0


class JwtSettings(BaseModel):
    # Min length 32 for 256-bit: https://www.rfc-editor.org/rfc/rfc7518#section-3.2
    SECRET: str = Field(min_length=32)

    ALGORITHM: JwtAlgorithm = "HS256"
    ISSUER: str = "car-rental-backend"
    AUDIENCE: str = "car-rental-clients"
    ACCESS_TTL_MIN: int = Field(ge=1, default=15)
    REFRESH_TTL_DAYS: int = Field(ge=1, default=30)

    @property
    def access_ttl(self) -> timedelta:
        return timedelta(minutes=self.ACCESS_TTL_MIN)

    @property
    def refresh_ttl(self) -> timedelta:
        return timedelta(days=self.REFRESH_TTL_DAYS)


class SessionSettings(BaseModel):
    # Retained as a no-op shim during the cookie→bearer migration.
    # Will be removed once all references are gone.
    TTL_MIN: int = Field(ge=1, default=5)
    REFRESH_THRESHOLD_RATIO: float = Field(gt=0, lt=1, default=0.2)

    @property
    def ttl(self) -> timedelta:
        return timedelta(minutes=self.TTL_MIN)


class CorsSettings(BaseModel):
    ALLOWED_ORIGINS: list[str] = []


class CookieSettings(BaseModel):
    NAME: str = "auth_token"
    PATH: str = "/"
    HTTPONLY: bool = True
    SECURE: bool = True
    SAMESITE: Literal["lax", "strict", "none"] = "none"


class RedisSettings(BaseModel):
    HOST: str = "redis"
    PORT: int = 6379
    DB: int = 0
    PASSWORD: str | None = None

    @property
    def url(self) -> str:
        auth = f":{self.PASSWORD}@" if self.PASSWORD else ""
        return f"redis://{auth}{self.HOST}:{self.PORT}/{self.DB}"


class SmtpSettings(BaseModel):
    HOST: str = "smtp.gmail.com"
    PORT: int = 465
    USERNAME: str = ""
    PASSWORD: str = ""
    FROM_EMAIL: str = ""
    USE_TLS: bool = True


class VerificationSettings(BaseModel):
    CODE_TTL_MIN: int = Field(ge=1, default=10)
    RESEND_COOLDOWN_SEC: int = Field(ge=10, default=60)

    @property
    def code_ttl(self) -> timedelta:
        return timedelta(minutes=self.CODE_TTL_MIN)


class InternalJobsSettings(BaseModel):
    RUNNER_SECRET: str = Field(min_length=32)
