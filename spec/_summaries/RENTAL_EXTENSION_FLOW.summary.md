# Rental Extension Approval Flow — Implementation Summary

- **Spec:** `spec/RENTAL_EXTENSION_FLOW.md`
- **Implemented on:** 2026-06-06
- **Implemented by:** Claude (assisting Almaz)
- **Commit / PR:** _pending — pairs with the HTTPException burndown PR._

## What was done

### 1. `ExtendRental` rewritten — `src/app/core/commands/extend_rental.py`
- Takes a new dependency `ExtensionRequestTxStorage`.
- Loads rental, enforces `status ∈ {CONFIRMED, ACTIVE}` (unchanged).
- Calls `get_pending_for_rental(...)`; if a pending request already exists, raises `PendingExtensionExistsError`.
- Computes `additional_cost = new_estimated_total − rental.estimated_total`.
- Creates an `ExtensionRequest(status=PENDING, ...)` and adds it to storage.
- **No longer mutates** `rental.scheduled_end` or `rental.estimated_total`.

### 2. Route error_map — `src/app/presentation/http/rentals/extend_rental.py`
- Added `PendingExtensionExistsError: status.HTTP_409_CONFLICT`.

### 3. Nullable `reviewed_at` mapping fix — `src/app/infrastructure/persistence_sqla/mappings/extension_request.py`
- The original `composite(UtcDatetime, table.c.reviewed_at)` crashed when the row's `reviewed_at` was NULL because `UtcDatetime.__post_init__` requires a tz-aware datetime. (Latent bug — never tripped before because no rows ever existed.)
- Dropped the composite; mapped `reviewed_at` as a plain column.
- Entity (`src/app/core/common/entities/extension_request.py`) updated: `reviewed_at: UtcDatetime | None` → `datetime | None`.
- Approve/reject handlers (`approve_extension_request.py`, `reject_extension_request.py`) updated to assign `now.value` (`datetime`) instead of `now` (`UtcDatetime`).

## Verification (live curl + direct DB inspection)

| Step | Expected | Got |
|---|---|---|
| Extend a rental at `active` → returns | 204 | **204** ✅ |
| Rental's `scheduled_end` unchanged after extend | yes | **unchanged** ✅ |
| `SELECT count(*) FROM extension_requests WHERE rental_id=…` | 1 | **1** ✅ |
| Listing `/rentals/extension-requests` includes the new pending row | yes | ✅ |
| Second extend on same rental → 409 (`PendingExtensionExistsError`) | 409 | **409** ✅ |
| Approve → DB row becomes `status=approved`, `reviewed_at IS NOT NULL` | yes | ✅ (verified by SQL) |
| Approve → `rental.scheduled_end` shifts to the new date | yes | ✅ (2027-01-05 → 2027-01-08) |
| Approve → `rental.estimated_total` rises by `additional_cost` | yes | ✅ (60000 → 90000) |
| Approve a second time → 409 (`InvalidExtensionRequestStatusError`) | 409 | **409** ✅ |
| HTTP response code of approve/reject | 200 | **503** ⚠️ — see Follow-up #1 |

**The core extension workflow is functionally correct at the data layer.** Data persists correctly; status transitions enforce correctly; idempotency works. The misleading HTTP code on the success path is caused by an unrelated downstream notification bug.

## What was NOT done (and why)

- **The 503 on approve/reject** is caused by `NotificationService.send(user_id=rental.client_id)` — but `notifications.user_id` foreign-keys to `users.id`, and `clients.id` ≠ `users.id` (clients and users are separate tables). The `transaction_manager.commit()` for the ext-request + rental update fires **before** the notification dispatch, so the data is already persisted by the time the FK violation throws. Out of scope for this spec — separate domain bug, tracked below.
- I didn't rename `_nullable_utc_datetime` factory or pursue a generalized fix for nullable composites. The other latent sites (see Follow-up #2) need separate consideration.

## Deviations from the spec

- The spec said the approve/reject handlers needed no changes. In practice, the entity-type change (`UtcDatetime | None` → `datetime | None` for `reviewed_at`) required updating both handlers' assignment (`= now` → `= now.value`). One-line change in each.

## Follow-ups discovered

1. **`notification_service.send(user_id=client_id)` FK violation.** `clients` and `users` are separate tables with separate IDs; the notification table FKs to `users.id`. Either:
   - Notify only when `clients.user_id` is populated (i.e. the client has a paired account), or
   - Change the notification table to FK against a `principal` table that covers both users and clients, or
   - Make `notification.user_id` nullable.
   This bug surfaces on extension approve/reject and likely on *every* rental notification path (overdue, pickup, return). → new spec.

2. **Other nullable timestamp composites are latent bombs.** Same shape as `reviewed_at`. Grep for `composite(UtcDatetime, …)` on columns marked `nullable=True`:
   - `invite.used_at` (`mappings/invite.py:57`)
   - `notification.read_at` (`mappings/notification.py:68`)
   - `device_token.last_active_at` (`mappings/device_token.py:54`)
   - possibly more in rental check-in/check-out timestamps.
   None of them have crashed in tests yet because no NULL rows existed. → new spec / sweep.

3. **Approve/reject path parameter `{rental_id}` is actually an extension-request ID.** Still on the ROADMAP from the earlier rentals fix.

## Files changed

```
src/app/core/commands/extend_rental.py                                  rewritten
src/app/presentation/http/rentals/extend_rental.py                      ±5  (error_map entry)
src/app/infrastructure/persistence_sqla/mappings/extension_request.py   ±2  (drop composite for reviewed_at)
src/app/core/common/entities/extension_request.py                       ±2  (reviewed_at type)
src/app/core/commands/approve_extension_request.py                      ±2  (now → now.value)
src/app/core/commands/reject_extension_request.py                       ±1  (now → now.value)
spec/RENTAL_EXTENSION_FLOW.md                                           new
spec/_summaries/RENTAL_EXTENSION_FLOW.summary.md                        new
```
