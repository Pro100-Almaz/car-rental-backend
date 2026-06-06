# Rentals Routing & Validation Fixes — Implementation Summary

- **Spec:** `spec/RENTALS_ROUTING_FIX.md`
- **Implemented on:** 2026-06-06
- **Implemented by:** Claude (assisting Almaz)
- **Commit / PR:** _pending — bundle with the rentals testing pass._

## What was done

Applied three targeted fixes — all small, all verified live:

### 1. Router ordering — `src/app/presentation/http/rentals/router.py`
Moved `make_list_pending_extensions_router()` to register **before** the parametric `/{rental_id}` routes. Added an inline comment explaining why literal-path routes must come first.

### 2. `GetRental` 404 path — `src/app/presentation/http/rentals/get_rental.py`
Replaced `raise HTTPException(404)` with `raise RentalNotFoundError` (the same domain exception already used by every rental *command* route). Added `RentalNotFoundError: status.HTTP_404_NOT_FOUND` to the route's `error_map`. The `HTTPException` import was removed; `RentalNotFoundError` is imported from `app.core.commands.exceptions`.

### 3. Calendar `month` validation — `src/app/presentation/http/rentals/get_rental_calendar.py`
Tightened `CalendarRequestSchema.month` to `Annotated[str, StringConstraints(pattern=r"^\d{4}-\d{2}$")]`. Malformed input now fails at the FastAPI validation layer (422) before the handler runs.

## Verification (live curl against `make upd` stack)

| Case | Before | After | Verdict |
|---|---|---|---|
| §3.2 `GET /rentals/{unknown_uuid}` | **500** | **404** | ✅ fixed |
| §5.3 `GET /rentals/calendar?month=2026/07` | **500** | **422** | ✅ fixed |
| §14 `GET /rentals/extension-requests?organization_id=…` | **422** UUID error | **200** with `{items:[], total:0}` | ✅ fixed |
| Regression: §2.1 `GET /rentals/?organization_id=…` | 200 | 200 | ✅ |
| Regression: §5.1 `GET /rentals/calendar?month=2026-07` | 200 | 200 | ✅ |
| Regression: §3.1 `GET /rentals/{existing_uuid}` | 200 | 200 | ✅ |

Hot-reload (uvicorn `--reload`, enabled by the P0 work) picked up every edit without a container restart.

## What was NOT done (and why)

- **§15.1 / §15.2 / §15.3 still couldn't be exercised.** The route is reachable (`200`), but the list is empty because `POST /rentals/{id}/extend` does **not** create an `extension_requests` row — it directly mutates the rental's `scheduled_end` (verified by SQL: `SELECT * FROM extension_requests` returns 0 rows after 4 successful `extend` calls; the affected rentals' `scheduled_end` already shifted). That's a **separate domain bug** outside this spec's scope. Tracked as a follow-up.
- **The same `HTTPException`-inside-`ErrorAwareRouter` anti-pattern exists in 14 other routes** (`clients/get_client.py`, `payments/get_transaction.py`, `vehicles/get_vehicle.py`, `cash_journal/get_entry.py`, `service_tasks/get_service_task.py`, `fines/get_fine.py`, `investors/get_investor.py`, `mobile/get_my_rental.py`, `mobile/get_my_active_rental.py`, `mobile/get_my_verification.py`, `mobile/get_vehicle.py`, `dashboard/revenue_chart.py` x3). All will return 500 instead of 404 when the resource is missing. Out of scope here; tracked as a separate burndown.

## Deviations from the spec

None.

## Follow-ups discovered

1. **`POST /rentals/{id}/extend` semantic bug.** The handler updates the rental directly, bypassing the approval flow. Either the approval workflow should be wired (extend → create row → approve/reject mutates rental), or the `/extension/approve` and `/extension/reject` endpoints are dead code. Pick one and document. → new spec.
2. **HTTPException-in-ErrorAwareRouter burndown.** 14 more sites with the same latent 500 bug. Cheap to fix uniformly (add `<Resource>NotFoundError` to each route's `error_map` and replace `raise HTTPException(404)`). → new spec.
3. **Approve/reject path uses `{rental_id}` as parameter name but holds an extension-request ID.** Rename to `{extension_request_id}` for API clarity. → ROADMAP.
4. **Dev session lifetime is 5 minutes** — painful for manual testing. Worth raising in dev via env override and documenting. → ROADMAP.

## Files changed

```
src/app/presentation/http/rentals/router.py              | +4/-1 (route order + comment)
src/app/presentation/http/rentals/get_rental.py          | +3/-3 (RentalNotFoundError)
src/app/presentation/http/rentals/get_rental_calendar.py | +2/-2 (regex validator)
spec/RENTALS_ROUTING_FIX.md                              | new (spec)
spec/_summaries/RENTALS_ROUTING_FIX.summary.md           | new (this file)
```

No tests added — the curl plan in `spec/RENTALS_API_TESTING.md` already serves as the integration check.
