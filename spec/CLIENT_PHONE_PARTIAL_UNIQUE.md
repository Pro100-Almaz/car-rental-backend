# Clients — Partial-Unique Index on Phone

> `idx_clients_phone` is currently a full unique index on `(organization_id, phone)`. Because `phone` is `NOT NULL` and signups default to `""` when no phone is provided, every phoneless signup competes for the same `("", default_org)` slot — so the second one fails with `IntegrityError`. Switch the index to a partial unique that only enforces uniqueness when phone is non-empty.
>
> Estimated effort: **~10 min**.
> Risk: **Very low** — index swap only. No code touched. Behaviour change: multiple phoneless clients in one org are now allowed.

## Today vs. after

| | Today | After |
|---|---|---|
| Index | `UNIQUE (organization_id, phone)` | `UNIQUE (organization_id, phone) WHERE phone <> ''` |
| Insert client A `phone=""` in org X | OK | OK |
| Insert client B `phone=""` in org X | **IntegrityError** | OK |
| Insert client A `phone="+777..."` then B `phone="+777..."` in org X | IntegrityError | IntegrityError (unchanged) |
| Insert same phone across two orgs | OK (unchanged) | OK (unchanged) |

## Changes

### Migration (`d8r8o8p8d8u8`, `2026-06-06_020000_clients_phone_partial_unique.py`)

- `op.drop_index("idx_clients_phone", table_name="clients")`
- `op.create_index("idx_clients_phone", "clients", ["organization_id", "phone"], unique=True, postgresql_where=sa.text("phone <> ''"))`
- Down: reverse — restore the full unique.

No mapping or code changes — the index is declared only in alembic, not in `mappings/client.py`. New installations get the partial variant via this migration chain.

## Acceptance

- After `alembic upgrade head`, `\d clients` shows `idx_clients_phone` with `WHERE phone <> ''`.
- Two consecutive signups in the same org with no phone → both succeed (204 / 204).
- Two consecutive signups in the same org with the same non-empty phone → second one fails (503 with `Database constraint violation`). Unchanged.
- `alembic downgrade -1` restores the original full unique index.

## Non-goals

- Changing `clients.phone` to nullable. Could be a future cleanup but every caller would need to handle `None`; partial unique gets the same effect with one index swap.
- Touching any other "(org_id, scalar)" unique that may have the same shape (e.g. `clients.iin`). Out of scope.
