# Lint Burn-Down

> Make `make lint-check` exit zero so CI can actually gate on it.
> Today: 143 ruff violations across ~110 files.
> Estimated effort: **~2–3 h** (auto-fix is instant; the hand-fix tail is the work).
> Risk: **Medium** — touches many files. Auto-fixes are mechanical; the manual fixes include `DTZ011` (semantics around timezone-naive dates) which warrants a tests-pass check.

---

## Inventory

From `ruff check --no-fix --statistics`:

| Rule | Count | Fixable | Description |
|---|---|---|---|
| I001 | 95 | ✓ | Unsorted imports |
| B008 | 13 | ✗ | `Query(...)` etc. as function default |
| DTZ011 | 8 | ✗ | `datetime.date.today()` without timezone |
| F401 | 8 | ✓ | Unused imports |
| UP017 | 7 | ✓ | `datetime.timezone.utc` → `datetime.UTC` |
| PERF401 | 2 | ✗ | Manual list comprehension |
| PLR2004 | 2 | ✗ | Magic value comparison |
| A002 | 1 | ✗ | Function arg `type` shadows builtin |
| C901 | 1 | ✗ | Too-complex function |
| E501 | 1 | ✗ | Line too long (138 > 120) |
| PLC0415 | 1 | ✗ | Import outside top-level |
| PLR0915 | 1 | ✗ | Too many statements |
| RUF005 | 1 | ✓ | Collection literal concatenation |
| RUF059 | 1 | ✓ | Unused unpacked variable |
| S105 | 1 | ✗ | Hardcoded password string |
| **Total** | **143** | **112 auto-fix / 31 manual** | |

## Strategy

### Phase 1 — Take the auto-fixes

Run `make lint-fix`. This applies the 112 mechanical fixes (`ruff check --fix` honors `unsafe-fixes = true` from `pyproject.toml`).

**Review pass after auto-fix:**
- `git diff --stat` — confirm only `.py` files changed.
- Spot-check `UP017` migrations (`datetime.timezone.utc` → `datetime.UTC`) — semantically identical, but eyeball one or two.
- Spot-check `F401` (deleted imports) — make sure no `__all__` exports got broken.

### Phase 2 — Hand-fix the 31 manual violations

| Rule | Approach |
|---|---|
| **B008** (13) | Convert `param: T = Query(...)` → `param: Annotated[T, Query(...)]`. The codebase already uses `Annotated` in newer routes (e.g. `src/app/presentation/http/reports/export.py:53`). Apply the same pattern everywhere ruff complains. |
| **DTZ011** (8) | Replace `datetime.date.today()` with `datetime.datetime.now(tz=UTC).date()`. The codebase is UTC-throughout (see `UtcTimer`), so this is semantically equivalent. |
| **PERF401** (2) | Convert `for x: list.append(...)` to `list.extend(...)`. Mechanical. |
| **PLR2004** (2) | Extract magic value into a module-level constant (e.g. `DECEMBER = 12`). |
| **A002** (1) | Rename `type` parameter to `report_type` (or `kind`). Caller side must be updated — internal route only, low blast radius. |
| **C901** (1) | Add `# noqa: C901` with a comment "// TODO: refactor — see ROADMAP". Burn-down is not a refactor. |
| **E501** (1) | Split the long literal across lines. |
| **PLC0415** (1) | Hoist import to module top if no circular, else `# noqa: PLC0415` with reason. |
| **PLR0915** (1) | `# noqa: PLR0915` on `make_export_router` with a TODO. Refactoring the export router is its own story. |
| **RUF005**, **RUF059** | Auto-fix in Phase 1. |
| **S105** (1) | Inspect — if false positive (a constant name like `_PASSWORD_FIELD = "password"`), add `# noqa: S105` with reason. If real, escalate. |

### Phase 3 — Verify

- `make lint-check` exits 0.
- `make test` (light suite — no docker required) passes.
- `git diff --stat` reviewed for total file count and concentrated changes.

## Acceptance

- `make lint-check` is clean (exit 0, zero findings).
- The light test suite (`tests/sanity`, `tests/unit`, `tests/integration/no_infra`) passes.
- No `# noqa` added without an inline reason.
- No semantic changes beyond the documented categories above.

## Non-goals

- Refactoring `make_export_router` (its `PLR0915` and `C901` are noqa'd with TODO).
- Migrating the entire codebase to `Annotated` parameters — only the routes ruff complains about. Other routes stay as-is.
- Touching files outside `src/`.

## Rollback

This PR can be reverted as a single revert commit if regressions appear. The auto-fix portion is self-contained per file; the hand-fix portion is small and localized.
