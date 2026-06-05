# API

## Base Path

All endpoints are under `/api/v1`. Interactive docs at `GET /` (redirects to `/docs`).

## Authentication

Cookie-based. On successful login the server sets an `HttpOnly; Secure; SameSite=none` cookie named `auth_token`. All subsequent requests must carry this cookie. No `Authorization: Bearer` header scheme is used.

Session TTL defaults to 5 minutes (configurable via `SESSION_TTL_MIN`), with sliding refresh when within 20% of expiry.

---

## Account (`/api/v1/account`)

| Method | Path | Description |
|---|---|---|
| POST | `/account/signup` | Register a new account. Sends verification email. |
| POST | `/account/login` | Authenticate. Sets `auth_token` cookie. Requires `email_verified=true`. |
| POST | `/account/logout` | Clears session and cookie. |
| POST | `/account/verify-email` | Submit OTP code from email. |
| POST | `/account/resend-verification` | Re-send verification email (60s cooldown). |
| POST | `/account/change-password` | Change password (authenticated). Revokes all sessions. |
| POST | `/account/forgot-password` | Request password reset email. |
| POST | `/account/reset-password` | Submit reset token + new password. |

## Invites (`/api/v1/invites`)

| Method | Path | Description |
|---|---|---|
| POST | `/invites/` | Create an invite link for a new staff member. |
| GET | `/invites/{token}` | Look up an invite by token (used during sign-up). |

## Users (`/api/v1/users`)

| Method | Path | Description |
|---|---|---|
| GET | `/users/` | List users (paginated). |
| POST | `/users/` | Create a user (admin-only). |
| POST | `/users/{user_id}/activate` | Activate a user. |
| POST | `/users/{user_id}/deactivate` | Deactivate a user. |
| POST | `/users/{user_id}/set-password` | Set a user's password (admin). |
| POST | `/users/{user_id}/set-role` | Change a user's role. |

## Organizations (`/api/v1/organizations`)

| Method | Path | Description |
|---|---|---|
| GET | `/organizations/` | List organizations. |
| POST | `/organizations/` | Create an organization. |
| GET | `/organizations/{org_id}` | Get organization detail. |
| PATCH | `/organizations/{org_id}` | Update organization. |

## Branches (`/api/v1/branches`)

| Method | Path | Description |
|---|---|---|
| GET | `/branches/` | List branches. |
| POST | `/branches/` | Create a branch. |

## Vehicles (`/api/v1/vehicles`)

| Method | Path | Description |
|---|---|---|
| GET | `/vehicles/` | List vehicles (paginated, filterable). |
| POST | `/vehicles/` | Create a vehicle. |
| GET | `/vehicles/{vehicle_id}` | Get vehicle detail. |
| PATCH | `/vehicles/{vehicle_id}` | Update vehicle. |
| POST | `/vehicles/{vehicle_id}/status` | Change vehicle status. |
| POST | `/vehicles/bulk-status` | Bulk change vehicle statuses. |
| POST | `/vehicles/{vehicle_id}/photos` | Add/remove photos. |
| GET | `/vehicles/{vehicle_id}/financials` | Vehicle financial summary. |
| GET | `/vehicles/{vehicle_id}/timeline` | Vehicle rental/service timeline. |

## Vehicle Categories (`/api/v1/vehicle-categories`)

CRUD for vehicle category labels. Routers exist in `vehicle_categories/router.py`.

## Vehicle Documents (`/api/v1/vehicle-documents`)

| Method | Path | Description |
|---|---|---|
| GET | `/vehicle-documents/` | List documents for a vehicle. |
| POST | `/vehicle-documents/` | Upload a document. |
| DELETE | `/vehicle-documents/{doc_id}` | Delete a document. |

## Vehicle Pricing (`/api/v1/vehicle-pricing`)

| Method | Path | Description |
|---|---|---|
| GET | `/vehicle-pricing/` | List pricing records for a vehicle. |
| POST | `/vehicle-pricing/` | Create a pricing entry. |
| PATCH | `/vehicle-pricing/{pricing_id}` | Update a pricing entry. |

## Clients (`/api/v1/clients`)

| Method | Path | Description |
|---|---|---|
| GET | `/clients/` | List clients. |
| POST | `/clients/` | Create a client. |
| GET | `/clients/{client_id}` | Get client detail. |
| PATCH | `/clients/{client_id}` | Update client. |
| POST | `/clients/{client_id}/verify` | Mark client as verified. |
| POST | `/clients/{client_id}/blacklist` | Blacklist a client. |
| POST | `/clients/{client_id}/unblacklist` | Remove from blacklist. |
| GET | `/clients/{client_id}/rentals` | List client's rentals. |
| GET | `/clients/{client_id}/payments` | List client's payments. |
| POST | `/clients/{client_id}/debt-reminder` | Send debt reminder notification. |

## Rentals (`/api/v1/rentals`)

| Method | Path | Description |
|---|---|---|
| POST | `/rentals/` | Create a rental (status: pending). |
| GET | `/rentals/` | List rentals (paginated, filterable). |
| GET | `/rentals/booking-requests` | List booking requests from mobile. |
| GET | `/rentals/calendar` | Rental calendar view. |
| GET | `/rentals/returns-queue` | Vehicles due for return. |
| GET | `/rentals/{rental_id}` | Get rental detail. |
| PATCH | `/rentals/{rental_id}` | Update rental fields. |
| POST | `/rentals/{rental_id}/transition` | Generic status transition. |
| POST | `/rentals/{rental_id}/checkin` | Check in (start) a rental. |
| POST | `/rentals/{rental_id}/checkout` | Check out (end) a rental. |
| POST | `/rentals/{rental_id}/extend` | Extend scheduled end date. |
| POST | `/rentals/{rental_id}/cancel` | Cancel a rental. |
| POST | `/rentals/{rental_id}/complete` | Complete a rental. |
| GET | `/rentals/pending-extensions` | List pending extension requests. |
| POST | `/rentals/{rental_id}/extensions/{ext_id}/approve` | Approve extension request. |
| POST | `/rentals/{rental_id}/extensions/{ext_id}/reject` | Reject extension request. |

`RentalStatus` flow: `pending → confirmed → active → returning → completed | cancelled | disputed`.

## Rental Services (`/api/v1/rental-services`)

| Method | Path | Description |
|---|---|---|
| GET | `/rental-services/` | List services on a rental. |
| POST | `/rental-services/` | Add a service to a rental. |
| DELETE | `/rental-services/{service_id}` | Remove a service. |

## Additional Services (`/api/v1/additional-services`)

Catalogue management (service types that can be added to rentals).

| Method | Path | Description |
|---|---|---|
| GET | `/additional-services/` | List. |
| POST | `/additional-services/` | Create. |
| PATCH | `/additional-services/{id}` | Update. |

## Payments (`/api/v1/payments`)

| Method | Path | Description |
|---|---|---|
| GET | `/payments/` | List transactions. |
| GET | `/payments/pending` | List pending payment approvals. |
| GET | `/payments/{transaction_id}` | Get transaction detail. |
| POST | `/payments/charge` | Charge a client. |
| POST | `/payments/hold-deposit` | Hold a deposit. |
| POST | `/payments/release-deposit` | Release a deposit. |
| POST | `/payments/refund` | Process refund. |
| POST | `/payments/{transaction_id}/confirm` | Confirm a pending payment. |
| POST | `/payments/{transaction_id}/reject` | Reject a pending payment. |
| POST | `/payments/{transaction_id}/status` | Update transaction status. |

## Fines (`/api/v1/fines`)

| Method | Path | Description |
|---|---|---|
| GET | `/fines/` | List fines. |
| POST | `/fines/` | Create a fine. |
| GET | `/fines/{fine_id}` | Get fine detail. |
| POST | `/fines/{fine_id}/charge` | Charge fine to client. |

## Service Tasks (`/api/v1/service-tasks`)

| Method | Path | Description |
|---|---|---|
| GET | `/service-tasks/` | List tasks. |
| POST | `/service-tasks/` | Create a task. |
| GET | `/service-tasks/{task_id}` | Get task detail. |
| PATCH | `/service-tasks/{task_id}` | Update task. |
| POST | `/service-tasks/{task_id}/complete` | Mark task complete. |

## Investors (`/api/v1/investors`)

| Method | Path | Description |
|---|---|---|
| GET | `/investors/` | List investors. |
| POST | `/investors/` | Create investor. |
| GET | `/investors/{investor_id}` | Get investor detail. |
| PATCH | `/investors/{investor_id}` | Update investor. |
| GET | `/investors/{investor_id}/vehicles` | List investor's vehicles. |
| POST | `/investors/{investor_id}/vehicles` | Bind vehicle to investor. |
| DELETE | `/investors/{investor_id}/vehicles/{vid}` | Unbind vehicle. |
| GET | `/investors/{investor_id}/payouts` | List payouts. |
| POST | `/investors/{investor_id}/payouts` | Create payout. |
| PATCH | `/investors/{investor_id}/payouts/{payout_id}` | Update payout status. |
| GET | `/investors/{investor_id}/pnl` | Investor P&L report. |

## Investor Portal (`/api/v1/investor-portal`)

Self-service endpoints for users with role `investor`.

| Method | Path | Description |
|---|---|---|
| GET | `/investor-portal/dashboard` | Investor dashboard summary. |
| GET | `/investor-portal/vehicles` | Investor's own vehicles. |
| GET | `/investor-portal/payouts` | Investor's payouts. |

## Expense Categories (`/api/v1/expense-categories`)

| Method | Path | Description |
|---|---|---|
| GET | `/expense-categories/` | List. |
| POST | `/expense-categories/` | Create. |
| PATCH | `/expense-categories/{id}` | Update. |

## Cash Journal (`/api/v1/cash-journal`)

| Method | Path | Description |
|---|---|---|
| GET | `/cash-journal/` | List entries. |
| POST | `/cash-journal/` | Create entry. |
| GET | `/cash-journal/{entry_id}` | Get entry. |
| PATCH | `/cash-journal/{entry_id}` | Update entry. |
| POST | `/cash-journal/{entry_id}/confirm` | Confirm entry. |
| DELETE | `/cash-journal/{entry_id}` | Delete entry. |
| GET | `/cash-journal/balance` | Current balance. |
| GET | `/cash-journal/export` | Export to Excel (openpyxl). |

## Reports (`/api/v1/reports`)

| Method | Path | Description |
|---|---|---|
| GET | `/reports/pnl` | Company P&L report. |
| GET | `/reports/cash-flow` | Cash flow report. |
| GET | `/reports/vehicles-comparison` | Vehicle-by-vehicle comparison. |
| GET | `/reports/export` | Excel export of reports. |

## Dashboard (`/api/v1/dashboard`)

| Method | Path | Description |
|---|---|---|
| GET | `/dashboard/kpis` | Key performance indicators. |
| GET | `/dashboard/alerts` | Operational alerts. |
| GET | `/dashboard/active-rentals` | Currently active rentals. |
| GET | `/dashboard/revenue-chart` | Revenue over time chart data. |
| GET | `/dashboard/mobile-metrics` | Mobile app usage metrics. |

## Health (`/health`)

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Liveness check. Returns `{"status": "ok"}`. |

---

## Mobile (`/api/v1/mobile`)

All endpoints require the client to be authenticated with role `client` (permission `mobile.*`).

### Profile
| Method | Path | Description |
|---|---|---|
| GET | `/mobile/profile` | Get my profile. |
| PATCH | `/mobile/profile` | Update my profile. |
| GET | `/mobile/verification` | Get my verification status. |
| POST | `/mobile/documents` | Upload identity document. |
| GET | `/mobile/fines` | My fines. |
| GET | `/mobile/payments` | My payment history. |
| GET | `/mobile/outstanding` | My outstanding balance. |
| PATCH | `/mobile/notification-preferences` | Update notification preferences. |

### Notifications
| Method | Path | Description |
|---|---|---|
| GET | `/mobile/notifications` | List my notifications. |
| POST | `/mobile/notifications/{notification_id}/read` | Mark notification as read. |

### Devices
| Method | Path | Description |
|---|---|---|
| POST | `/mobile/devices` | Register push token (FCM/APNs). |
| DELETE | `/mobile/devices/{token}` | Unregister push token. |

### Organizations
| Method | Path | Description |
|---|---|---|
| GET | `/mobile/organizations` | List organizations I belong to. |
| POST | `/mobile/organizations/{org_id}/join` | Join an organization. |
| POST | `/mobile/organizations/{org_id}/leave` | Leave an organization. |

### Vehicles
| Method | Path | Description |
|---|---|---|
| GET | `/mobile/vehicles` | List available vehicles. |
| GET | `/mobile/vehicles/{vehicle_id}` | Vehicle detail. |
| GET | `/mobile/vehicles/{vehicle_id}/availability` | Check availability for date range. |

### Rentals
| Method | Path | Description |
|---|---|---|
| GET | `/mobile/rentals` | My rental history. |
| GET | `/mobile/rentals/active` | My current active rental. |
| GET | `/mobile/rentals/{rental_id}` | Rental detail. |
| POST | `/mobile/bookings` | Submit a booking request. |
| POST | `/mobile/rentals/{rental_id}/cancel` | Cancel my rental. |
| POST | `/mobile/rentals/{rental_id}/extension-request` | Request rental extension. |

### Payments
| Method | Path | Description |
|---|---|---|
| POST | `/mobile/payments` | Record a payment (pending confirmation by staff). |

---

## Error Responses

All errors follow a consistent structure via `fastapi-error-map`:

```json
{
  "detail": "<human-readable message>"
}
```

Standard HTTP codes used:

| Code | Meaning |
|---|---|
| 400 | Business rule violation (`BusinessTypeError`) |
| 401 | Not authenticated (`AuthenticationError`) |
| 403 | Not authorised (`AuthorizationError`) |
| 409 | Conflict (e.g. rental date overlap) |
| 503 | Storage/infrastructure error (`StorageError`) |

## Pagination

List endpoints use offset pagination. Query parameters: `offset` (default 0), `limit` (default varies). Response shape includes `items: [...]` and `total: int`.
