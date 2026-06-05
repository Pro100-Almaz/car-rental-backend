# Deployment

## Current Setup

The project ships as a single Docker image fronted by docker-compose. There is no CI/CD pipeline in the repository (`.github/` directory exists but is empty).

## Docker Image

`Dockerfile` — multi-stage build using the official `uv` base image.

- Base: `ghcr.io/astral-sh/uv:python3.13-trixie-slim`
- Build arg `ENVIRONMENT` (`prod` | `dev`, default `prod`) controls whether dev dependencies are installed.
- In `prod` mode: `uv sync --frozen --no-cache --no-dev`.
- In `dev` mode: `uv sync --frozen --no-cache --dev` (used in docker-compose).
- Runs as non-root user `runner`.
- Exposes port `8000`.
- Entrypoint: `docker-entrypoint.sh`.

## Entrypoint

`docker-entrypoint.sh` supports two modes:

| Command | Behaviour |
|---|---|
| `start <port>` | `alembic upgrade head` then `uvicorn app.main.run:make_app --factory --host 0.0.0.0 --port <port> --reload` |
| `pytest [args]` | `alembic upgrade head` then `pytest <args>` |
| anything else | exec directly |

The container in `docker-compose.yml` runs `command: ["start", "8000"]`.

Note: `--reload` is enabled even in the Docker dev setup — this is not safe for production use (file watching adds overhead and can mask startup issues).

## docker-compose.yml

Two services:

| Service | Image | Port |
|---|---|---|
| `app` | built from `Dockerfile` with `ENVIRONMENT=dev` | `127.0.0.1:${UVICORN_PORT}:8000` |
| `db_pg` | `postgres:18-alpine` | `127.0.0.1:${POSTGRES_PORT}:5432` |

`app` depends on `db_pg` with a health check (`pg_isready`). The app source is mounted as a volume (`- .:/code`), enabling live reload.

PostgreSQL data is persisted in the named volume `pg_data`.

## docker-compose.test.yml

Used by `make test-docker`. Overrides the `app` service to run pytest instead of uvicorn. The test runner container is named `$(PROJECT_NAME)-test-runner` for log/coverage extraction.

## Running in Production (Recommended Steps)

The current setup is dev-only. Before shipping to production:

1. Remove `--reload` from the entrypoint start command.
2. Set `ENVIRONMENT=prod` in the Docker build args.
3. Set `COOKIE_SECURE=true`, `COOKIE_SAMESITE=none` (already default).
4. Replace the hardcoded `CORS_ALLOWED_ORIGINS` with environment-specific values.
5. Use a proper secrets manager (Vault, AWS SSM, etc.) for `JWT_SECRET` and `PASSWORD_PEPPER`.
6. Set `APP_DEBUG_MODE=false`.
7. Configure `SQLA_POOL_SIZE` based on your worker count.
8. Add a reverse proxy (nginx/caddy) for TLS termination.
9. Consider running multiple uvicorn workers (`--workers N`) or using gunicorn as the process manager.

## Environment Configuration

All config is injected via environment variables. The `.env` file is loaded by pydantic-settings from `src/app/main/config/loader.py`. In production, pass env vars directly to the container rather than using a `.env` file.

Required secrets (no defaults — app will fail to start without them):

- `JWT_SECRET` (min 32 characters)
- `PASSWORD_PEPPER` (min 32 characters)
- `POSTGRES_DB`, `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_USER`, `POSTGRES_PASSWORD`

## No CI/CD

The `.github/` directory is present but empty. There is no automated pipeline. Setting one up is listed as a priority in `ROADMAP.md`.
