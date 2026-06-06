# `HTTPException`-inside-`ErrorAwareRouter` Burndown

> Same anti-pattern, 14 sites. Every "get one" / "get my X" endpoint that uses `ErrorAwareRouter` and raises `HTTPException(404)` is silently returning **500** instead of **404** because `fastapi_error_map` requires every exception to be in `error_map`.
>
> Surfaced by the rentals testing pass — see `spec/_summaries/RENTALS_API_TESTING.summary.md`. Same root cause as Bug 2 in `spec/RENTALS_ROUTING_FIX.md`, just spread across the codebase.
>
> Estimated effort: **~45 min** (mechanical).
> Risk: **Low** — same change applied uniformly, single helper exception per file.

## Inventory

| File | Current `HTTPException` | Target domain exception | New status |
|---|---|---|---|
| `clients/get_client.py` | 404 "Client not found." | `ClientNotFoundError` | 404 |
| `payments/get_transaction.py` | 404 "Transaction not found." | `TransactionNotFoundError` | 404 |
| `vehicles/get_vehicle.py` | 404 "Vehicle not found." | `VehicleNotFoundError` | 404 |
| `cash_journal/get_entry.py` | 404 "Cash journal entry not found." | `CashJournalEntryNotFoundError` | 404 |
| `service_tasks/get_service_task.py` | 404 "Service task not found." | `ServiceTaskNotFoundError` | 404 |
| `fines/get_fine.py` | 404 "Fine not found." | `FineNotFoundError` | 404 |
| `investors/get_investor.py` | 404 "Investor not found." | `InvestorNotFoundError` | 404 |
| `mobile/get_my_rental.py` | 404 "Rental not found." | `RentalNotFoundError` | 404 |
| `mobile/get_my_active_rental.py` | 404 "No active rental found." | `RentalNotFoundError` | 404 |
| `mobile/get_my_verification.py` | 404 "Client not found." | `ClientNotFoundError` | 404 |
| `mobile/get_vehicle.py` | 404 "Vehicle not found." | `VehicleNotFoundError` | 404 |
| `dashboard/revenue_chart.py` × 3 | 400 (week_start/week_end validation) | `InvalidRevenueChartRangeError` (new) | 400 |

**Total:** 11 NotFound 404 sites + 3 revenue-chart 400 sites = 14 `raise HTTPException` calls across 12 files.

All needed `*NotFoundError` exceptions already exist in `src/app/core/commands/exceptions.py`. One new exception class is added for the revenue-chart range validations.

## Changes per file

### Pattern A — NotFound 404 (11 sites)

```diff
-from fastapi import APIRouter, HTTPException, status
+from fastapi import APIRouter, status

+from app.core.commands.exceptions import <Resource>NotFoundError

     @router.get(
         "/{id}",
         error_map={
             AuthenticationError: status.HTTP_401_UNAUTHORIZED,
             ReaderError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
+            <Resource>NotFoundError: status.HTTP_404_NOT_FOUND,
         },
         ...
     )
     async def get_x(...):
         result = await interactor.execute(...)
         if result is None:
-            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="X not found.")
+            raise <Resource>NotFoundError
         return result
```

### Pattern B — revenue_chart 400s

Add a new exception in `src/app/core/commands/exceptions.py`:

```python
class InvalidRevenueChartRangeError(BaseError):
    """week_start/week_end pair is malformed (e.g. not Mon–Sun, or only one provided)."""
```

Then in `dashboard/revenue_chart.py`, replace the 3 `HTTPException(400, …)` raises with `raise InvalidRevenueChartRangeError("...")` (BaseError accepts a message), and add `InvalidRevenueChartRangeError: status.HTTP_400_BAD_REQUEST` to the route's `error_map`.

## Acceptance

For at least 3 representative routes verify via curl that requesting an unknown UUID returns **404**:

- `GET /api/v1/clients/00000000-0000-0000-0000-000000000000` → 404
- `GET /api/v1/vehicles/00000000-0000-0000-0000-000000000000` → 404
- `GET /api/v1/fines/00000000-0000-0000-0000-000000000000` → 404

And confirm at least one revenue-chart misuse returns **400**:

- `GET /api/v1/dashboard/revenue-chart?organization_id=…&week_start=2026-06-03&week_end=2026-06-09` (Wednesday start, not Monday) → 400.

`make lint-check` (the ruff portion that runs locally) stays clean. `git grep "raise HTTPException" src/app/presentation/http/` returns no matches afterwards.

## Non-goals

- Refactoring any of these handlers further.
- Touching tests (the existing curl plans become the integration check; specific module test specs will use these endpoints).
- Re-running mass formatting via `make lint-fix` — keep the diff scoped.
