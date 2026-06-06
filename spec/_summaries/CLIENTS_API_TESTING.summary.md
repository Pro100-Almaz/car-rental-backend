# Clients API Testing — Implementation Summary

- **Spec:** `spec/CLIENTS_API_TESTING.md`
- **Implemented on:** 2026-06-06
- **Implemented by:** Claude (assisting Almaz)
- **Commit / PR:** _pending — test-only, no production code changes._

## What was done

Executed the full curl plan against the live local stack (post-migrations from `USER_CLIENT_LINK_CLEANUP` and `CLIENT_PHONE_PARTIAL_UNIQUE`). All 21 cases passed first attempt.

## Result matrix

| § | Case | Expected | Got |
|---|---|---|---|
| 1.1 | minimal create | 201 | **201** ✅ |
| 1.2 | missing required field | 422 | **422** ✅ |
| 1.3 | unauthenticated | 401 | **401** ✅ |
| 1.4 | duplicate non-empty phone in same org | 503 | **503** ✅ |
| 2.1 | list by org | 200 | **200** ✅ |
| 2.2 | filter `verification_status=pending` | 200 | **200** ✅ |
| 2.3 | filter `is_blacklisted=false` | 200 | **200** ✅ |
| 2.4 | search by name | 200 | **200** ✅ |
| 3.1 | get existing | 200 | **200** ✅ |
| 3.2 | get unknown UUID | 404 | **404** ✅ (HTTPException burndown holds) |
| 4.1 | PATCH first_name | 204, value updated | **204, "Renamed"** ✅ |
| 4.2 | PATCH unknown id | 404 | **404** ✅ |
| 5.1 | verify → status=verified | 204, status flipped | **204, "verified"** ✅ |
| 5.2 | invalid enum value | 422 | **422** ✅ |
| 5.3 | verify unknown id | 404 | **404** ✅ |
| 6.1 | blacklist with reason | 204, flag flips, reason persists | **204, true / "fraud attempt"** ✅ |
| 6.2 | unblacklist (DELETE) | 204, flag clears | **204, false** ✅ |
| 6.3 | blacklist missing reason | 422 | **422** ✅ |
| 7.1 | client → rentals subresource | 200 | **200** ✅ |
| 8.1 | client → payments subresource | 200 | **200** ✅ |
| 9.1 | reminder to client without `user_id` | 404 | **404** ✅ (`SendDebtReminder` hard-fails when client has no linked user) |
| 9.2 | reminder to a signup-originated client (has `user_id`) | 200, notification row created | **200, 1 row in `notifications`** ✅ |

## Cross-spec confirmations

- **`HTTPEXCEPTION_BURNDOWN`** held — §3.2 returns 404 (was 500 before that fix).
- **`CLIENT_PHONE_PARTIAL_UNIQUE`** held — §1.4 still 503 on duplicate non-empty phone, and earlier signup tests showed phoneless coexistence works.
- **`NOTIFICATION_CLIENT_FK_FIX`** held — §9.2 produced a real `notifications` row without FK violation. §9.1's 404 (instead of silent skip) is the expected difference: `SendDebtReminder` is the only caller that **hard-fails** when `client.user_id` is missing, by design.
- **`USER_CLIENT_LINK_CLEANUP`** held — no regressions; client lookups now go through `clients.user_id`.

## What was NOT done (and why)

- Did not exercise the **rentals subresource** beyond confirming it returns 200 — the rentals test plan already covers list-rentals filtering by client.
- Did not stress-test the **search** filter beyond a single match. Substring matching across name/phone/email is a small, easy follow-up.
- No tear-down of fixture data. The test creates one client per run; rerunning is idempotent via the `$$` suffix on phone/iin.

## Deviations from the spec

None.

## Follow-ups discovered

- **`SendDebtReminder` returns a generic `ClientNotFoundError` for the "no linked user account" case.** Better UX would be a distinct error like `ClientHasNoUserAccountError → 409`. Tiny ergonomic improvement; the current 404 is defensible. → ROADMAP.
- **Filter on `is_blacklisted` accepts query-string `true/false` and parses correctly** — worth a doc note in `docs/API.md` since Pydantic-via-Depends behavior here isn't obvious.

## Files changed

```
spec/CLIENTS_API_TESTING.md                        new
spec/_summaries/CLIENTS_API_TESTING.summary.md     new
```

No production code touched.
