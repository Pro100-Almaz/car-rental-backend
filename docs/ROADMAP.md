# Roadmap

Prioritised gaps and recommendations for moving from MVP to production-grade.

---

## P0 — Must fix before any production traffic

### 1. Remove debug `print()` from login handler
`src/app/infrastructure/auth_ctx/handlers/log_in.py:62` contains `print("*"*10, user.email_verified)`. Remove it.

### 2. Replace `--reload` in Docker entrypoint
`docker-entrypoint.sh` starts uvicorn with `--reload` even in Docker. For production, start without `--reload` and use a fixed worker count:
```bash
exec uvicorn app.main.run:make_app --factory --host 0.0.0.0 --port "$PORT" --workers 4
```

### 3. Externalise CORS allowed origins
`src/app/main/config/settings.py` has a hardcoded Vercel URL in the default `ALLOWED_ORIGINS`. Replace defaults with empty list and require explicit env config (`CORS_ALLOWED_ORIGINS`).

### 4. Secrets management
`JWT_SECRET` and `PASSWORD_PEPPER` are plain env vars. Wire a secrets manager (Vault, AWS SSM, or at minimum Docker secrets) before deploying.

---

## P1 — Critical gaps that limit reliability

### 5. CI/CD pipeline
The `.github/` directory is empty. Add GitHub Actions workflows for:
- `make lint` on every PR
- `make test-docker` on every PR
- Docker image build and push on merge to main

### 6. Push notifications implementation
`StubPushSender` in `src/app/infrastructure/adapters/stub_push_sender.py` does nothing. Implement a real `PushSender` using Firebase Cloud Messaging (FCM) or APNs. The device token model (`device_tokens` table) and notification preferences are already in place.

### 7. Scheduled job runner for reminders and overdue checks
The following commands exist but have no scheduler wired:
- `CheckPickupReminders`
- `CheckReturnReminders`
- `CheckOverdueRentals`
- `SendDebtReminder`

Add a scheduler (e.g. APScheduler, ARQ with Redis, or a simple cron container) that calls these commands on a schedule.

### 8. Rate limiting
No rate limiting exists anywhere. Add it at minimum to:
- `POST /account/login` (brute-force protection)
- `POST /account/resend-verification`
- `POST /account/forgot-password`

Use `slowapi` (wraps `limits`) or a reverse proxy (nginx `limit_req`).

---

## P2 — Quality and observability

### 9. Structured logging and correlation IDs
Currently uses `logging.basicConfig` with a plain text format. Add:
- JSON structured logging (e.g. `structlog` or `python-json-logger`)
- A request-scoped correlation ID injected into all log records
- Log the request method, path, status code, and duration for each request

### 10. OpenAPI auth scheme
The OpenAPI schema does not declare cookie authentication, so the `/docs` UI cannot authenticate. Add a `SecurityScheme` for cookie-based auth to make interactive testing possible.

### 11. Health check — database probe
`GET /health` currently returns a static `{"status": "ok"}`. Extend it to probe the database connection so load balancers can detect backend failures.

### 12. Test coverage gaps
`make test` runs only sanity, unit, and no-infra integration tests. The `with_infra` integration tests only cover `account/` and `users/`. Add integration tests for:
- Rentals lifecycle (create → confirm → active → complete)
- Payment flows
- Mobile booking request flow

Target: 80%+ branch coverage across the full `with_infra` suite.

### 13. OpenAPI response schema definitions
Many endpoints return `TypedDict` or `dict` responses without full Pydantic response model declarations. Add explicit Pydantic response models to generate accurate OpenAPI schemas.

---

## P3 — Performance and scalability

### 14. Caching layer
There is no caching. Add Redis for:
- Vehicle availability checks (frequently read, rarely written)
- Dashboard KPIs (acceptable staleness of ~30s)
- Session invalidation list (faster than DB lookup for revoked sessions)

### 15. Connection pool tuning
`SQLA_POOL_SIZE` defaults to 15 with `MAX_OVERFLOW=0`. Under load with multiple workers this will exhaust connections. Document and tune based on `workers × pool_size ≤ max_db_connections`.

### 16. Async email sending
`SmtpEmailSender` sends email synchronously (blocking). Move email sending to a background task or queue to avoid adding latency to the request.

### 17. File/document storage
Client documents and vehicle photos are stored as URLs in JSONB fields. There is no upload endpoint backed by actual object storage. Integrate S3-compatible storage (AWS S3, MinIO) and return pre-signed URLs.

---

## P4 — Feature completeness

### 18. Booking approval workflow
`SubmitBookingRequest` creates a rental with `source=mobile`. The approval/rejection by staff is not yet a distinct endpoint — it reuses the generic `transition_rental`. Make the booking approval flow explicit with proper notifications.

### 19. Invoice generation
`invoice_url` exists on the `Rental` entity but is always `None`. Implement PDF invoice generation (e.g. via `weasyprint` or `reportlab`) on rental completion.

### 20. Multi-currency support
All amounts are `Numeric(10,2)` with no currency field. If the platform expands beyond KZT (Kaspi payment method is present), add a `currency` column to transactions.

### 21. Audit log
Sensitive operations (role changes, blacklisting, password resets, payout approvals) have no audit trail. Add an `audit_log` table populated by command handlers.

### 22. Admin panel / backoffice
No admin UI. Consider connecting to an existing tool (e.g. `sqladmin` for a basic FastAPI-native admin, or an external React/Next.js panel).
