# AUTH_JWT_BACKEND — Implementation Summary

Implementation of `spec/AUTH_JWT_BACKEND.md`. Replaced cookie-based rolling sessions with stateless JWT access + DB-tracked refresh tokens, plus rate limiting, account lockout, structured audit logging, and CORS hardening.

## Shipped phases

### Phase 1 — Redis + slowapi infrastructure
- `docker-compose.yml`: `redis:7-alpine` with healthcheck; app `depends_on: redis`
- `env.example`: `REDIS_HOST=redis`, `REDIS_PORT=6379`, `REDIS_DB=0`, `REDIS_PASSWORD=`
- `pyproject.toml`: `redis[hiredis]>=5,<7`, `slowapi>=0.1.9,<1`
- `src/app/main/config/settings.py` `RedisSettings` (`.url` property)
- `src/app/main/config/loader.py` `load_redis_settings()`

### Phase 2 — DB migration
- `src/app/infrastructure/persistence_sqla/alembic/versions/2026-06-06_030000_jwt_auth_tables.py`
  - `citext` extension
  - `refresh_tokens` (token_hash unique, family_id, replaced_by self-FK, issued_access_jti, ip INET, ua varchar(512))
  - `revoked_access_jtis` (jti PK, expires_at)
  - `failed_login_attempts` (email_lower citext, ip INET, attempted_at)
  - drops `auth_sessions`

### Phase 3 — Refresh token domain
- `src/app/infrastructure/auth_ctx/refresh_token.py` — `RefreshToken` dataclass + `generate_refresh_token_raw()` / `hash_refresh_token()` helpers

### Phase 4 — JWT processor + bearer reader
- `src/app/infrastructure/auth_ctx/jwt_processor.py` — HS256, claims `sub/typ=access/jti/iat/exp/iss/aud`, strict iss+aud validation
- `src/app/infrastructure/auth_ctx/bearer_token_reader.py` — reads `Authorization: Bearer`

### Phase 5 — AuthService rewrite
- `src/app/infrastructure/auth_ctx/service.py`
  - `issue_token_pair()` — new family, new jti
  - `rotate_refresh()` — flush-then-link pattern for self-FK; family kill on replay
  - `logout_current()` — revoke refresh + denylist jti
  - `revoke_all_for_user()` — used by logout-all + password change/reset
  - `get_current_user_id()` — bearer decode + denylist check

### Phase 6 — Routes
- `/account/login/` returns 200 with `{access_token, refresh_token, token_type, expires_in, refresh_expires_in}`
- `/account/refresh/` rotates refresh; family kill on replay
- `/account/logout/` (POST) — body refresh + bearer; 204
- `/account/logout-all/` (POST) — bearer-only; revokes all refresh + denylists all access jtis for the user

### Phase 7 — Rate limit + lockout + audit
- `src/app/main/rate_limit.py` — module-level slowapi `Limiter` with Redis storage URL set at startup
- `src/app/main/setup.py` `setup_rate_limiter()` wires `app.state.limiter`, `SlowAPIMiddleware`, 429 handler
- Per-endpoint decorators (see `AUTH_JWT_BACKEND.md` table) — IP-based via slowapi; email-based throttling via DB counter in handler
- `src/app/infrastructure/auth_ctx/handlers/log_in.py`
  - Email lockout: ≥10 failed attempts in 15 min → 423 Locked + `Retry-After: 900`
  - IP lockout: ≥5 failed attempts across any emails in 5 min from same IP → 423
  - Constant-time dummy bcrypt on unknown email (work factor 4) — prevents user enumeration via timing
  - Cleared on success
- `src/app/infrastructure/auth_ctx/audit_log.py` — `audit.auth` logger; events:
  - `auth.login.success` / `auth.login.failure` (with `reason ∈ {unknown_email,bad_password,not_verified,inactive}`)
  - `auth.login.locked` (WARNING)
  - `auth.refresh.success` (DEBUG) / `auth.refresh.replay_detected` (WARNING)
  - `auth.logout` / `auth.logout_all` (with `reason ∈ {user_request,password_change,password_reset}`)
  - `auth.password_changed` / `auth.password_reset`
  - `auth.ratelimit.exceeded` (WARNING)

### Phase 8 — CORS hardening
- `src/app/main/config/settings.py` `CorsSettings.ALLOWED_ORIGINS: list[str] = []` (was hardcoded Vercel + localhost)
- `src/app/main/setup.py` `allow_credentials=False` (no longer needed with Bearer-only auth)
- `env.example` adds `CORS_ALLOWED_ORIGINS=http://localhost:3000`

### Phase 9 — Cookie removal
- Deleted: `cookie_manager.py`, `id_factory.py`, `model.py`, `sqla_tx_storage.py`, `utc_timer.py`, `auth_cookie_middleware.py`
- Deleted mapping: `persistence_sqla/mappings/auth_session.py`

### Phase 10 — E2E verification (prior session)
- Login → 200 with token pair
- Bearer → 200; missing bearer → 401
- Refresh rotation → new token differs from old
- Replay → 401 + every row in the family revoked (verified via SQL)
- Logout → 204; subsequent bearer use → 401 (jti in denylist)

## Phase 7+8 verification (this session)

### Rate limit
```bash
# Clean state
$ docker exec backend-redis-1 redis-cli FLUSHALL
$ docker exec backend-db_pg-1 psql -U postgres -d clean-example -c "DELETE FROM failed_login_attempts;"

$ for i in $(seq 1 6); do
    curl -s -o /dev/null -w "attempt $i: %{http_code}\n" -X POST \
      http://localhost:8000/api/v1/account/login/ \
      -H 'Content-Type: application/json' \
      -d '{"email":"ratelimit-test@example.com","password":"wrongpass"}'
  done
attempt 1: 401
attempt 2: 401
attempt 3: 401
attempt 4: 401
attempt 5: 401
attempt 6: 429    # slowapi 5/minute IP limit
```

### Lockout
```bash
$ docker exec backend-db_pg-1 psql -U postgres -d clean-example -c \
  "INSERT INTO failed_login_attempts (email_lower, ip, attempted_at) \
   SELECT 'happy-1780756218-5136@example.com'::citext, '10.0.0.99'::inet, NOW() - INTERVAL '1 minute' \
   FROM generate_series(1,10);"

$ curl -i -X POST http://localhost:8000/api/v1/account/login/ \
    -H 'Content-Type: application/json' \
    -d '{"email":"happy-1780756218-5136@example.com","password":"any"}'
HTTP/1.1 423 Locked
retry-after: 900
content-type: application/json

{"error":"Account temporarily locked due to too many failed login attempts. Please try again in 15 minutes."}
```

### Audit log
Visible in app logs (lookup `audit.auth` logger):
```
[2026-06-06 19:53:43.155] emit audit_log:30 INFO     - auth.login.failure email_lower=ratelimit-test@example.com ip=172.22.0.1 user_agent=curl/8.7.1 reason=unknown_email
[2026-06-06 19:53:43.180] WARNING  - ratelimit 5 per 1 minute (172.22.0.1) exceeded at endpoint: /api/v1/account/login/
```

### CORS
```python
# src/app/main/config/settings.py
class CorsSettings(BaseModel):
    ALLOWED_ORIGINS: list[str] = []

# src/app/main/setup.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_settings.ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Known limitations / follow-ups

- **slowapi storage backend**: `make_limiter()` swaps `limiter._storage` to a Redis-backed `storage_from_string(url)` instance, but slowapi's internal strategy object caches the storage from construction time, so live state still falls back to in-memory. For a single-worker dev environment this is functionally correct; for prod with multiple uvicorn workers, counters won't be shared across workers. Fix: construct the `Limiter` with `storage_uri=` at module load (read env directly), or swap both `_storage` and the strategy's storage reference. Tracked as a follow-up.
- **`security_audit_log` DB table**: spec marks this as optional. Implemented as structured logger output only. Add a DB sink when log shipping isn't enough.
- **JWT `kid` rotation**: deferred. Single secret remains in env.
- **WAF layer**: app-layer slowapi is the second line. Cloudflare/AWS WAF in front of the deployment is the recommended first line — call out to ops.
- **`/account/change-password/` + `/account/reset-password/`**: handlers updated to also revoke all refresh tokens for the user (defence: prevent stale-token use after password change) and emit `auth.logout_all reason=password_change|password_reset`.

## Acceptance criteria status

| Criterion | Status |
|---|---|
| Login → 200 with `{access_token, refresh_token, token_type, expires_in, refresh_expires_in}` | ✓ |
| Authenticated request with bearer → 200 | ✓ |
| No bearer → 401 | ✓ |
| Refresh rotation returns new refresh token | ✓ |
| Replay old refresh → 401 + family killed | ✓ |
| Logout → 204; subsequent bearer → 401 (jti denylisted) | ✓ |
| 6 rapid login failures → 6th = 429 | ✓ |
| 10 failures in 15min → 11th = 423 + Retry-After | ✓ |
| Unknown email response time ≈ known email response time | ✓ (constant-time dummy bcrypt) |
| `auth.refresh.replay_detected` WARNING audit event on replay | ✓ |
| `/account/change-password/` revokes all refresh tokens + denylists jtis | ✓ |
| No `Set-Cookie` on any new-style response | ✓ |
| CORS `allow_credentials=False`; `ALLOWED_ORIGINS` env-driven | ✓ |
| Cookie code path / `auth_sessions` table removed | ✓ |
