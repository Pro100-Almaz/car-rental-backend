# Data Model

## Database

PostgreSQL 18 (Alpine). All IDs are UUIDs. All timestamps are timezone-aware (`DateTime(timezone=True)`). Monetary values use `Numeric(10,2)`. String enums are stored as `VARCHAR`.

## Entity Inventory

### users
Core operator/staff table.

| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| organization_id | UUID FK → organizations | |
| email | VARCHAR | unique |
| phone | VARCHAR | nullable |
| password_hash | BYTEA | bcrypt + pepper |
| role | VARCHAR | `UserRole` enum |
| first_name / last_name | VARCHAR | |
| is_active | BOOLEAN | |
| email_verified | BOOLEAN | required before login |
| last_login_at | TIMESTAMPTZ | nullable |
| branch_id | UUID FK → branches | nullable |
| client_id | UUID FK → clients | nullable — links operator to their client profile |
| notification_preferences | JSONB | nullable |
| created_at / updated_at | TIMESTAMPTZ | |

Roles: `super_admin`, `admin`, `booking_manager`, `financial_manager`, `investor`, `technician`, `client`.

### auth_sessions
JWT-backed server-side sessions.

| Column | Type | Notes |
|---|---|---|
| id | UUID PK | session identifier encoded in JWT |
| user_id | UUID FK → users | |
| expiration | TIMESTAMPTZ | sliding window, refreshed if within threshold |

### email_verification_codes
OTP codes for email verification and password reset.

| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| user_id | UUID FK | |
| code | VARCHAR | |
| type | VARCHAR | `email_verification`, `password_reset` |
| expires_at | TIMESTAMPTZ | |

### invites
Invite tokens for staff onboarding.

| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| email | VARCHAR | |
| role | VARCHAR | |
| organization_id | UUID FK | |
| token | VARCHAR | |
| expires_at | TIMESTAMPTZ | |
| used_at | TIMESTAMPTZ | nullable |

### organizations
Top-level tenant.

| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| name | VARCHAR | |
| slug | VARCHAR | unique |
| settings | JSONB | |
| created_at / updated_at | TIMESTAMPTZ | |

### branches
Sub-units of an organization.

| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| organization_id | UUID FK → organizations | |
| name / address | VARCHAR | |

### vehicles
Fleet items.

| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| organization_id | UUID FK | |
| category_id | UUID FK → vehicle_categories | nullable |
| make / model / year | VARCHAR / INT | |
| plate_number | VARCHAR | |
| vin | VARCHAR | nullable |
| color | VARCHAR | nullable |
| fuel_type | VARCHAR | `FuelType` enum |
| transmission | VARCHAR | `Transmission` enum |
| mileage | INT | |
| status | VARCHAR | `VehicleStatus` enum |
| photos | JSONB | list of URLs |
| branch_id | UUID FK | nullable |
| notes | TEXT | nullable |
| created_at / updated_at | TIMESTAMPTZ | |

`VehicleStatus`: `available`, `reserved`, `rented`, `returning`, `in_service`, `in_wash`, `decommissioned`, `sold`.

### vehicle_categories
| Column | Type |
|---|---|
| id | UUID PK |
| organization_id | UUID FK |
| name | VARCHAR |

### vehicle_pricing
Rate cards per vehicle.

| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| vehicle_id | UUID FK | |
| rate_type | VARCHAR | `RateType` enum |
| price | Numeric(10,2) | |
| is_active | BOOLEAN | |

### vehicle_documents
| Column | Type |
|---|---|
| id | UUID PK |
| vehicle_id | UUID FK |
| type / title | VARCHAR |
| url | VARCHAR |
| expires_at | TIMESTAMPTZ nullable |

### clients
End-customer profiles.

| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| organization_id | UUID FK | |
| first_name / last_name | VARCHAR | |
| phone | VARCHAR | |
| email | VARCHAR | nullable |
| id_number | VARCHAR | nullable |
| trust_level | VARCHAR | `TrustLevel`: new/verified/trusted/vip |
| verification_status | VARCHAR | `VerificationStatus`: pending/verified/rejected |
| is_blacklisted | BOOLEAN | |
| documents | JSONB | |
| source | VARCHAR | `RegistrationSource`: manual/mobile |
| created_at / updated_at | TIMESTAMPTZ | |

### client_organizations
Join table: client ↔ org membership.

| Column | Type |
|---|---|
| id | UUID PK |
| client_id | UUID FK |
| organization_id | UUID FK |
| joined_at | TIMESTAMPTZ |

### rentals
Core rental record.

| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| organization_id | UUID FK | |
| vehicle_id | UUID FK → vehicles RESTRICT | |
| client_id | UUID FK → clients RESTRICT | |
| manager_id | UUID FK → users SET NULL | nullable |
| status | VARCHAR | `RentalStatus` enum |
| booking_type | VARCHAR | hourly/daily/weekly/monthly |
| booked_at | TIMESTAMPTZ | |
| scheduled_start / end | TIMESTAMPTZ | |
| actual_start / end | TIMESTAMPTZ | nullable |
| base_rate | Numeric(10,2) | |
| rate_type | VARCHAR | |
| estimated_total | Numeric(10,2) | |
| actual_total | Numeric(10,2) | nullable |
| discount_code / amount | VARCHAR / Numeric | |
| late_fee, mileage_surcharge, fuel_charge, wash_fee, damage_charge, fine_charge | Numeric(10,2) | surcharge line items |
| deposit_type / amount / status / refund_amount | various | |
| checkin_data / checkout_data | JSONB | inspection photos/notes |
| prepayment_amount / status | Numeric / VARCHAR | |
| source | VARCHAR | manual/mobile |
| invoice_url | VARCHAR | nullable |
| cancellation_reason / pickup_notes / notes | TEXT | nullable |

Indexes: `(organization_id, status)`, `(vehicle_id, status)`, `(client_id, status)`.

### rental_services
Additional services attached to a rental (line items).

| Column | Type |
|---|---|
| id | UUID PK |
| rental_id | UUID FK |
| additional_service_id | UUID FK |
| quantity | INT |
| price | Numeric(10,2) |

### additional_services
Service catalogue.

| Column | Type |
|---|---|
| id | UUID PK |
| organization_id | UUID FK |
| name | VARCHAR |
| price | Numeric(10,2) |
| is_active | BOOLEAN |

### transactions
Payment ledger.

| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| rental_id | UUID FK | nullable |
| client_id | UUID FK | |
| organization_id | UUID FK | |
| type | VARCHAR | `TransactionType` enum |
| method | VARCHAR | `PaymentMethod` enum |
| amount | Numeric(10,2) | |
| status | VARCHAR | `TransactionStatus` enum |
| source | VARCHAR | manual/mobile/auto |
| created_at / updated_at | TIMESTAMPTZ | |

### fines
Traffic/parking fines against a vehicle.

| Column | Type |
|---|---|
| id | UUID PK |
| organization_id / vehicle_id / rental_id | UUID FKs |
| type | VARCHAR — `FineType` |
| amount | Numeric(10,2) |
| status | VARCHAR — `FineStatus` |
| issued_at | TIMESTAMPTZ |

### service_tasks
Maintenance / operational tasks.

| Column | Type |
|---|---|
| id | UUID PK |
| organization_id / vehicle_id | UUID FKs |
| assigned_to | UUID FK → users nullable |
| type | VARCHAR — `ServiceTaskType` |
| priority | VARCHAR — `TaskPriority` |
| status | VARCHAR — `TaskStatus` |
| scheduled_at | TIMESTAMPTZ |

### investors / vehicle_investors / investor_payouts
Investor management for profit-sharing.

- `investors`: investor profile, type (`own/partner/shared`), contact info.
- `vehicle_investors`: binding between investor and vehicle with profit distribution config.
- `investor_payouts`: payout records with status (`calculated/approved/paid`).

### expense_categories
| Column | Type |
|---|---|
| id | UUID PK |
| organization_id | UUID FK |
| name | VARCHAR |
| type | VARCHAR — `ExpenseCategoryType`: direct/overhead |

### cash_journal_entries
Manual cash flow records.

| Column | Type |
|---|---|
| id | UUID PK |
| organization_id / branch_id | UUID FKs |
| operation_type | VARCHAR — income/expense |
| category_id | UUID FK nullable |
| amount | Numeric(10,2) |
| confirmed | BOOLEAN |
| description | TEXT |
| occurred_at | TIMESTAMPTZ |

### notifications
In-app notifications for mobile clients.

| Column | Type |
|---|---|
| id | UUID PK |
| user_id | UUID FK |
| type | VARCHAR — `NotificationType` |
| payload | JSONB |
| is_read | BOOLEAN |
| created_at | TIMESTAMPTZ |

### device_tokens
FCM/APNs tokens for mobile push.

| Column | Type |
|---|---|
| id | UUID PK |
| user_id | UUID FK |
| token | VARCHAR |
| platform | VARCHAR — ios/android |

### extension_requests
Client-initiated rental extension requests.

| Column | Type |
|---|---|
| id | UUID PK |
| rental_id / client_id | UUID FKs |
| requested_end | TIMESTAMPTZ |
| status | VARCHAR — pending/approved/rejected |

## Migration Strategy

Migrations live in `src/app/infrastructure/persistence_sqla/alembic/versions/`. They are date-prefixed (`YYYY-MM-DD_HHMMSS_<description>.py`) and applied sequentially via `alembic upgrade head`. The entrypoint (`docker-entrypoint.sh`) runs `alembic upgrade head` before starting uvicorn on every container start.

Migration history (21 files, in order):
1. `2026-04-01` — users
2. `2026-04-01` — auth_sessions
3. `2026-05-09` — organizations, branches, update users
4. `2026-05-09` — vehicles
5. `2026-05-09` — clients
6. `2026-05-09` — rentals
7. `2026-05-09` — transactions
8. `2026-05-10` — fines
9. `2026-05-10` — service_tasks
10. `2026-05-10` — add missing spec fields
11. `2026-05-10` — investors
12. `2026-05-11` — vehicle_pricing, additional_services, cash_journal
13. `2026-05-11` — email_verification_codes
14. `2026-05-11` — invites
15. `2026-05-11` — add client.user_id
16. `2026-05-13` — vehicle_documents
17. `2026-05-13` — vehicle_categories
18. `2026-05-13` — vehicle_category to string
19. `2026-05-13` — update user roles
20. `2026-05-22–23` — mobile sprint 1–5 (notifications, device_tokens, extension_requests, client_organizations)
21. `2026-05-23` — multi-org support
