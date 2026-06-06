# Notification Client→User FK Fix — Implementation Summary

- **Spec:** `spec/NOTIFICATION_CLIENT_FK_FIX.md`
- **Implemented on:** 2026-06-06
- **Implemented by:** Claude (assisting Almaz)
- **Commit / PR:** _pending — pairs naturally with the rental-extension flow fix._

## What was done

### 1. New method `NotificationService.send_to_client(...)` — `src/app/core/common/services/notification_service.py`

- Resolves `clients.user_id` via the newly injected `ClientTxStorage`.
- If client missing OR `client.user_id is None`: logs at INFO and returns (no DB write, no FK violation).
- Otherwise delegates to the existing `send(user_id=client.user_id, ...)` path.

### 2. Five callers switched from `send(user_id=client_id)` → `send_to_client(client_id=…)`

| File | Old | New |
|---|---|---|
| `core/commands/approve_extension_request.py` | `send(user_id=rental.client_id, …)` | `send_to_client(client_id=rental.client_id, …)` |
| `core/commands/reject_extension_request.py` | `send(user_id=user_id, …)` | `send_to_client(client_id=client_id, …)` (variable renamed) |
| `core/commands/check_overdue_rentals.py` | `send(user_id=rental["client_id"], …)` | `send_to_client(client_id=rental["client_id"], …)` |
| `core/commands/check_pickup_reminders.py` | same shape | same shape |
| `core/commands/check_return_reminders.py` | same shape | same shape |

### 3. `send_debt_reminder.py` left alone

This caller was already correct — it loads the client itself, raises `ClientNotFoundError` if `client.user_id` is None, and then calls `send(user_id=client.user_id, …)`. Different policy (hard-fail vs silent-skip) but the right shape. Documented in summary; not refactored.

### 4. DI

No IoC changes needed — `ClientTxStorage` was already provided in `app/main/ioc/core.py:309`. Dishka picks it up automatically through the new constructor parameter.

## Verification (live curl + DB)

| Step | Expected | Got |
|---|---|---|
| Extend an active rental whose client has no paired user | 204 | **204** ✅ |
| Approve the resulting pending request | 200 (was 503) | **200** ✅ |
| DB: ext request row is `status=approved`, `reviewed_at IS NOT NULL` | yes | **yes** ✅ |
| App log emits `"Notification skipped: client … has no paired user account."` | yes | **yes** ✅ |
| App log emits ForeignKeyViolation | no | **none** ✅ |
| Reject another pending request | 200 (was 503) | **200** ✅ |
| DB: ext request row is `status=rejected`, `rejection_reason="vehicle reserved"` | yes | **yes** ✅ |

## What was NOT done (and why)

- **No schema change** to `notifications.user_id` (still FKs to `users.id`, still NOT NULL). The resolve-or-skip approach keeps the invariant — a notification row only exists when there's a real `users.id` to point at.
- **No back-fill** of `clients.user_id` for existing clients. Clients without app accounts simply don't get in-app notifications; once they sign up via mobile, future notifications will route to them.
- **No alternate delivery channels** (SMS/email/push-to-unregistered-device) for clients without user accounts. Out of scope here.

## Deviations from the spec

- Spec listed 6 broken callers; actually 5. `send_debt_reminder.py` resolves `client.user_id` itself and was already correct (it hard-fails with `ClientNotFoundError` when the client has no user, rather than silently skipping). Kept as-is; noted above.

## Follow-ups

- **Inconsistency between `send_debt_reminder` (hard-fail) and `send_to_client` (silent skip).** Both are defensible policies but the project should pick one and apply uniformly. Recommendation: keep `send_debt_reminder`'s hard-fail (the user is explicitly invoking a "send reminder" action — silence would be surprising), and keep silent-skip in `send_to_client` (used for system-generated reminders where a missing user account is expected). Document this in a short note when the notifications doc gets written. → ROADMAP.
- **`send_to_client` does one extra DB round-trip** to fetch the client. For high-volume reminder runs (`CheckOverdueRentals` etc.) this matters. Future optimisation: have `RentalReader.list_*` queries return `client.user_id` already joined, then pass `user_id` directly. Out of scope for this fix.

## Files changed

```
src/app/core/common/services/notification_service.py        +44 / -1   (new send_to_client + ClientTxStorage dep)
src/app/core/commands/approve_extension_request.py          ±2
src/app/core/commands/reject_extension_request.py           ±10  (variable renamed for clarity)
src/app/core/commands/check_overdue_rentals.py              ±2
src/app/core/commands/check_pickup_reminders.py             ±2
src/app/core/commands/check_return_reminders.py             ±2
spec/NOTIFICATION_CLIENT_FK_FIX.md                          new
spec/_summaries/NOTIFICATION_CLIENT_FK_FIX.summary.md       new
```
