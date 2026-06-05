# Architecture

## Overview

This is a FastAPI (Python 3.13) backend for a car rental management platform. It follows **Clean Architecture** with a strict CQRS pattern enforced by import-linter contracts. The codebase is a single deployable service backed by PostgreSQL.

## Layer Structure

```
src/app/
  core/           # Domain: entities, value objects, commands, queries, ports
  infrastructure/ # Adapters: SQLAlchemy, auth context, email, hashing
  presentation/   # HTTP routers and error mapping
  main/           # Application wiring: IoC container, config, entrypoint
```

The import direction is strictly enforced (inner must not import outer):

```
main → presentation → infrastructure → core
```

Import contracts are defined in `pyproject.toml` under `[tool.importlinter]`. Any violation causes `lint-imports` to fail.

## Core Layer (`src/app/core/`)

### Commands (`core/commands/`)
Use-case handlers for all write operations. Each command is a class with an `execute(request)` method. Commands depend only on abstract ports (interfaces). Authorisation is called inline via `authorize()` from `core/common/authorization/authorize.py`.

### Queries (`core/queries/`)
Read-only use-case handlers. Each returns a typed read model (`core/queries/models/`). Query ports (`core/queries/ports/`) are separate from command ports to enforce CQRS separation — import-linter contracts forbid `commands` importing `queries` and vice versa.

### Common (`core/common/`)
Shared across commands and queries — but `core/common` must not import from `core/commands` or `core/queries` (enforced by import-linter).

- **Entities**: `core/common/entities/` — plain Python classes, `Entity[ID]` base.
- **Value objects**: `core/common/value_objects/` — `Email`, `RawPassword`, `UtcDatetime`, `Username`, `Phone`, `Slug`.
- **Types**: `core/common/entities/types_.py` — all `NewType` IDs and `StrEnum` status/type enums.
- **Authorization**: `core/common/authorization/` — `HasPermission` (RBAC via glob matching), `CanManageSubordinate`, role hierarchy.
- **Ports**: abstract interfaces for `PasswordHasher`, `IdentityProvider`, `AccessRevoker`, `EmailSender`, `PushSender`.

## Infrastructure Layer (`src/app/infrastructure/`)

### Adapters (`infrastructure/adapters/`)
Concrete SQLAlchemy implementations for every command port (tx storage) and query port (reader). Naming convention: `sqla_<entity>_tx_storage.py` for writes, `sqla_<entity>_reader.py` for reads. Additional adapters: `BcryptPasswordHasher`, `SmtpEmailSender`, `AuthSessionIdentityProvider`, `StubPushSender`.

### Auth Context (`infrastructure/auth_ctx/`)
Self-contained authentication subsystem with its own SQLAlchemy session, transaction manager, and handlers. Handles: sign-up, log-in, log-out, email verification, password change/reset, and invite management. Uses JWT (HS256) stored in an `HttpOnly` cookie. Manages session records in the `auth_sessions` table. Import-linter forbids `auth_ctx` from importing from the general `adapters/` package.

### Persistence (`infrastructure/persistence_sqla/`)
- `mappings/` — SQLAlchemy ORM table definitions (imperative mapping style).
- `alembic/versions/` — 21 migration files, date-prefixed.
- `registry.py` — SQLAlchemy mapper registry.

## Presentation Layer (`src/app/presentation/http/`)

FastAPI routers, one module per use-case. Each handler module exports a `make_<action>_router()` factory. Error-to-HTTP mapping is done via `fastapi-error-map` (`ErrorAwareRouter`). The standard error map for every endpoint covers: `AuthenticationError → 401`, `AuthorizationError → 403`, `StorageError → 503`, `BusinessTypeError → 400`.

Routers are assembled in `api_v1_router.py` under the `/api/v1` prefix, then in `root_router.py` which also mounts `/health`.

## Main Layer (`src/app/main/`)

- `run.py` — `make_app()` factory, used both by uvicorn and tests.
- `config/loader.py` — pydantic-settings classes, one per settings group, each with its own env prefix.
- `ioc/core.py` — `CoreProvider` (dishka): binds all commands, queries, and their ports.
- `ioc/infrastructure.py` — `PersistenceSqlaProvider`, `AuthProvider`, `EmailProvider`, `HasherThreadPoolProvider`, `RequestProvider`.

## Dependency Injection

[dishka](https://dishka.readthedocs.io) is used for IoC. Scopes: `APP` (singleton per process), `REQUEST` (per HTTP request). The DI container is created in `make_app()` and attached to the FastAPI application via `setup_dishka`. Handler arguments annotated `FromDishka[T]` are resolved automatically via the `@inject` decorator.

## Authentication Flow

1. Client calls `POST /api/v1/account/login` with `{email, password}`.
2. `LogIn` handler verifies credentials, checks `is_active` and `email_verified`.
3. `AuthService.issue_session()` creates an `AuthSession` record, signs a JWT, and stages a cookie via `CookieManager`.
4. `AuthCookieMiddleware` (Starlette middleware) reads the staged cookie from request state and writes it to the response as `HttpOnly; Secure; SameSite=none`.
5. Subsequent requests carry the cookie; `AuthSessionIdentityProvider` decodes the JWT and looks up the session, refreshing it if within the `REFRESH_THRESHOLD_RATIO` window.

## Authorization

Permission checks use a glob-based RBAC table in `core/common/authorization/permissions.py`. Each role maps to a list of permission strings (e.g. `"rental.*"`, `"fleet.read"`). `HasPermission.is_satisfied_by()` calls `fnmatch.fnmatch(required, perm)`. The `authorize()` helper raises `AuthorizationError` on failure. Role-based subordinate management (who can manage whom) is in `rbac.py` using `ROLE_HIERARCHY`.

## Multi-Tenancy

Every entity carries an `organization_id`. The `DEFAULT_ORGANIZATION_ID` app setting exists to support single-tenant deployments where all entities belong to one org. Full multi-org is supported — clients can join/leave organizations and have a `ClientOrganization` join record.

## Key Design Decisions

- **No background task runner** — commands like `check_overdue_rentals`, `check_pickup_reminders`, `check_return_reminders` exist but must be triggered via HTTP endpoints. No Celery/ARQ/scheduler is wired.
- **Push notifications stubbed** — `StubPushSender` is the only `PushSender` implementation; actual push delivery is not implemented.
- **SMTP email** — real email sending via `SmtpEmailSender` (Gmail by default) for verification and password reset.
- **Decimal for money** — all monetary fields use `Decimal` (Python) and `Numeric(10,2)` (PostgreSQL).
- **No pagination cursor** — pagination is offset-based (`core/queries/query_support/offset_pagination.py`).
- **Connection pool** — configured in `SqlaSettings`: `POOL_SIZE=15`, `MAX_OVERFLOW=0`, `pool_pre_ping=True`.

## Current Limitations

- No real push notification delivery (stub only).
- No scheduled job runner; reminder/overdue commands require external triggering.
- No rate limiting middleware.
- No OpenAPI auth scheme definition (cookie auth is not declared in the OpenAPI spec).
- No Redis or any caching layer.
- Single-process only — uvicorn runs with `--reload` in Docker (not production-safe).
- CORS allows `http://localhost:3000` and a hardcoded Vercel URL in default settings.
- `print()` statement left in `log_in.py:62` (debug artifact).
