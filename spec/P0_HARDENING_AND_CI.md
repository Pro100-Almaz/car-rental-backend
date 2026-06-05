# P0 Hardening & CI Bootstrap

> First-pass production-readiness pass. Three small, independent fixes plus a CI pipeline.
> Estimated total effort: **~30 min code changes + ~30 min CI iteration**.
> Risk: **zero for the code fixes**; CI is additive and cannot break runtime.

---

## Scope

This spec covers three tasks that should land together as one PR:

1. **Remove a `print()` debug artifact** in the auth login handler.
2. **Stop running `uvicorn --reload` in container `start` mode** (it currently runs in every env, including prod).
3. **Add GitHub Actions CI** that runs `make lint` and `make test-docker` on every push and PR.

Out of scope (tracked separately in `docs/ROADMAP.md`):
- Real `PushSender` implementation
- Scheduler wiring for reminder commands
- Rate limiting, CORS hardening, secrets review

---

## Task 1 — Remove `print()` from login handler

### Problem

`src/app/infrastructure/auth_ctx/handlers/log_in.py:62` contains a stray debug `print` that ships to production logs and leaks `user.email_verified` per login attempt.

```python
print("*"*10, user.email_verified)
```

### Change

Delete the line. No replacement needed — structured logging via `logger.info("Log in: done.")` on line 69 already covers the success path.

### Acceptance

- `rg "print\(" src/app/infrastructure/auth_ctx/` returns no results.
- `make lint` passes.
- `make test` passes (login unit tests under `tests/unit/...auth_ctx` should be unaffected).

---

## Task 2 — Make `--reload` opt-in (not the prod default)

### Problem

`docker-entrypoint.sh:9` unconditionally launches uvicorn with `--reload`:

```bash
exec uvicorn app.main.run:make_app --factory --host 0.0.0.0 --port "$PORT" --reload
```

`--reload` spawns a file-watcher process, increases memory footprint, disables some uvicorn optimizations, and is explicitly documented as a development-only flag. In production it means every process restart re-scans the source tree.

### Change

Gate `--reload` behind an env var so dev keeps the live-reload behaviour but prod runs a plain uvicorn process.

Edit `docker-entrypoint.sh`:

```bash
#!/bin/bash
set -e

PORT=${2:-8000}
RELOAD_FLAG=""
if [ "${APP_UVICORN_RELOAD:-false}" = "true" ]; then
    RELOAD_FLAG="--reload"
fi

case "$1" in
    start)
        alembic upgrade head
        exec uvicorn app.main.run:make_app --factory --host 0.0.0.0 --port "$PORT" $RELOAD_FLAG
        ;;
    pytest)
        alembic upgrade head
        shift
        exec pytest "$@"
        ;;
    *)
        exec "$@"
        ;;
esac
```

Then in `docker-compose.yml`, set `APP_UVICORN_RELOAD=true` on the dev `app` service only (leave it unset / `false` everywhere else).

Add the variable to `env.example` with a comment:

```
# Enable uvicorn auto-reload (development only). Default: false.
APP_UVICORN_RELOAD=false
```

### Acceptance

- `bash -n docker-entrypoint.sh` passes (syntax check).
- Local `make up` still hot-reloads on source edits.
- With `APP_UVICORN_RELOAD` unset, `docker-entrypoint.sh start` runs uvicorn without `--reload` (verify with `ps aux | grep uvicorn` inside the container — no `--reload` flag).
- `make test-docker` passes.

---

## Task 3 — GitHub Actions CI

### Problem

`.github/` is empty. Lint and tests run only when a developer remembers to run them locally. Reviewers have no signal on PRs.

### Change

Create `.github/workflows/ci.yml`:

```yaml
name: CI

on:
  push:
    branches: [master]
  pull_request:
    branches: [master]

concurrency:
  group: ci-${{ github.ref }}
  cancel-in-progress: true

jobs:
  lint:
    name: Lint
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v3
        with:
          enable-cache: true

      - name: Set up Python
        run: uv python install

      - name: Install dependencies
        run: uv sync --all-extras --dev

      - name: Run make lint
        run: uv run make lint

  test:
    name: Test (docker)
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Run make test-docker
        run: make test-docker
```

### Notes on the CI file

- **Python version & uv:** the project uses `uv` per `uv.lock`. If `make lint` requires tools installed outside the uv environment (e.g. `tombi`, `deptry`, `lint-imports`, `mypy`), confirm they are listed in `pyproject.toml` dev dependencies. If any are missing, add an explicit install step or add them to dev deps. Run `make lint` locally first to confirm a clean baseline before relying on CI.
- **`make test-docker`:** the existing Makefile target already spins up Postgres via `docker-compose.test.yml` and runs the full suite. GitHub-hosted runners have Docker preinstalled, so no extra setup is needed beyond `setup-buildx-action` for layer caching.
- **Concurrency:** the `concurrency` block cancels superseded runs on the same branch (saves CI minutes when force-pushing).
- **No deploy step yet:** intentional. Deploy automation is a separate roadmap item.

### Acceptance

- The workflow file exists at `.github/workflows/ci.yml` and is valid YAML (`python -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"`).
- On the PR that introduces this spec, both `Lint` and `Test (docker)` jobs run and pass.
- A deliberately failing change (e.g. add `import os` unused) makes the `Lint` job fail.

---

## Rollout

1. Branch from `master`: `git checkout -b chore/p0-hardening-and-ci`
2. Apply Task 1, 2, 3 in any order — they are independent.
3. Run locally:
   ```
   make lint
   make test-docker
   bash -n docker-entrypoint.sh
   ```
4. Open a PR. Wait for the new CI to go green.
5. Squash-merge.

## Verification checklist (post-merge)

- [ ] `rg "print\(" src/app/` returns nothing in non-test code.
- [ ] First prod deploy after this change: `docker exec <app> ps -ef | grep uvicorn` shows no `--reload`.
- [ ] A PR opened against master triggers both CI jobs.
- [ ] Failing `ruff` or failing tests block the PR (branch protection is a separate config — note in PR description if not yet enabled).
