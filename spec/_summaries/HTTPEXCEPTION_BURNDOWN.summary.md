# HTTPException Burndown — Implementation Summary

- **Spec:** `spec/HTTPEXCEPTION_BURNDOWN.md`
- **Implemented on:** 2026-06-06
- **Implemented by:** Claude (assisting Almaz)
- **Commit / PR:** _pending — bundles cleanly with the rentals fix._

## What was done

Replaced every `raise HTTPException(...)` inside an `ErrorAwareRouter` route with a domain-mapped exception. Removed the dead `HTTPException` imports.

- **11 NotFound sites** (404): use the existing `*NotFoundError` exception that already lived in `app.core.commands.exceptions`. Added `<Resource>NotFoundError: status.HTTP_404_NOT_FOUND` to each route's `error_map`.
- **3 revenue-chart range sites** (400): added one new `InvalidRevenueChartRangeError(BaseError)` and mapped it once.

## Files changed

```
src/app/core/commands/exceptions.py                                   +4  (new InvalidRevenueChartRangeError)
src/app/presentation/http/clients/get_client.py                       ±5
src/app/presentation/http/payments/get_transaction.py                 ±5
src/app/presentation/http/vehicles/get_vehicle.py                     ±5
src/app/presentation/http/cash_journal/get_entry.py                   ±5
src/app/presentation/http/service_tasks/get_service_task.py           ±5
src/app/presentation/http/fines/get_fine.py                           ±5
src/app/presentation/http/investors/get_investor.py                   ±5
src/app/presentation/http/mobile/get_my_rental.py                     ±5
src/app/presentation/http/mobile/get_my_active_rental.py              ±5
src/app/presentation/http/mobile/get_my_verification.py               ±5
src/app/presentation/http/mobile/get_vehicle.py                       ±5
src/app/presentation/http/dashboard/revenue_chart.py                  ±8  (3 raises + import + error_map)
spec/HTTPEXCEPTION_BURNDOWN.md                                        new
spec/_summaries/HTTPEXCEPTION_BURNDOWN.summary.md                     new
```

## Verification (live curl after hot-reload)

| Endpoint | Expected | Got |
|---|---|---|
| `GET /clients/{unknown_uuid}` | 404 | **404** ✅ |
| `GET /vehicles/{unknown_uuid}` | 404 | **404** ✅ |
| `GET /fines/{unknown_uuid}` | 404 | **404** ✅ |
| `GET /cash-journal/{unknown_uuid}` | 404 | **404** ✅ |
| `GET /investors/{unknown_uuid}` | 404 | **404** ✅ |
| `GET /tasks/{unknown_uuid}` | 404 | **404** ✅ |
| `GET /dashboard/revenue-chart?week_start=Wed…` | 400 | **400** ✅ |
| `GET /dashboard/revenue-chart?week_start=…` (only one) | 400 | **400** ✅ |
| Regression: `GET /rentals/{unknown_uuid}` | 404 | **404** ✅ |

`grep -rn "raise HTTPException" src/app/presentation/http/` returns zero matches.

## What was NOT done

- The `_parse_period` and similar helpers still raise `int()`-conversion ValueErrors on malformed input (e.g. `period=2026-XX`). That's the same family of bug fixed for `/rentals/calendar` in the previous spec but in other dashboard/report routes. Tracked as a follow-up.
- I did not run `make lint-fix` to mass-format the edits — kept the diff scoped. `ruff check --no-fix` was clean over the changed files (no new violations introduced).

## Deviations from the spec

None.

## Follow-ups discovered

1. **Other `int()`-on-malformed-input crashes.** Same shape as the `/rentals/calendar` bug, present in `dashboard/kpis.py`, `dashboard/revenue_chart.py`, `reports/pnl.py`, `reports/vehicles_comparison.py`, `reports/export.py`, `investors/get_pnl.py`, `core/queries/investor_portal_dashboard.py`. All parse `period` as `YYYY-MM` via `int(period[:4]), int(period[5:7])` without validation. Add a `^\d{4}-\d{2}$` regex constraint at each schema boundary. → new spec.
2. The `default_message: ClassVar[str]` attached to each `*NotFoundError` is unused at the HTTP boundary because `fastapi_error_map` swallows the message and returns whatever the rule's translator renders. Worth a wider check of what shape the client actually sees for each 404.
