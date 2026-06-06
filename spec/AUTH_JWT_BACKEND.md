# JWT Auth Backend — Access + Refresh Tokens, No Cookies

> Replace the cookie-based rolling-session model in `AuthService` with stateless JWT access tokens and DB-tracked refresh tokens, delivered in JSON request/response bodies. Bake in rate limiting, brute-force protection, and refresh-token reuse detection so the new endpoints are not a soft target for credential stuffing or DDoS.
>
> Estimated effort: **~2 days** (one focused PR, plus follow-up PRs for rate-limiter ops tuning and CORS lockdown).
> Risk: **High** — every authenticated route changes its credential source. Cookie path is removed in the same release after both clients ship. Mistakes here are security incidents, not bugs.
>
> Supersedes the rolling-cookie behaviour in `src/app/infrastructure/auth_ctx/service.py`. Builds on the hardened signup contract in `spec/SIGNUP_HARDENING.md`.

## Why

Today's auth is a single short-lived session row keyed by a `sid` JWT claim, written to a `Set-Cookie` header that the browser sends back on every request. `AuthService.get_current_user_id` extends `expiration` and re-issues the cookie when the session is within 20% of its TTL (`AuthSessionUtcTimer.needs_refresh`). This works for the browser. It does not work for mobile, which has no cookie jar to roll on every response and which the user is now building.

The chosen direction: the server returns `{access_token, refresh_token}` in the login response body. The client sends `Authorization: Bearer <access>` on every API call. When the access token expires, the client posts the refresh token to `/account/refresh/` and gets a new pair. This is the standard mobile pattern, works equally well for the web SPA, and removes the cookie dependency entirely.

The user explicitly raised DDoS concerns: this spec also pins rate-limiting and lockout policy on the auth endpoints. Without those, `/login/` and `/forgot-password/` are free targets.

## Token model

Two tokens. They have different jobs and different lifetimes.

### Access token — short, stateless, JWT

- **Algorithm**: HS256. The backend is a single-tenant monolith; there is no third party that needs to verify these. RS256 buys nothing here and costs key-pair ops. Reconsider if/when a second service needs to validate tokens it did not mint.
- **TTL**: **15 minutes**. Long enough that a user does not feel the refresh hop; short enough that a leaked access token has a small blast radius. Today's 5-minute TTL exists to compensate for the rolling-cookie design and is painful for testing; 15 minutes is the prod default.
- **Storage**: stateless. We do **not** look it up in the DB on every request. The `jti` claim is recorded so we can blacklist on logout (see "Access revocation"), but the common path is signature + `exp` check only.
- **Claims**:
  ```json
  {
    "sub": "<user_uuid>",
    "typ": "access",
    "jti": "<token_uuid>",
    "iat": 1717689600,
    "exp": 1717690500,
    "iss": "car-rental-backend",
    "aud": "car-rental-clients"
  }
  ```
  - `sub` is the `users.id` UUID.
  - `typ` discriminates access vs refresh — never accept a refresh token at a route that wants an access token, and vice versa.
  - `jti` enables short-window blacklist on logout. NO role/permission claims — those are looked up from the DB by `CurrentUserService` so role changes take effect immediately, not at the next refresh.
  - `iss` / `aud` are validated on every decode.

### Refresh token — long, DB-tracked, rotated, opaque to client

- **Format**: A 256-bit cryptographically random string (`secrets.token_urlsafe(32)`), **not** a JWT. JWTs are a poor fit for refresh because we need to store a per-token state row anyway (`revoked_at`, `replaced_by`, family). An opaque string is shorter, less leaky, and unambiguous.
- **TTL**: **30 days**.
- **Storage**: a new `refresh_tokens` table (see schema below). The client gets the raw token; the DB stores `sha256(token)` — never the raw value. Compromised DB dump does not yield usable tokens.
- **Single-use**: every successful `/refresh/` call **rotates** the refresh token. The presented token is marked `revoked_at = now()` and `replaced_by = <new_token_id>`, and a brand-new token is returned. Old refresh tokens never work twice.
- **Family / reuse detection**: every login starts a new "family" (a UUID stamped on every token in the rotation chain). If a token marked `revoked_at IS NOT NULL` is ever presented again, that is a replay — almost certainly a stolen token being used after the legitimate client already rotated. **The entire family is revoked** (all tokens with that `family_id` get `revoked_at = now()`), an audit event is logged at WARNING, and the user is logged out across every device that shared that family. This is the standard refresh-token reuse mitigation; do not skip it.

### Access revocation (the logout problem)

Stateless access tokens cannot be "deleted." For logout we accept up to 15 minutes of residual access on the old token if we do nothing — usually fine, but the user can change their password and still see their bank balance from the previous session, which is bad.

Decision: a small **access-token denylist** keyed by `jti`, kept in Postgres (`revoked_access_jtis` table: `jti PK, user_id, expires_at`). On every authenticated request the `Authorization: Bearer` middleware checks the denylist. Rows are reaped by a daily job once `expires_at < now()`. The table stays small because access TTL is short.

- On `/logout/`: refresh token is revoked (DB), the access token's `jti` is added to the denylist.
- On password change / reset: revoke every refresh token for the user + denylist every outstanding access `jti` we have on hand (we have them from the refresh table only if we also store the last-issued access jti per refresh — we do; see schema).

This is the deliberate stateful tradeoff. Pure stateless JWT is incompatible with "log me out now" UX.

### Key rotation

- `JWT_SECRET` stays in env (today's `JwtSettings.SECRET`, min 32 chars). For rotation we add an `kid` header to issued tokens and load a `{kid: secret}` map. Validation tries the `kid` from the header. New tokens always use the current `kid`. Old `kid`s stay loaded for one access TTL window (15 min), then drop.
- This is **not** in the first PR. The first PR uses a single secret. The follow-up adds `kid` once the operational story (where do secrets live, how is rotation triggered) is decided. Call out as future work.

## Endpoint contract

All under `/api/v1/account/`.

### `POST /account/login/` — status code 200 (was 204)

Request:
```json
{ "email": "alice@example.com", "password": "..." }
```

Success response (200):
```json
{
  "access_token": "eyJhbGciOi...",
  "refresh_token": "k1zN-...-Q",
  "token_type": "Bearer",
  "expires_in": 900,
  "refresh_expires_in": 2592000
}
```

Error responses:
- 401 — invalid credentials (intentionally vague — same body for "wrong email" and "wrong password" to prevent user enumeration).
- 403 — `EmailNotVerifiedError`, `AlreadyAuthenticatedError`.
- 423 — account locked (new — see "Account lockout").
- 429 — rate limit exceeded (new — see "Rate limiting").
- 503 — storage / hasher unavailable.

Side effects on success:
- New row in `refresh_tokens` with a fresh `family_id`.
- Audit event `auth.login.success` (user_id, ip, user_agent).

Side effects on failure:
- `failed_login_attempts` counter for that email is incremented (sliding window, see lockout).
- Audit event `auth.login.failure` (email, ip, user_agent, reason classifier).
- Response time deliberately constant (~bcrypt cost) even when the email does not exist — we still execute a dummy hash compare. Prevents timing-based user enumeration.

### `POST /account/refresh/` — new endpoint, status 200

Request:
```json
{ "refresh_token": "k1zN-...-Q" }
```

Response (200) — same shape as `/login/`. The returned refresh token is **different** from the one sent (rotation).

Errors:
- 401 — token unknown, expired, or revoked. **If revoked, the entire family is killed and the audit event `auth.refresh.replay_detected` is logged.**
- 423 — user account locked or deactivated.
- 429 — rate limited.

The endpoint does **not** require an access token. That is intentional: refresh is what you do when your access token is dead.

### `POST /account/logout/` — body-based, status 204

Request:
```json
{ "refresh_token": "k1zN-...-Q" }
```

Auth: `Authorization: Bearer <access>` required (so we know who is logging out and can denylist the right `jti`).

Behaviour:
- Revokes the refresh token presented.
- Denylists the access token's `jti` until its natural `exp`.
- Audit event `auth.logout`.
- Returns 204.

If the body's refresh token does not match the access token's user — 400. If it is already revoked — still return 204 (idempotent).

### `POST /account/logout-all/` — new endpoint, status 204

Auth: bearer required. Revokes every refresh token + denylists every known access `jti` for the user. Used by "log out everywhere" UI and triggered automatically on password change / reset.

### Other authenticated routes

Every existing protected route stops depending on the auth cookie and switches to the new `BearerAuthMiddleware` (or per-router `Depends(get_current_user)`). The dependency reads `Authorization: Bearer <token>`, decodes the JWT, checks `typ == "access"`, checks the `jti` denylist, and populates `request.state.user_id`. `CurrentUserService` reads from there instead of the cookie path.

### Endpoints that stay unchanged

- `POST /account/signup/` — already returns 204, no session issued (signup → verify-email → login is the flow).
- `POST /account/verify-email/` — no session involved.
- `POST /account/resend-verification/` — no session.
- `POST /account/forgot-password/` — no session.
- `POST /account/reset-password/` — no session.
- `POST /account/change-password/` — requires bearer instead of cookie. Triggers `logout-all` for the user after success.
- `GET /account/default-organization/` — public, unchanged.

## DB schema

### New table `refresh_tokens`

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `user_id` | UUID FK `users.id` ON DELETE CASCADE | indexed |
| `family_id` | UUID NOT NULL | indexed; all tokens issued via rotation share this |
| `token_hash` | TEXT NOT NULL UNIQUE | `sha256(raw_token)` hex |
| `issued_access_jti` | UUID | the access jti we issued with this refresh; used for "logout-all" denylisting |
| `expires_at` | TIMESTAMPTZ NOT NULL | indexed |
| `revoked_at` | TIMESTAMPTZ NULL | NULL means active |
| `replaced_by` | UUID NULL FK self | filled on rotation |
| `created_at` | TIMESTAMPTZ NOT NULL | |
| `last_used_at` | TIMESTAMPTZ NULL | updated on every accepted refresh |
| `ip` | INET NULL | observed on issue |
| `user_agent` | TEXT NULL | truncated to 512 chars |

Indices: `(user_id)`, `(family_id)`, `(token_hash)` unique, `(expires_at)` for the reaper.

### New table `revoked_access_jtis`

| Column | Type | Notes |
|---|---|---|
| `jti` | UUID PK | |
| `user_id` | UUID FK `users.id` ON DELETE CASCADE | |
| `expires_at` | TIMESTAMPTZ NOT NULL | indexed for reaper |

### New table `failed_login_attempts`

| Column | Type | Notes |
|---|---|---|
| `id` | BIGSERIAL PK | |
| `email_lower` | CITEXT NOT NULL | indexed; lowercased so case does not bypass |
| `ip` | INET NOT NULL | indexed |
| `attempted_at` | TIMESTAMPTZ NOT NULL | indexed |

Sliding-window queries select rows in the last N minutes.

### Existing `auth_sessions` table

**Drop after migration completes.** During the transition window (one release), both paths coexist; the table is unused by the new code. Migration drops it in the release after.

Migration files go under `src/app/infrastructure/persistence_sqla/alembic/versions/`. Naming: `2026-06-NN_HHMMSS_add_refresh_tokens.py` etc.

## Security controls

### Rate limiting — `slowapi`

Add `slowapi` (Redis-backed counter store; falls back to in-memory for dev/single-worker). Required for prod because uvicorn workers do not share in-memory state, so an in-memory limiter is per-worker and trivially bypassed by repeating requests until they hit different workers.

Per-endpoint limits (IP-keyed unless noted). All limits are pragma — tune in week one of prod traffic.

| Endpoint | Limit | Key | Rationale |
|---|---|---|---|
| `POST /account/login/` | 5/minute, 30/hour | IP **and** email (whichever exceeds first) | Brute force + credential stuffing. Email-keyed catches distributed attacks against one account. |
| `POST /account/refresh/` | 30/minute | IP | A real client refreshes ~4x/hour. 30/min is generous; spikes are suspicious. |
| `POST /account/signup/` | 3/hour, 10/day | IP | Signup is expensive (SMTP, user creation) and a classic spam vector. |
| `POST /account/forgot-password/` | 3/hour | IP **and** email | Email-keyed so an attacker cannot pump password-reset emails to a victim. |
| `POST /account/reset-password/` | 5/hour | IP | Token-gated so volume is naturally low. |
| `POST /account/resend-verification/` | already cooldown-gated (`VerificationSettings.RESEND_COOLDOWN_SEC`); also apply 5/hour IP | IP | Defence in depth. |
| `POST /account/change-password/` | 10/hour | user_id | Authenticated, so we have a user. |
| `POST /account/logout/` | 30/minute | user_id | Should not be a hot path. |
| All other authenticated routes | 120/minute | user_id | Generic abuse cap; well above any real client need. |
| Anonymous fallback for all other routes | 60/minute | IP | Cheap DDoS speed bump. |

429 responses include `Retry-After`. Limit breaches log an audit event at WARNING.

This is not a real WAF. **Note as follow-up**: for production deploy, terminate at Cloudflare/AWS WAF with global IP rate limits and bot challenges. Application-layer slowapi is the second line, not the first.

### Account lockout

- Sliding window: 10 failed login attempts for the same `email_lower` in 15 minutes → account is "soft locked" for 15 minutes.
- Soft-locked = `/login/` returns **423 Locked** with a `Retry-After` header. Password is not validated (so the lockout window cannot itself be used to probe).
- 5 failed attempts from the same IP across **any** emails in 5 minutes → that IP is rate-limited harder (drop to 1/min on `/login/`) for 30 minutes. Catches credential-stuffing scripts hitting many accounts from one host.
- Successful login clears the email's failed-attempts rows.
- Locked accounts do NOT auto-notify the user by email — that would be a free unauthenticated email-trigger endpoint. Notify on the *next successful* login ("There were 12 failed attempts to sign in to your account").

### Refresh token rotation + replay detection

Already covered above; reiterating because it is the single most important control:

1. Every `/refresh/` returns a new refresh token and revokes the old one.
2. If a revoked refresh token is presented, the **whole family** is revoked, the user is forced to re-log on every device that shared the family, and we log `auth.refresh.replay_detected` at WARNING with `family_id`, `user_id`, `ip`, `user_agent`.

### Audit log

Add a `security_audit_log` table (or write to a dedicated logger that ships to whatever the platform's log sink is — pick the table approach so DB-only ops have observability):

| Event | Level | Fields |
|---|---|---|
| `auth.login.success` | INFO | user_id, ip, user_agent |
| `auth.login.failure` | INFO | email (lowercased), ip, user_agent, reason ∈ {unknown_email, bad_password, not_verified, locked, inactive} |
| `auth.login.locked` | WARNING | email, ip |
| `auth.refresh.success` | DEBUG | user_id, family_id |
| `auth.refresh.replay_detected` | WARNING | user_id, family_id, ip, user_agent |
| `auth.logout` | INFO | user_id |
| `auth.logout_all` | INFO | user_id, reason ∈ {user_request, password_change, password_reset} |
| `auth.password_changed` | INFO | user_id |
| `auth.password_reset` | INFO | user_id |
| `auth.ratelimit.exceeded` | WARNING | endpoint, key, key_kind ∈ {ip, email, user_id} |

Reason classifiers in `auth.login.failure` are for our logs only — the HTTP response stays a generic 401.

### CORS

Today's `CorsSettings.ALLOWED_ORIGINS` hardcodes `https://car-rental-frontend-ruddy-nu.vercel.app` and `http://localhost:3000`. With cookies gone, `allow_credentials=True` is no longer needed — the browser does not carry credentials to a Bearer-only API.

- Change `allow_credentials=False`.
- Move `ALLOWED_ORIGINS` to env (it already is via pydantic-settings; the default list in `settings.py` is the issue). Strip the Vercel preview URL from the default; require the deployment environment to provide it.
- This is **not blocking** for the auth PR, but call it out as the immediate follow-up so the security model is consistent.

### Secrets

- `JWT_SECRET` — already env-sourced, min 32 chars. Stays that way. Rotate manually on incident.
- Future: AWS Secrets Manager / GCP Secret Manager backing. Out of scope for this spec.

### Optional — future work

- Device fingerprinting: bind a refresh token to a `device_id` claim and refuse refresh from a different device. Skipped for v1 because mobile and web give different signals and a buggy implementation is worse than no implementation.
- Geolocation anomaly detection: notify the user on login from a new country. Needs a geoip dependency and a notification template. Future.
- WebAuthn / passkeys: post-MVP.

## Migration plan

**Hard cutover, single release.** Both clients land their changes behind a feature flag; backend ships both paths for one release; the next release drops cookies.

Sequence:

1. **Release N (this spec)**: backend ships:
   - New `/account/refresh/` endpoint.
   - `/account/login/` returns 200 with the JSON body **in addition to** setting the legacy cookie (for as long as `LEGACY_COOKIE_ENABLED=true`).
   - `BearerAuthMiddleware` runs **before** the cookie middleware. If `Authorization` is present, it wins; otherwise the cookie path runs.
   - `/account/logout/` accepts both body refresh token and cookie session (whichever is present).
   - New tables ship.
   - Mobile cannot use cookies, so it goes straight to bearer once the mobile spec ships.
2. **Release N+1**: web frontend ships its spec; nothing on the backend changes.
3. **Release N+2 (cleanup)**: `LEGACY_COOKIE_ENABLED=false` becomes default; cookie middleware unregistered; `AuthCookieMiddleware`, `CookieManager`, `auth_sessions` table, `CookieSettings` are deleted. `AuthService.issue_session` and friends go too. Migration drops the table.

This is one extra release. The alternative — hard cutover in N — risks leaving users on stale builds without auth. Worth the patience.

### Backward compatibility during the transition

Existing `auth_sessions` rows are honoured by the legacy code path. There is no migration needed for them; they expire on their own (5-min TTL today). The new code path never reads or writes that table.

## Acceptance criteria

```bash
# Login
$ curl -i -X POST https://api/.../v1/account/login/ \
    -H 'Content-Type: application/json' \
    -d '{"email":"alice@example.com","password":"correct horse"}'
HTTP/1.1 200 OK
{
  "access_token": "eyJ...",
  "refresh_token": "k1...",
  "token_type": "Bearer",
  "expires_in": 900,
  "refresh_expires_in": 2592000
}

# Authenticated request
$ curl -i https://api/.../v1/account/default-organization/ \
    -H 'Authorization: Bearer eyJ...'
HTTP/1.1 200 OK

# Without bearer
$ curl -i https://api/.../v1/rentals/123/
HTTP/1.1 401 Unauthorized

# Refresh
$ curl -i -X POST https://api/.../v1/account/refresh/ \
    -H 'Content-Type: application/json' \
    -d '{"refresh_token":"k1..."}'
HTTP/1.1 200 OK
# Returns a NEW refresh_token (rotation)

# Replay the old refresh — entire family killed
$ curl -i -X POST https://api/.../v1/account/refresh/ \
    -H 'Content-Type: application/json' \
    -d '{"refresh_token":"k1..."}'   # the original, now revoked
HTTP/1.1 401 Unauthorized
# Audit log shows auth.refresh.replay_detected at WARNING.
# DB: every row with this family_id has revoked_at IS NOT NULL.

# Logout
$ curl -i -X POST https://api/.../v1/account/logout/ \
    -H 'Authorization: Bearer eyJ...' \
    -H 'Content-Type: application/json' \
    -d '{"refresh_token":"k2..."}'
HTTP/1.1 204 No Content

# Subsequent bearer use of the old access token
$ curl -i https://api/.../v1/account/default-organization/ \
    -H 'Authorization: Bearer eyJ...'
HTTP/1.1 401 Unauthorized   # jti denylisted

# Rate-limit verification
$ for i in $(seq 1 6); do
    curl -s -o /dev/null -w "%{http_code}\n" -X POST .../v1/account/login/ \
      -H 'Content-Type: application/json' \
      -d '{"email":"alice@example.com","password":"wrong"}'
  done
401
401
401
401
401
429   # 6th request blocked by IP+email rate limit
```

Plus:

- `POST /login/` with wrong password 10x in 15 min → 11th attempt returns **423 Locked**, even with the correct password, until the window elapses. Server logs `auth.login.locked` at WARNING.
- `POST /login/` with an unknown email returns 401 in ~the same time as a known-email-wrong-password attempt (timing check: median over 100 calls within 50ms of each other).
- `POST /refresh/` with an expired refresh → 401, no family kill.
- `POST /refresh/` with a token from a logged-out session → 401, no family kill (single revoked token, not a replay-of-already-revoked).
- `POST /refresh/` with a token that was already rotated once → 401 + `auth.refresh.replay_detected` + family kill.
- `POST /account/change-password/` with bearer → 204, all refresh tokens for the user are revoked, all known access jtis are denylisted; next API call from any other device returns 401.
- No cookie is set on any new-style request (`Set-Cookie` header absent in response).
- During transition window: an old browser session with a valid cookie and no bearer continues to work — legacy fallback path.
- `make lint-check`, `mypy`, and the existing test suite stay green over the changed files.

## Non-goals

- Replacing bcrypt or changing `PasswordHasherSettings` — out of scope (signup hardening already touched the password path; this spec does not).
- Implementing the `kid`-based JWT key rotation in this PR — added as a tracked follow-up.
- WebAuthn / passkeys / TOTP MFA — separate spec when it lands.
- Tightening CORS or removing the Vercel preview origin — flagged here as immediate follow-up, but lives in its own PR so the security-controls diff is reviewable.
- Push-notification token rotation on login/logout is described in `AUTH_JWT_MOBILE.md`, not here.
- Migrating existing `auth_sessions` rows — they expire naturally inside the 5-min TTL; no backfill into `refresh_tokens`.
- A full WAF / Cloudflare layer — operational concern, not a backend code change. Called out as the recommended outer layer.
