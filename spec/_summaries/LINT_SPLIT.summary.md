# Lint Split — Implementation Summary

- **Spec:** `spec/LINT_SPLIT.md`
- **Implemented on:** 2026-06-05
- **Implemented by:** Claude (assisting Almaz)
- **Commit / PR:** _pending — bundled with the P0 hardening PR_

## What was done

- **Makefile:** split the `lint` target into three:
  - `lint-check` — read-only, CI-safe.
  - `lint-fix` — mutating; equivalent to the old `lint` behavior.
  - `lint` — alias of `lint-fix` for backwards compatibility with developer muscle memory.
  - `.PHONY` updated accordingly.
- **`.github/workflows/ci.yml`:** the `Lint` job now runs `uv run make lint-check` instead of `make lint`. CI is now non-mutating.

## What was NOT done (and why)

- **Did not fix the 143 ruff violations.** That is a separate burn-down PR — out of scope for this spec. The whole point here was to surface them in CI, not to fix them.
- **Did not split per-tool targets** (`lint-ruff`, `lint-mypy`, etc.). Not needed yet.

## Deviations from the spec

- **One critical addition:** the spec's `lint-check` invoked `ruff check`. That is **not** read-only in this repo because `pyproject.toml` sets `[tool.ruff] fix = true`, which makes `ruff check` silently apply auto-fixes by default. The first run mutated 105 files. The Makefile now uses `ruff check --no-fix` explicitly, with a comment documenting why. (An alternative would be to remove `fix = true` from `pyproject.toml`, but that would change `ruff` CLI behavior for every developer's editor integration. Keeping the global default but overriding in CI is the safer choice.)
- No other deviations.

## Verification

| Check | Command | Result |
|---|---|---|
| `lint-check` is read-only | `make lint-check` then `git status --short` | **PASS** — `git status` after the run shows only the four intentional file edits already in the tree; zero new modifications from `lint-check`. |
| `lint-check` exits non-zero on violations | `make lint-check; echo $?` | **PASS** — exits 1 with "Found 143 errors. [*] 112 fixable with the `--fix` option." (correct CI signal). |
| `lint` alias still works | (inspected Makefile) | **PASS** — `lint: lint-fix` is in place. |
| `lint-fix` behavior unchanged | (inspected Makefile diff) | **PASS** — identical command list to the previous `lint` target. |

## Follow-ups discovered

1. **Burn down the 143 ruff violations.** Already noted in the P0 summary; this PR doesn't change that count. A reasonable order: (a) take `ruff check --fix` once on a feature branch and review the auto-fixes; (b) hand-fix the remaining ~30 unsafe ones (mostly `DTZ011`, `PLR2004`, `B008`, `A002`). Estimated 2–3 hours. → Add to `docs/ROADMAP.md` as a dedicated entry.
2. **`tombi format --check` flag verification.** The `--check` flag is the documented non-mutating mode, but if a future tombi version renames it, `lint-check` would silently regress to mutating. Worth a CI assertion (e.g. `git diff --exit-code` after `lint-check` in CI). Not blocking.
3. **Consider also dropping `fix = true` from `pyproject.toml`** at some point. Currently it makes editor integrations (LSP/VS Code) auto-apply fixes on save, which can be surprising. Out of scope here.

## Files changed

```
Makefile                          | ~15 lines reorganized (one target → three)
.github/workflows/ci.yml          | 2 lines (step name + command)
spec/LINT_SPLIT.md                | new file (spec)
spec/_summaries/LINT_SPLIT.summary.md | new file (this file)
```
