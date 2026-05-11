# AutoFleet Backend

Car sharing operations platform backend built with FastAPI, SQLAlchemy 2.0, and PostgreSQL.

## Architecture

Clean Architecture with 4 layers enforced by import-linter (6 contracts):

```
core/           Domain entities, commands (CQRS writes), queries (CQRS reads)
infrastructure/ SQLAlchemy persistence, adapters, auth context
presentation/   FastAPI HTTP routers
main/           Configuration, IoC container (dishka)
```

Key patterns:
- **CQRS** -- commands write via TxStorage ports, queries read via Reader ports
- **Imperative SQLAlchemy mapping** -- domain entities stay ORM-free
- **dishka DI** -- Provider classes with APP/REQUEST scopes
- **RBAC** -- fnmatch-based wildcard permissions per role
- **State machines** -- for vehicles, rentals, transactions, and service tasks

## Implemented Modules

| Module | Endpoints | Description |
|--------|-----------|-------------|
| **Organizations** | `POST /api/v1/organizations` | Multi-tenant org management |
| **Branches** | `POST, GET /api/v1/branches` | Branch locations per org |
| **Users** | `POST, GET, PATCH /api/v1/users` | User CRUD, roles, activate/deactivate |
| **Account** | `POST /api/v1/account` | Auth sessions (login/logout) |
| **Vehicles** | `POST, GET, PATCH /api/v1/vehicles` | Fleet CRUD, status state machine, nickname support |
| **Clients** | `POST, GET, PATCH /api/v1/clients` | Profiles, verification, blacklisting, trust scoring |
| **Rentals** | `POST, GET, PATCH /api/v1/rentals` | Booking CRUD, state machine (pending -> confirmed -> active -> returning -> completed), check-in/out, extend, cancel with reason, prepayment tracking |
| **Payments** | `POST, GET /api/v1/payments` | Transactions, deposit hold/release, charge, refund |
| **Fines** | `POST, GET, PATCH /api/v1/fines` | Fine registration, charge to client |
| **Service Tasks** | `POST, GET, PATCH /api/v1/tasks` | Task CRUD, state machine (created -> assigned -> in_progress -> photo_proof -> completed), completion with proof |

## Tech Stack

- **Python 3.12+**, **FastAPI**, **SQLAlchemy 2.0** (async), **PostgreSQL**
- **Alembic** for migrations
- **dishka** for dependency injection
- **bcrypt** for password hashing
- **Pydantic v2** for validation
- **Ruff** + **mypy** + **import-linter** for code quality

## Prerequisites

```shell
uv sync
source .venv/bin/activate
pre-commit install --hook-type pre-commit --hook-type pre-push
```

## Start in Docker

```shell
make upd
```

## Start locally

```shell
make upd-local
alembic upgrade head
uvicorn app.main.run:make_app --host 0.0.0.0 --port 8000 --reload
```

Full API access:
- Create user via sign up
- Set its role to `super_admin` manually in DB
- Log in as super admin

## Stop

```shell
make down
```

## Test

```shell
make check        # light paths
make test-docker  # all paths
```

See [Makefile](Makefile) for more commands.

## Project Structure

```
src/app/
  core/
    common/
      entities/        Domain entities (Vehicle, Rental, Client, etc.)
      authorization/   RBAC, current user service
      factories/       ID factories
      value_objects/   UtcDatetime, Slug, Email
    commands/          Write operations (CQRS command side)
      ports/           Abstract storage interfaces
    queries/           Read operations (CQRS query side)
      ports/           Abstract reader interfaces
      models/          Query result dataclasses
  infrastructure/
    persistence_sqla/
      mappings/        Imperative SQLAlchemy table mappings
      alembic/         Database migrations
    adapters/          Concrete implementations of ports
    auth_ctx/          Auth session management
  presentation/
    http/              FastAPI routers per domain
  main/
    config/            Settings (Pydantic)
    ioc/               dishka IoC container providers
```
