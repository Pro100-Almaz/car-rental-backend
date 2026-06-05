# Reminder Scheduler

> Wire a clock-driven runner that periodically invokes the three reminder/overdue command handlers. Today they exist and are tested but never execute in production.
> Estimated effort: **~1 day** (process + DI wiring + ops + smoke test).
> Risk: **Low–Medium** — additive process; the failure mode if scheduler crashes is "notifications stop", not "API breaks".

---

## Context — what already exists

| Handler | Path | Purpose |
|---|---|---|
| `CheckOverdueRentals` | `src/app/core/commands/check_overdue_rentals.py` | Finds rentals overdue > 1 h, notifies client |
| `CheckPickupReminders` | `src/app/core/commands/check_pickup_reminders.py` | Finds rentals with pickup in the next 1 h, notifies client |
| `CheckReturnReminders` | `src/app/core/commands/check_return_reminders.py` | Same shape, return-side |
| IoC bindings | `src/app/main/ioc/core.py:409-411` | All three already `provide(...)`'d |

All three are scoped per `organization_id`. Whatever scheduler we add must iterate organizations and invoke each handler per org.

What is missing: **the trigger.** Nothing periodically wakes up to call `.execute(...)`.

---

## Scope

In-scope:
- A separate worker process that runs scheduled jobs.
- A scheduler implementation tied to the app's DI container (so handlers get the same DB session, services, settings as the API).
- A scheduling table that maps each handler to a cadence.
- Container changes: add a `worker` entrypoint mode in `docker-entrypoint.sh`, add a `worker` service in `docker-compose.yml`.
- A heartbeat log line per tick so liveness is observable.
- One integration test that boots the scheduler with mocked handlers and asserts they fire on cadence (or asserts the registry is correctly populated, which is the more practical test).

Out of scope:
- Multi-node coordination (leader election, distributed locks). Single-instance worker for MVP.
- Per-organization custom cadence (everyone runs at the same cadence).
- A web UI for managing jobs.
- Backfill / catch-up logic if the worker was down (we accept skipped ticks).

---

## Design decision: which scheduler

Recommended: **APScheduler with `AsyncIOScheduler`** running in its own container, sharing the codebase and DI container.

Why:
- Pure Python — no new infrastructure dependency (no Redis, no broker).
- Plays nicely with `asyncio` and the existing async handlers.
- Job definitions live in code, version-controlled like everything else.
- For MVP single-instance deployment, the lack of distributed coordination is fine.

Rejected alternatives:
- **Celery beat + workers** — adds Redis/RabbitMQ + a second runtime model. Worth it once you also have queue-shaped background work; not for three cron-style jobs.
- **External cron / k8s CronJob** — works but requires either a CLI entrypoint per command or an internal HTTP endpoint. Both add surface area and split responsibility.
- **APScheduler in-process with the API** — tempting, but couples the API process lifecycle to scheduled work, breaks once you scale the API to N replicas (jobs run N times), and increases the API blast radius.

When the platform scales to multiple worker replicas, the migration path is APScheduler-with-`SQLAlchemyJobStore` and a `coalesce=true` lock, or switch to Celery.

---

## Cadence (initial)

| Job | Cron | Why |
|---|---|---|
| `CheckPickupReminders` | every 5 min | Window in handler is 1 h ahead — 5 min granularity is fine |
| `CheckReturnReminders` | every 5 min | Same |
| `CheckOverdueRentals` | every 15 min | Overdue check tolerates longer cadence (1 h threshold already) |

These numbers are starting points; tune from metrics after the first week.

---

## Implementation outline

> This is a *plan*. No implementation lands as part of this spec.

### 1. New worker entrypoint

Add a module `src/app/main/worker.py`:

- Builds the same Dishka container the API uses (factory in `src/app/main/setup.py`).
- Constructs an `AsyncIOScheduler`.
- Registers one job per handler. Job callable:
  1. Opens a request scope on the container.
  2. Lists organization IDs from a fresh `OrganizationReader` (need to confirm the port name — if absent, add a tiny query rather than hardcoding).
  3. For each org, resolves the handler and awaits `.execute(organization_id=...)`.
  4. Logs counts and exceptions.
- Starts the scheduler and blocks on `asyncio.Event().wait()`.
- Handles SIGTERM cleanly (shutdown scheduler, close container).

### 2. Entrypoint mode

Extend `docker-entrypoint.sh` to recognize a new `worker` command:

```bash
case "$1" in
    start)        # existing
        ...
        ;;
    worker)
        alembic upgrade head
        exec python -m app.main.worker
        ;;
    pytest)       # existing
        ...
        ;;
    *)
        exec "$@"
        ;;
esac
```

(`alembic upgrade head` is defensive — should already have been run by the API container, but harmless if it has.)

### 3. Compose service

Add to `docker-compose.yml`:

```yaml
  worker:
    build:
      context: .
      dockerfile: ./Dockerfile
      args:
        - ENVIRONMENT=dev
    restart: on-failure
    depends_on:
      db_pg:
        condition: service_healthy
    env_file:
      - .env
    command: ["worker"]
```

Single instance — no port mapping, no health check needed beyond the log heartbeat.

### 4. Listing organizations

The handlers take an `organization_id`. The worker needs an iterable of org IDs. Confirm whether `OrganizationReader.list_all()` (or equivalent) exists; if not, add the smallest query that returns active org IDs.

### 5. Observability

- `log.info("scheduler.tick %s", job_name)` on each fire.
- `log.info("scheduler.result %s org=%s sent=%d", job_name, org_id, sent)` per org.
- Sum counts and emit one line per tick so log volume is bounded.

### 6. Tests

- `tests/integration/no_infra/test_worker_registry.py`:
  - Imports `app.main.worker.build_scheduler(container)`.
  - Asserts the three jobs are registered with the expected IDs and triggers.
- Resist the temptation to test "wait 5 minutes and observe a fire" — that's flaky and slow. Test registration; test the handlers themselves separately (they already are).

---

## Acceptance

- `docker compose up worker` brings up a healthy worker that logs its first heartbeat within 60 s.
- A manual `docker exec ... python -c "from app.main.worker import run_once_now; ..."` (or equivalent admin command) successfully runs one tick of each job against the dev DB.
- Worker survives a single handler exception (logs and continues).
- `docs/DEPLOYMENT.md` includes worker deployment notes.

---

## Risks / open questions

- **Multi-replica safety.** If the worker is accidentally scaled to >1, jobs fire >1× → duplicate notifications. Mitigation: document "single replica" in `DEPLOYMENT.md`; add a `replicas: 1` constraint in compose/k8s; consider a Postgres advisory lock as cheap insurance.
- **Missed-tick policy.** If the worker is down for 2 h and comes back, do overdue checks "catch up"? APScheduler default is to skip — acceptable for these workloads. Document it.
- **Organization listing source.** If no port exists, decide whether the worker reads from `OrganizationReader` (preferred) or directly from a session — preserve layering.
- **Timezone.** All cron expressions run in UTC. Confirm the handlers' `UtcTimer` produces UTC instants (it does, by name) so wall-clock semantics align.
