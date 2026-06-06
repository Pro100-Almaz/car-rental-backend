# Rentals — Routing & Validation Fixes

> Three bugs discovered during the rentals API test pass (see `spec/_summaries/RENTALS_API_TESTING.summary.md`).
> Estimated effort: **~30 min**.
> Risk: **Low** — localised changes in two files; no schema or behaviour migration.

## Bugs to fix

### Bug 1 — `/rentals/extension-requests` shadowed by `/rentals/{rental_id}`

- **Symptom:** `GET /api/v1/rentals/extension-requests?organization_id=…` returns `422` with `Input should be a valid UUID … input: 'extension-requests'`.
- **Cause:** `src/app/presentation/http/rentals/router.py` registers `make_list_pending_extensions_router()` (literal path `/extension-requests`) **after** `make_get_rental_router()` (`/{rental_id}`). FastAPI matches the parametric route first.
- **Fix:** move `make_list_pending_extensions_router()` to be included **before** `make_get_rental_router()`. Same applies to any future literal-path route.

### Bug 2 — `GET /rentals/{unknown_uuid}` returns 500 instead of 404

- **Symptom:** Looking up a non-existent rental ID returns `500 Internal Server Error`.
- **Root cause:** `src/app/presentation/http/rentals/get_rental.py:36` does `raise HTTPException(404)`. The route is wrapped by `ErrorAwareRouter` (from `fastapi_error_map`), which requires every raised exception to be in `error_map`. `HTTPException` isn't mapped → the library raises `RuntimeError: No rule defined for HTTPException` → 500.
- **Fix:** stop raising `HTTPException` from inside an `ErrorAwareRouter`. Raise the existing domain `RentalNotFoundError` (already used by every rental *command* route) and add `RentalNotFoundError: status.HTTP_404_NOT_FOUND` to the route's `error_map`.

### Bug 3 — `/rentals/calendar?month=2026/07` returns 500 instead of 400

- **Symptom:** Any `month` value without a `-` separator crashes the handler.
- **Root cause:** `src/app/presentation/http/rentals/get_rental_calendar.py:43` does `year, month_num = (int(x) for x in request_schema.month.split("-"))`. For `"2026/07"`, `split("-")` returns one element, `int("2026/07")` raises `ValueError`, which `ErrorAwareRouter` doesn't have a rule for.
- **Fix:** validate `month` at the schema layer with a regex (`^\d{4}-\d{2}$`) so FastAPI returns `422` before the handler runs.

## Changes

### `src/app/presentation/http/rentals/router.py`

Move the `extension-requests` include up before the parametric routes:

```diff
     router.include_router(make_list_rentals_router())
+    router.include_router(make_list_pending_extensions_router())
     router.include_router(make_get_rental_router())
     ...
-    router.include_router(make_list_pending_extensions_router())
     router.include_router(make_approve_extension_router())
```

### `src/app/presentation/http/rentals/get_rental.py`

Replace `HTTPException` with `RentalNotFoundError` and map it:

```diff
-from fastapi import APIRouter, HTTPException, status
+from fastapi import APIRouter, status
 from fastapi_error_map import ErrorAwareRouter

+from app.core.commands.exceptions import RentalNotFoundError
 from app.core.queries.get_rental import GetRental, GetRentalRequest
 ...

     @router.get(
         "/{rental_id}",
         error_map={
             AuthenticationError: status.HTTP_401_UNAUTHORIZED,
             ReaderError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
+            RentalNotFoundError: status.HTTP_404_NOT_FOUND,
         },
         ...
     )
     async def get_rental(...) -> RentalQm:
         result = await interactor.execute(GetRentalRequest(rental_id=rental_id))
         if result is None:
-            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rental not found.")
+            raise RentalNotFoundError
         return result
```

### `src/app/presentation/http/rentals/get_rental_calendar.py`

Constrain `CalendarRequestSchema.month`:

```diff
-from pydantic import BaseModel, ConfigDict
+from typing import Annotated as _Annotated
+from pydantic import BaseModel, ConfigDict, StringConstraints

 class CalendarRequestSchema(BaseModel):
     model_config = ConfigDict(frozen=True)
     organization_id: UUID
-    month: str
+    month: _Annotated[str, StringConstraints(pattern=r"^\d{4}-\d{2}$")]
```

## Acceptance

After the fix, re-run the relevant curl cases from `spec/RENTALS_API_TESTING.md`:

- **§3.2** `GET /rentals/00000000-…` → `404` (was `500`).
- **§5.3** `GET /rentals/calendar?month=2026/07` → `422` (was `500`).
- **§14** `GET /rentals/extension-requests?organization_id=…` → `200` (was `422`).
- **§15.1 / §15.2** can now run (they were blocked by §14).

## Non-goals (deliberately out of scope)

- The same `raise HTTPException`-inside-`ErrorAwareRouter` anti-pattern exists in **14 other routes** (`clients/get_client.py`, `payments/get_transaction.py`, `vehicles/get_vehicle.py`, etc.). They all have the same latent 500 bug. We are not fixing them here; they're tracked in `docs/ROADMAP.md` as a separate burndown.
- Renaming the `{rental_id}` path parameter on `approve`/`reject` extension routes (semantically it's the extension-request ID).
- Bumping dev session lifetime from 5 minutes.
