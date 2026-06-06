# User ↔ Client Back-Reference Cleanup

> `users.client_id` and `clients.user_id` encode the same relationship from opposite ends. Drop the `users` side so the user/client link is one-directional. Side-effects: signup loses the cycle-break, the schema loses a column, and a couple of mobile handlers switch from `current_user.client_id` to a new `get_by_user_id` lookup.
>
> Estimated effort: **~45 min**.
> Risk: **Medium** — touches a column with a unique constraint + 3 callers + 1 migration. All changes ship in one PR.

## The redundancy

```
users.client_id  ──► clients.id     (this gets dropped)
clients.user_id  ──► users.id       (this stays — the only edge now)
```

After this spec, finding "the client record for a user" is `clients WHERE user_id = $user_id`, not a back-reference column. SQLA query, one indexed lookup.

## Changes

### 1. DB migration — `src/app/infrastructure/persistence_sqla/alembic/versions/2026-06-06_010000_drop_users_client_id.py`

- `op.drop_constraint("uq_users_client_id", "users", type_="unique")`
- `op.drop_constraint("fk_users_client_id_clients", "users", type_="foreignkey")`
- `op.drop_column("users", "client_id")`
- Down: re-add column + constraint + FK (no data restore — empty column on downgrade).

Migration ID: pick something readable like `drop_users_client_id`; revises the current head (`m6u6l6t6i6o6`).

### 2. `User` entity — `src/app/core/common/entities/user.py`

- Drop `client_id: ClientId | None` constructor parameter.
- Drop `self.client_id = client_id` assignment.

### 3. SQLA mapping — `src/app/infrastructure/persistence_sqla/mappings/user.py`

- Drop the `Column("client_id", ...)` from `users_table`.
- Drop `"client_id": users_table.c.client_id` from the properties dict.

### 4. `UserService` — `src/app/core/common/services/user.py`

- Drop `client_id` parameter from `create_user(...)` and `create_user_with_raw_password(...)`.
- Drop the corresponding `client_id=client_id` kwarg from `User(...)` construction.

### 5. `ClientTxStorage` port — `src/app/core/commands/ports/client_tx_storage.py`

Add a method:

```python
async def get_by_user_id(
    self,
    user_id: UserId,
    *,
    for_update: bool = False,
) -> Client | None: ...
```

### 6. SQLA adapter — `src/app/infrastructure/adapters/sqla_client_tx_storage.py`

Implement `get_by_user_id` via `select(Client).where(clients_table.c.user_id == user_id)`.

### 7. Callers — replace `current_user.client_id` lookups with `client_tx_storage.get_by_user_id(current_user.id_)`

- `src/app/core/commands/submit_booking_request.py` — lines 131, 159.
- `src/app/core/commands/cancel_own_rental.py` — line 54.

Both already inject `ClientTxStorage`, so this is a method swap.

### 8. Signup handler — `src/app/infrastructure/auth_ctx/handlers/sign_up.py`

- Drop the `user.client_id = client_id; await flusher.flush()` cycle-break at the end.
- `client_id=None` argument to `create_user_with_raw_password` becomes simply omitted (since the param is gone).
- The handler then becomes: flush user → flush client → email → commit primary → commit auth. Two flushes, not three.

## Acceptance

- `alembic upgrade head` runs cleanly; the column is gone (`\d users` shows no `client_id`).
- `alembic downgrade -1` restores the column (smoke: just verify it adds; data loss is documented and expected).
- Happy-path signup → verify-email → login still returns 204/204/204 (live curl).
- Mobile booking — `POST /api/v1/mobile/rentals/book` against a signed-up client — still works (handler now resolves client via `get_by_user_id`).
- Direct DB check: `SELECT * FROM users` shows no `client_id` column.

## Non-goals

- Touching `clients.user_id` (the surviving edge).
- Migrating existing prod data — the column drop is destructive for that one redundant field; the canonical link in `clients.user_id` is untouched.
- Renaming the `uq_clients_user_id` constraint or relaxing the "one user → one client" invariant (it stays).
