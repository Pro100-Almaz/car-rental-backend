# Split `make lint` into check + fix

> Today `make lint` runs `ruff check --fix`, `ruff format`, and `tombi format` — all of which mutate the working tree. That makes the target unsafe to use as a CI gate (CI silently rewrites files instead of failing) and surprising for developers who expect `lint` to be read-only.
> Estimated effort: **~15 min**.
> Risk: **Very low** — purely a Make/CI change.

---

## Goal

After this change:

- `make lint-check` — **read-only**. Safe for CI. Fails non-zero on any violation.
- `make lint-fix` — **mutating**. Auto-applies ruff fixes, runs formatters. For developer use before commit.
- `make lint` — kept as an alias for **`lint-fix`** to preserve existing developer muscle memory.
- `.github/workflows/ci.yml` calls `lint-check`, not `lint`.

## Changes

### Makefile

Replace the single `lint` target with:

```make
.PHONY: lint lint-check lint-fix

# Read-only checks. CI uses this.
lint-check:
	ruff check
	ruff format --check
	tombi format --check
	tombi lint
	deptry
	$(MAKE) slotscheck
	lint-imports
	mypy

# Apply auto-fixes and formatters. Developer convenience.
lint-fix:
	ruff check --fix
	ruff format
	tombi format
	tombi lint
	deptry
	$(MAKE) slotscheck
	lint-imports
	mypy

# Default for `make lint` stays as the fix variant to preserve current dev workflow.
lint: lint-fix
```

`check: lint test` still works (it pulls in `lint-fix` via the alias — fine for local use).

### CI workflow

`.github/workflows/ci.yml`: change `uv run make lint` → `uv run make lint-check`.

## Acceptance

- `make lint-check` exits non-zero (it will — there are 32 pre-existing ruff errors). That's the **correct** behavior; the point of this PR is to surface them in CI rather than auto-fixing them away.
- `make lint-check` does NOT modify any tracked files. Confirm with `git status` before/after.
- `make lint-fix` behaves exactly as the old `make lint` did.
- CI's `Lint` job invokes `make lint-check`.

## Non-goals

- Fixing the 32 ruff errors. That is a separate burn-down PR.
- Splitting per-tool (e.g. `lint-ruff`, `lint-mypy`). Not worth the granularity yet.
