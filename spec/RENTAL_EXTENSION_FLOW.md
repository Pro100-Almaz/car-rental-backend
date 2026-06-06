# Rental Extension Approval Flow

> Surfaced by the rentals testing pass — `POST /rentals/{id}/extend` mutates the rental's `scheduled_end` directly, never creating an `extension_requests` row. The `approve` and `reject` endpoints therefore operate on data that never gets created.
>
> Estimated effort: **~30 min**.
> Risk: **Low–Medium** — changes the semantics of `/extend` (it no longer instantly shifts the rental's dates), but every approve/reject endpoint and the listing endpoint are already coded to the new behaviour.

## Current vs. intended behaviour

| Step | Current (broken) | Intended |
|---|---|---|
| Client `POST /rentals/{id}/extend` | Mutates `rentals.scheduled_end` + `estimated_total` instantly | Inserts `extension_requests` row with status `pending`; rental unchanged |
| Manager `GET /rentals/extension-requests` | Always returns `{items:[]}` (no rows ever created) | Lists pending requests |
| Manager `POST /rentals/{ext_id}/extension/approve` | Looks up an `ExtensionRequest`, raises 404 | Sets request → `approved` AND shifts rental dates |
| Manager `POST /rentals/{ext_id}/extension/reject` | Same as approve — 404 | Sets request → `rejected` with reason |

The approve/reject handlers are already coded correctly — they expect a `pending` row to act on. The only broken piece is `ExtendRental.execute()`.

## Building blocks (already exist)

| Piece | Path |
|---|---|
| `ExtensionRequest` entity | `src/app/core/common/entities/extension_request.py` |
| `ExtensionRequestTxStorage` port | `src/app/core/commands/ports/extension_request_tx_storage.py` (`add`, `get_by_id`, `get_pending_for_rental`) |
| `create_extension_request_id()` factory | `src/app/core/common/factories/id_factory.py:116` |
| `ExtensionRequestStatus` enum | `src/app/core/common/entities/types_.py:258` (`PENDING`/`APPROVED`/`REJECTED`) |
| `PendingExtensionExistsError` | `src/app/core/commands/exceptions.py:110` |
| SQLA adapter | already wired (approve/reject use it successfully against the same DB) |

So the fix is **purely a rewrite of `ExtendRental.execute()`**.

## Changes

### `src/app/core/commands/extend_rental.py`

Rewrite the handler:

1. Resolve current user, authorize (`rental.update`).
2. Load the rental.
3. Reject if rental status is not in `{CONFIRMED, ACTIVE}` (unchanged from today).
4. Check `extension_request_tx_storage.get_pending_for_rental(rental.id_)` — if non-`None`, raise `PendingExtensionExistsError`.
5. Compute `additional_cost = request.new_estimated_total - rental.estimated_total`.
6. Construct `ExtensionRequest(status=PENDING, ...)`.
7. `extension_request_tx_storage.add(...)`.
8. Commit.
9. Do NOT touch `rental.scheduled_end` or `rental.estimated_total`.

Constructor gains `extension_request_tx_storage: ExtensionRequestTxStorage`.

### `src/app/main/ioc/core.py`

The DI container already provides `ExtensionRequestTxStorage` (approve/reject consume it). No new binding needed — the `provide(ExtendRental)` line will resolve the new dependency through the existing tree automatically.

## Acceptance

End-to-end via curl:

1. Create rental, confirm, check-in → status=`active`.
2. `POST /rentals/{id}/extend` with new dates → **204**.
3. Verify in DB: `SELECT * FROM extension_requests WHERE rental_id = …` returns **1 row** with status `pending`.
4. Verify rental's `scheduled_end` is **unchanged** (still the original date).
5. `GET /rentals/extension-requests?organization_id=…` → contains the new row.
6. `POST /rentals/{ext_id}/extension/approve` → **200**.
7. Verify rental's `scheduled_end` now **matches** the requested new date.
8. Re-attempt step 2 on the same rental while a pending request exists → **409** (PendingExtensionExistsError → map to 409).

## Non-goals

- Notifications / push on extend creation (extension already covered on approve/reject paths).
- Auto-approval logic.
- Migration to a separate `ApproveExtensionRequest` endpoint name (path uses `{rental_id}` placeholder but really takes ext-request ID — still tracked as a follow-up).
