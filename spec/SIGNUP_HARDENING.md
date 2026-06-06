# Signup Hardening

> Seven targeted fixes to `POST /api/v1/account/signup/` and its handler. Bundled into one PR because they all touch the same file.
>
> Estimated effort: **~30 min**.
> Risk: **Medium for API contract (request body shrinks — breaking change for any existing caller)**; Low for behaviour internals.

## Changes

### 1. Drop `organization_id` and `role` from the request body
- Org id comes from invite (when `invite_token` provided) or from the platform's `DEFAULT_ORGANIZATION_ID` env var (exposed at `GET /account/default-organization/`).
- Role comes from invite when provided; otherwise defaults to **CLIENT** (was INVESTOR — the previous behaviour was almost certainly accidental).
- Mobile self-signup is the only entry point. Web/manager creates accounts via separate admin endpoints.

### 2. Default role = CLIENT
- Today: `UserRole.CLIENT if request.role == "client" else UserRole.INVESTOR` (line 169).
- After: non-invite signup is always `UserRole.CLIENT`.

### 3. Email-before-commit
- Currently: commit → send email. If SMTP fails, user row is persisted with `email_verified=False` and the user must call `/resend-verification/`.
- New order: flush → mark invite used → add verification code → **send email** → commit. If SMTP raises, the request raises 503; no commit happens; PG rolls back. Next attempt with the same email isn't blocked by a `unique(email)` violation because nothing was persisted.

### 4. Reuse the `invite` object from `_resolve_invite`
- Today: line 206 re-queries the invite after the flush to mark it used.
- After: `_resolve_invite` returns `(organization_id, role, invite)`; the caller uses the same instance for `invite.used_at = now`.

### 5. Fix the "already authenticated" check
- Today (inverted try/except, only catches `AuthenticationError` — `AuthorizationError` from a stale session falls through as 403):
  ```python
  try:
      await self._current_user_service.get_current_user()
      raise AlreadyAuthenticatedError
  except AuthenticationError:
      pass
  ```
- After:
  ```python
  try:
      await self._current_user_service.get_current_user()
  except (AuthenticationError, AuthorizationError):
      pass  # no valid session, signup is allowed
  else:
      raise AlreadyAuthenticatedError
  ```
- Effect: a stale session (session id present but user record missing) no longer blocks signup with a misleading 403; it's treated the same as no session.

### 6. Password-strength check
- No change — `RawPassword` value object handles validation today and the user is comfortable with that scope.

### 7. Remove the DEBUG log of the verification code
- `logger.debug("Verification code for %s: %s", email.value, code)` on line 221 is removed. The code is observable from the `email_verification_codes` table when needed.

## Request body — before vs after

```python
# BEFORE
class SignUpRequest:
    email: str
    password: str
    first_name: str
    last_name: str
    phone: str | None = None
    organization_id: UUID | None = None    # ← dropped
    invite_token: str | None = None
    role: str | None = None                 # ← dropped

# AFTER
class SignUpRequest:
    email: str
    password: str
    first_name: str
    last_name: str
    phone: str | None = None
    invite_token: str | None = None
```

## Acceptance

- `POST /signup/` with `{email, password, first_name, last_name}` (no invite, no org id) → **204**.
  - DB: one user row with `role=client`, `organization_id == APP_DEFAULT_ORGANIZATION_ID`, paired `clients` row exists.
- `POST /signup/` with the same email when `DEFAULT_ORGANIZATION_ID` is unset → **400** (OrganizationIdRequiredError).
- `POST /signup/` with `invite_token` for an INVESTOR invite → **204**, user role = `investor`, org from invite.
- Simulate an SMTP failure (e.g. wrong SMTP host in `.secrets`, restart) → **503**, and `SELECT count(*) FROM users WHERE email=…` returns 0. A subsequent retry with valid SMTP succeeds — no "email already exists" error.
- `logger.debug` no longer prints the verification code; same code does land in `email_verification_codes.code`.
- No regression on the existing happy path documented in `spec/RENTALS_API_TESTING.md` (login still works, etc.).

## Non-goals

- Multi-tenant signup picker (frontend already calls `/default-organization/` once and either shows or hides the picker).
- Email-already-verified handling for re-signup attempts on a verified email.
- Password-strength validation beyond what `RawPassword` already does.
