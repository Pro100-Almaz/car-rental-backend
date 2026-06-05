# Development

## Prerequisites

- Python 3.13 (exact version required — `requires-python = "==3.13.*"`)
- [uv](https://docs.astral.sh/uv/) (package manager, used by Dockerfile and Makefile scripts)
- Docker + Docker Compose (for infra and full test run)
- PostgreSQL 18 (or use `make upd-local` to run it in Docker)

## Local Setup

```bash
# 1. Clone and enter the project
cd /path/to/backend

# 2. Copy environment file
cp env.example .env
# Edit .env — at minimum set:
#   JWT_SECRET (min 32 chars)
#   PASSWORD_PEPPER (min 32 chars)
#   POSTGRES_* values

# 3. Install dependencies (creates .venv)
uv sync --frozen --dev

# 4. Install pre-commit hooks
uv run pre-commit install

# 5. Start the database only (Docker)
make upd-local

# 6. Run migrations
uv run alembic upgrade head

# 7. (Optional) Seed a super-admin user
uv run python -m app.main.cli.seed_superadmin

# 8. Start the dev server
uv run uvicorn app.main.run:make_app --factory --host 0.0.0.0 --port 8000 --reload
```

API docs are available at `http://localhost:8000/docs`.

## Environment Variables

All variables are loaded from `.env` at the project root. Each settings group has a prefix:

| Prefix | Settings class | Key variables |
|---|---|---|
| `APP_` | `AppSettings` | `LOGGING_LEVEL`, `DEBUG_MODE`, `ROOT_PATH`, `DEFAULT_ORGANIZATION_ID` |
| `POSTGRES_` | `PostgresSettings` | `DB`, `HOST`, `PORT`, `USER`, `PASSWORD` |
| `SQLA_` | `SqlaSettings` | `ECHO`, `POOL_SIZE` (default 15), `MAX_OVERFLOW` (default 0) |
| `JWT_` | `JwtSettings` | `SECRET` (min 32 chars), `ALGORITHM` (default HS256) |
| `PASSWORD_` | `PasswordHasherSettings` | `PEPPER` (min 32 chars), `WORK_FACTOR` (default 11) |
| `SESSION_` | `SessionSettings` | `TTL_MIN` (default 5), `REFRESH_THRESHOLD_RATIO` (default 0.2) |
| `COOKIE_` | `CookieSettings` | `NAME`, `SECURE`, `SAMESITE` |
| `CORS_` | `CorsSettings` | `ALLOWED_ORIGINS` (JSON list) |
| `SMTP_` | `SmtpSettings` | `HOST`, `PORT`, `USERNAME`, `PASSWORD`, `FROM_EMAIL` |
| `VERIFICATION_` | `VerificationSettings` | `CODE_TTL_MIN`, `RESEND_COOLDOWN_SEC` |

See `env.example` for a template. See `src/app/main/config/settings.py` for defaults and constraints.

## Make Targets

| Target | Description |
|---|---|
| `make lint` | ruff check+format, tombi format+lint, deptry, slotscheck, mypy, lint-imports |
| `make test` | pytest on sanity + unit + integration/no_infra with coverage |
| `make check` | lint + test + coverage html |
| `make test-docker` | Full test suite (all tiers) inside Docker with a live Postgres |
| `make upd` | Build and start all services in Docker (detached) |
| `make up` | Same, attached |
| `make upd-local` | Start infra services only (db_pg) in Docker for local dev |
| `make up-local` | Same, attached |
| `make down` | Stop and remove containers |
| `make pip-audit` | Security audit of Python dependencies |
| `make slotscheck` | Check `__slots__` consistency across `src/` |
| `make tree` | Print directory tree (clears pycache first) |
| `make plot-data` | Dump dishka dependency graph data |
| `make prune` | Docker system prune |

## Test Suite Structure

```
tests/
  sanity/           # Config and loader sanity checks (no DB)
  unit/             # Pure unit tests: entities, value objects, commands, auth
  integration/
    no_infra/       # Integration tests that need no running services
    with_infra/     # Full integration tests against a live Postgres DB
  smoke/            # HTTP-level smoke tests (ASGI test client, no DB)
  performance/      # Profiling scripts (not run in CI)
```

`make test` runs `sanity + unit + integration/no_infra` (fast, no Docker required).
`make test-docker` runs all tiers including `smoke` and `integration/with_infra` inside Docker.

## Code Quality Toolchain

- **ruff** — linting (extensive ruleset) and formatting. Config in `pyproject.toml [tool.ruff]`.
- **mypy** — strict type checking with pydantic and sqlalchemy plugins. Config in `pyproject.toml [tool.mypy]`.
- **import-linter** — enforces Clean Architecture layer boundaries and CQRS separation.
- **slotscheck** — verifies `__slots__` declarations are consistent.
- **deptry** — detects unused/missing declared dependencies.
- **tombi** — TOML formatting and linting.
- **pre-commit** — runs a subset of these checks on git commit. Config in `.pre-commit-config.yaml`.

Run the full suite: `make check`.

## Common Workflows

### Add a Python dependency
```bash
uv add <package>==<version>
# Then update pyproject.toml and uv.lock
```

### Generate a new migration
```bash
uv run alembic revision --autogenerate -m "describe_the_change"
# Review the generated file in src/app/infrastructure/persistence_sqla/alembic/versions/
# Then: uv run alembic upgrade head
```

### Apply pending migrations
```bash
uv run alembic upgrade head
```

### Rollback one migration
```bash
uv run alembic downgrade -1
```

### Seed superadmin
```bash
uv run python -m app.main.cli.seed_superadmin
```

### Run linting only (fast feedback)
```bash
uv run ruff check --fix && uv run ruff format
```
