# Notification FK Mismatch — Client → User Resolution

> Surfaced by `RENTAL_EXTENSION_FLOW` verification. Six commands call `NotificationService.send(user_id=rental.client_id)`, but `notifications.user_id` foreign-keys to `users.id` and `clients.id ≠ users.id`. Every such call dies with a `ForeignKeyViolation` and returns 503 (data may already be committed → confusing UX).
>
> Estimated effort: **~30 min**.
> Risk: **Low** — additive method on `NotificationService` + 6 call-site renames + 1 DI dependency added; no schema migration.

## Schema reality

```
clients ───┐                    notifications
           │                    user_id ──► users.id  (FK, NOT NULL)
           ▼ user_id (nullable)
         users
```

A `Client` may or may not have a paired user account (`clients.user_id` is nullable). The current code treats `client_id` as if it were a `user_id` — wrong type.

## Affected call sites (6)

| File | Line | What it passes |
|---|---|---|
| `core/commands/approve_extension_request.py` | 85 | `rental.client_id` |
| `core/commands/reject_extension_request.py` | 78 | `rental.client_id` (or `ext_req.client_id`) |
| `core/commands/check_overdue_rentals.py` | 36 | `rental["client_id"]` |
| `core/commands/check_return_reminders.py` | 38 | `rental["client_id"]` |
| `core/commands/check_pickup_reminders.py` | 38 | `rental["client_id"]` |
| `core/commands/send_debt_reminder.py` | 56 | `client.id_` (also a clients.id) |

## Design

Add a new method `send_to_client(*, client_id, organization_id, type_, ...)` on `NotificationService`. It:

1. Loads the client via the (newly injected) `ClientTxStorage`.
2. If client is `None` **or** `client.user_id is None` → log at INFO and return (no notification — no FK to violate).
3. Otherwise delegate to the existing `send(user_id=client.user_id, ...)`.

The existing `send()` method stays untouched — it remains the right entry point when callers genuinely have a `users.id` (e.g. staff notifications, audit messages).

Each of the 6 client-side callers switches from `send(user_id=<client_id>, ...)` to `send_to_client(client_id=<client_id>, ...)`.

`NotificationService.__init__` gains a `ClientTxStorage` dependency. Dishka already provides both — no new IoC bindings needed.

## Acceptance

- `POST /rentals/{ext_id}/extension/approve` against an extension whose client has **no paired user** → returns **200**, no notification row inserted, no FK violation in logs.
- Same path against a client **with** `clients.user_id IS NOT NULL` → returns **200**, notification row exists in `notifications` table.
- `POST /rentals/{ext_id}/extension/reject` behaves the same way.
- Logs at INFO level when notification is skipped (so it's observable).
- No regression on any other route — `make lint-check` (ruff portion) stays clean over the changed files.

## Non-goals

- Backfilling `clients.user_id` for existing clients.
- Notifying via email/SMS when a client has no app account — that's a future feature.
- Schema change to make `notifications.user_id` nullable — keeps the FK invariant; the resolve-or-skip approach is cleaner.
