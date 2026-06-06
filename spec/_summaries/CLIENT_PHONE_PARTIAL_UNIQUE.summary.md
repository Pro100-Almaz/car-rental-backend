# Clients Phone Partial-Unique — Implementation Summary

- **Spec:** `spec/CLIENT_PHONE_PARTIAL_UNIQUE.md`
- **Implemented on:** 2026-06-06
- **Implemented by:** Claude (assisting Almaz)
- **Commit / PR:** _pending — pairs naturally with the user/client cleanup migration._

## What was done

Single migration `d8r8o8p8d8u8` (`2026-06-06_020000_clients_phone_partial_unique.py`):

- `DROP INDEX idx_clients_phone`
- `CREATE UNIQUE INDEX idx_clients_phone ON clients (organization_id, phone) WHERE phone <> ''`

No code touched. The index lives only in alembic; nothing in `mappings/client.py` referenced it.

## Verification (live curl)

| Case | Expected | Got |
|---|---|---|
| Signup A with no phone | 204 | **204** ✅ |
| Signup B with no phone, same org (was 503 before) | 204 | **204** ✅ |
| Signup C with phone `+77099930165` | 204 | **204** ✅ |
| Signup D with same phone, same org | 503 (collide — unchanged) | **503** ✅ |
| `pg_indexes` shows partial predicate `WHERE (phone)::text <> ''::text` | yes | **yes** ✅ |

Net behavior: multiple phoneless clients in one org now coexist, while real phone uniqueness within an org is still enforced.

## What was NOT done

- Did not change `clients.phone` to nullable. Future cleanup option; not needed for this fix.
- Did not touch `clients.iin` (the national-id column) which may have a similar "empty collides" issue. Out of scope; tracked.

## Deviations from the spec

None.

## Follow-ups

- **`clients.iin` may have the same problem** if it has a `(org_id, iin)` unique on a string default of `""`. Worth a quick check next time the `clients` table is touched.
- Long-term: turn `phone` and `iin` into proper `str | None` columns and stop using empty-string sentinels.

## Files changed

```
src/app/infrastructure/persistence_sqla/alembic/versions/2026-06-06_020000_clients_phone_partial_unique.py   new
spec/CLIENT_PHONE_PARTIAL_UNIQUE.md                                                                          new
spec/_summaries/CLIENT_PHONE_PARTIAL_UNIQUE.summary.md                                                       new
```
