# Signup Hardening — Implementation Summary

- **Spec:** `spec/SIGNUP_HARDENING.md`
- **Implemented on:** 2026-06-06
- **Implemented by:** Claude (assisting Almaz)
- **Commit / PR:** _pending — bundles with the rentals + notification work._

## What was done

All seven items from the spec landed, plus one pre-existing bug discovered during verification (the signup endpoint had never actually worked end-to-end).

### 1. Request body slimmed
- Dropped `organization_id` (server uses `APP_DEFAULT_ORGANIZATION_ID` or the invite's org).
- Dropped `role` (server picks CLIENT for non-invite signups, invite carries the role otherwise).
- Body is now: `{email, password, first_name, last_name, phone?, invite_token?}`.

### 2. Default role = CLIENT (was INVESTOR)
- Non-invite signup unconditionally creates a `UserRole.CLIENT`.

### 3. Email-before-commit
- Old order: `commit → send_email` (SMTP failure left a half-committed user behind).
- New order: `flush user + client + verification_code → send_email → commit primary → commit auth`.
- If SMTP fails: no commit on either session → PG rolls back → next attempt with the same email is **NOT** blocked by `EmailAlreadyExistsError`.

### 4. Reused `invite` object
- `_resolve_invite` now returns `(organization_id, role, invite)` so the same instance is mutated for `invite.used_at = now`. Removed the post-flush re-query.

### 5. Fixed the "already authenticated" check
- Was `try/get_current_user; raise AlreadyAuth; except AuthenticationError` (let `AuthorizationError` from a stale session fall through as a misleading 403).
- Now `try/get_current_user; except (AuthenticationError, AuthorizationError): pass; else: raise AlreadyAuthenticatedError` — stale sessions are treated like no session and signup is allowed.

### 6. Password-strength check
- No change — `RawPassword` value object handles validation; user explicitly accepted that scope.

### 7. Debug log removed
- The `logger.debug("Verification code for %s: %s", email.value, code)` line is gone. The code is observable via the `email_verification_codes` table when needed.

### Bonus (uncovered during verification): cross-session circular-FK fix
- The previous handler wrote the user via `AuthSqlaUserTxStorage` (auth session) and the client via `ClientTxStorage` (primary session). Two PG connections, two transactions — neither could see the other's uncommitted rows.
- Compounding that: `clients.user_id ↔ users.client_id` is a **circular FK pair**, both `ON DELETE SET NULL`, **neither deferrable**. So even within one session, the inserts couldn't be done in either order without a violation.
- Fix:
  - Switched the user write to the **primary** `UserTxStorage` so user + client are in the same transaction.
  - Inserted user with `client_id=None`, then flushed.
  - Inserted client referencing user, flushed.
  - Set `user.client_id = client_id`, flushed (UPDATE).
- The handler now commits the **primary** session first (so the user row is visible) then the **auth** session (so the verification-code FK can see the user). Both commits live in the new handler; `AuthSqlaTransactionManager` is now injected alongside the primary one.

## Verification (live curl + DB)

| Case | Expected | Got |
|---|---|---|
| `POST /signup` no invite, valid body, placeholder SMTP | 503, 0 user rows, 0 client rows | **503, 0 / 0** ✅ |
| Same payload retried with same email | 503 (NOT 409 EmailAlreadyExists) | **503** ✅ |
| Payload includes deprecated `organization_id` and `role` | extra fields silently ignored (no 422) | **silently ignored** ✅ |
| Log trace on failure | `EmailSendError — Failed to send email...` (not `IntegrityError`) | **EmailSendError** ✅ — FK chain works, only SMTP fails |
| Log no longer prints the verification code at DEBUG | absent | **absent** ✅ |

**Happy-path with verified email delivery is not testable in this environment** (the dev `.env` ships placeholder Gmail credentials that fail with `SMTPAuthenticationError (535)`). Structurally the flow is correct — the only remaining failure surface is SMTP itself. To exercise it locally, point `SMTP_*` env vars at a real SMTP relay or run a local mailhog container.

## What was NOT done (and why)

- **Did not migrate the FK pair to `DEFERRABLE INITIALLY DEFERRED`.** Code-level UPDATE pattern unblocks signup today without a DB migration. Migration is the right long-term fix but out of scope here; tracked below.
- **Did not refactor away the dual-session design.** The two-session split (primary vs. auth) is still in place for other endpoints. Signup is now the only place that bridges them; further consolidation is a separate cleanup.
- **Did not unify the verification-code storage onto the primary session.** It still lives on the auth session and is committed by `auth_transaction_manager`. Moving it to primary would simplify the handler further but is not blocking.

## Deviations from the spec

- The spec didn't anticipate the cross-session FK problem; it surfaced during verification and required injecting `AuthSqlaTransactionManager` plus an UPDATE pattern. Otherwise no deviations.

## Follow-ups

1. **Migration: make `fk_users_client_id_clients` (or both circular FKs) `DEFERRABLE INITIALLY DEFERRED`.** Removes the need for the three-flush UPDATE dance and makes any future code-path touching this pair simpler. → new spec.
2. **`make_account_router` doesn't expose the `default-organization` endpoint description in a way the frontend can rely on long-term.** Mention in `docs/API.md`. → small docs PR.
3. **`(organization_id, phone)` UNIQUE constraint on `clients` collides on empty strings** — every client without a phone competes for the same `("", org)` slot. Probably should be `(organization_id, NULLIF(phone, ''))` or a partial unique index. Surfaced during early debugging of this spec. → ROADMAP.
4. **Switch dev SMTP to a local fake server (e.g. mailhog) and document in `.claude/skills/local-dev.md`** so signup happy-path can be exercised without a real Gmail account. → ROADMAP.
5. **Schema cleanup: `users.client_id` is essentially a back-reference of `clients.user_id`.** Long-term, drop one of the two columns (likely `users.client_id`) and rely on the reverse lookup. → ROADMAP.

## Files changed

```
src/app/infrastructure/auth_ctx/handlers/sign_up.py          rewritten (7 hardening items + cycle-break)
spec/SIGNUP_HARDENING.md                                     new
spec/_summaries/SIGNUP_HARDENING.summary.md                  new
```

No other files touched. No DI changes (both `AuthSqlaTransactionManager` and `UserTxStorage` are already registered).
