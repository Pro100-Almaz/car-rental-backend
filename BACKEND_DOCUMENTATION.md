# AutoFleet Backend — Implementation Documentation

## Architecture Overview

**Stack**: Python 3.13, FastAPI, SQLAlchemy (async), dishka DI, PostgreSQL
**Pattern**: Clean Architecture + CQRS (Commands for writes, Queries for reads)
**Layers**: `core` → `infrastructure` → `presentation` → `main`
**Package manager**: uv

```
src/app/
├── core/           # Domain logic (entities, commands, queries, ports)
├── infrastructure/ # Adapters (SQLAlchemy, auth, email)
├── presentation/   # HTTP endpoints (FastAPI routers)
└── main/           # App bootstrap (DI, config, setup)
```

---

## Entities & Enums

### Type Aliases (all UUID-based via NewType)

OrganizationId, BranchId, UserId, VehicleId, ClientId, RentalId, TransactionId, FineId, ServiceTaskId, InvestorId, VehicleInvestorId, InvestorPayoutId, VehiclePricingId, VehicleDocumentId, VehicleCategoryId, AdditionalServiceId, RentalServiceId, ExpenseCategoryId, CashJournalEntryId, UserPasswordHash

### Enums (all StrEnum)

- **VehicleStatus**: AVAILABLE, RESERVED, RENTED, RETURNING, IN_SERVICE, IN_WASH, DECOMMISSIONED, SOLD
- **FuelType**: PETROL, DIESEL, GAS, ELECTRIC, HYBRID
- **Transmission**: MANUAL, AUTOMATIC
- **VerificationStatus**: PENDING, VERIFIED, REJECTED
- **TrustLevel**: NEW, VERIFIED, TRUSTED, VIP
- **RentalStatus**: PENDING, CONFIRMED, ACTIVE, RETURNING, COMPLETED, CANCELLED, DISPUTED
- **BookingType**: HOURLY, DAILY, WEEKLY, MONTHLY
- **RateType**: PER_HOUR, PER_DAY, PER_WEEK, PER_MONTH
- **DepositType**: CASH, CARD_HOLD, KASPI, DEBT
- **DepositStatus**: PENDING, HELD, PARTIALLY_REFUNDED, REFUNDED, FORFEITED
- **PrepaymentStatus**: NONE, PARTIAL, FULL
- **TransactionType**: RENTAL_PAYMENT, DEPOSIT_HOLD, DEPOSIT_REFUND, FINE_CHARGE, WALLET_TOPUP, DEBT_PAYMENT, PLATFORM_FEE
- **PaymentMethod**: KASPI, CARD, CASH, WALLET, BANK_TRANSFER
- **TransactionStatus**: PENDING, PROCESSING, COMPLETED, FAILED, REFUNDED
- **ServiceTaskType**: WASH, MECHANICAL_SERVICE, REPAIR, RELOCATION, INSPECTION, FUEL_TOPUP
- **TaskPriority**: LOW, NORMAL, HIGH, URGENT
- **TaskStatus**: CREATED, ASSIGNED, IN_PROGRESS, PHOTO_PROOF, COMPLETED, CANCELLED
- **FineType**: TRAFFIC, PARKING, TOLL, OTHER
- **FineStatus**: PENDING, CHARGED_TO_CLIENT, PAID_BY_OPERATOR, DISPUTED
- **InvestorType**: OWN, PARTNER, SHARED
- **PayoutStatus**: CALCULATED, APPROVED, PAID
- **ProfitDistributionType**: PERCENTAGE, FIXED
- **UserRole**: SUPER_ADMIN, ADMIN, BOOKING_MANAGER, FINANCIAL_MANAGER, INVESTOR, TECHNICIAN
- **OperationType**: INCOME, EXPENSE
- **ExpenseCategoryType**: DIRECT, OVERHEAD

### Entity Definitions

**User**: id_, organization_id, email, phone, password_hash, role (UserRole), first_name, last_name, is_active, email_verified, last_login_at, branch_id, created_at, updated_at

**Organization**: id_, name, slug, settings (dict), subscription_plan, created_at, updated_at

**Branch**: id_, organization_id, name, address, latitude, longitude, timezone, created_at

**Vehicle**: id_, organization_id, nickname, make, model, year, vin, license_plate, color, category, status (VehicleStatus), fuel_type (FuelType), transmission (Transmission), current_mileage, purchase_price, purchase_date, insurance_expiry, inspection_expiry, gps_device_id, current_latitude, current_longitude, current_fuel_level, branch_id, photos (list[str]), features (dict), pricing_override (dict), created_at, updated_at

**VehicleCategory**: id_, organization_id, name, description, created_at

**VehiclePricing**: id_, vehicle_id, base_daily_rate, name, multiplier, valid_from, valid_to, is_active, created_at

**VehicleDocument**: id_, vehicle_id, document_type, name, url, expiry_date, created_at

**VehicleInvestor** (many-to-many link): id_, vehicle_id, investor_id, share_percentage, profit_distribution_type (ProfitDistributionType), created_at

**Rental**: id_, organization_id, vehicle_id, client_id, manager_id, status (RentalStatus), booking_type (BookingType), booked_at, scheduled_start, scheduled_end, actual_start, actual_end, base_rate, rate_type (RateType), estimated_total, actual_total, discount_code, discount_amount, late_fee, mileage_surcharge, fuel_charge, wash_fee, damage_charge, fine_charge, deposit_type (DepositType), deposit_amount, deposit_status (DepositStatus), deposit_refund_amount, checkin_data (dict), checkout_data (dict), invoice_url, cancellation_reason, prepayment_amount, prepayment_status (PrepaymentStatus), notes, created_at, updated_at

**RentalService**: id_, rental_id, service_id, quantity, price, created_at

**Client**: id_, organization_id, user_id, phone, email, first_name, last_name, id_document_url, license_front_url, license_back_url, verification_status (VerificationStatus), trust_score, trust_level (TrustLevel), is_blacklisted, blacklist_reason, wallet_balance, debt_balance, metadata (dict), created_at, updated_at

**Transaction**: id_, organization_id, rental_id, client_id, type_ (TransactionType), amount, currency, payment_method (PaymentMethod), status (TransactionStatus), external_id, metadata (dict), created_at, updated_at

**Fine**: id_, organization_id, vehicle_id, rental_id, client_id, fine_type (FineType), amount, description, fine_date, document_url, status (FineStatus), created_at, updated_at

**ServiceTask**: id_, organization_id, vehicle_id, rental_id, assigned_to, task_type (ServiceTaskType), priority (TaskPriority), status (TaskStatus), description, estimated_cost, actual_cost, proof_photos (list), notes, due_at, completed_at, created_at, updated_at

**Investor**: id_, organization_id, full_name, type_ (InvestorType), contact_phone, contact_email, user_id, notes, created_at, updated_at

**InvestorPayout**: id_, organization_id, investor_id, period_month, calculated_profit, share_amount, status (PayoutStatus), paid_at, notes, created_at

**AdditionalService**: id_, organization_id, name, price, is_active, created_at

**ExpenseCategory**: id_, organization_id, name, type_ (ExpenseCategoryType), is_system, sort_order, is_active, created_at

**CashJournalEntry**: id_, organization_id, date, operation_type (OperationType), vehicle_id, rental_id, expense_category_id, payment_method (PaymentMethod), amount, description, receipt_url, confirmed_by, confirmed_at, created_by, created_at

---

## Commands (Write Operations) — 73 total

**User Management**: ActivateUser, DeactivateUser, CreateUser, SetUserPassword, SetUserRole

**Organization & Branch**: CreateOrganization, UpdateOrganization, CreateBranch

**Vehicle Management**: CreateVehicle, UpdateVehicle, ChangeVehicleStatus (with VALID_TRANSITIONS state machine), BulkChangeVehicleStatus, CreateVehicleCategory, UpdateVehicleCategory, CreateVehiclePricing, UpdateVehiclePricing, CreateVehicleDocument, DeleteVehicleDocument, ManageVehiclePhotos (AddVehiclePhoto, RemoveVehiclePhoto), BindVehicleInvestor, UnbindVehicleInvestor

**Client Management**: CreateClient, UpdateClient, VerifyClient, BlacklistClient, UnblacklistClient

**Rental Management**: CreateRental, UpdateRental (uses _UNSET sentinel + model_fields_set for partial updates), TransitionRental (with VALID_RENTAL_TRANSITIONS state machine), CheckinRental, CheckoutRental, ExtendRental, CancelRental, CompleteRental

**Financial**: CreateTransaction, UpdateTransactionStatus, HoldDeposit, ReleaseDeposit, ChargeClient, ProcessRefund, CreateFine, ChargeFineToClient

**Service Tasks**: CreateServiceTask, UpdateServiceTask, CompleteServiceTask

**Investor**: CreateInvestor, UpdateInvestor, CreateInvestorPayout, UpdatePayoutStatus

**Additional Services**: CreateAdditionalService, UpdateAdditionalService, AddRentalService, RemoveRentalService

**Expense & Cash Journal**: CreateExpenseCategory, UpdateExpenseCategory, CreateCashJournalEntry, UpdateCashJournalEntry, ConfirmCashJournalEntry, DeleteCashJournalEntry

---

## Queries (Read Operations) — 45 total

**Dashboard**: GetDashboardKpis, GetDashboardAlerts, GetDashboardActiveRentals, GetDashboardRevenueChart (supports period YYYY-MM and week_start/week_end params)

**Reports**: GetCompanyPnl, GetCashFlow, GetVehiclesComparison

**Vehicles**: ListVehicles (filters: status, branch_id, category, investor_id, search, fuel_type, mileage_from, mileage_to), GetVehicle, GetVehicleFinancials, GetVehicleTimeline, GetVehiclePricing, ListVehiclePricing, ListVehicleCategories, ListVehicleDocuments

**Rentals**: ListRentals (filters: status, vehicle_id, client_id, date_from, date_to), GetRental, GetRentalCalendar (month param YYYY-MM), GetReturnsQueue

**Clients**: ListClients, GetClient

**Users**: ListUsers

**Financial**: ListTransactions, GetTransaction, GetCashJournalBalance, ListCashJournalEntries, GetCashJournalEntry, ListFines, GetFine

**Service Tasks**: ListServiceTasks, GetServiceTask

**Investors**: ListInvestors, GetInvestor, GetInvestorPnl, ListInvestorPayouts, ListInvestorVehicles, InvestorPortalDashboard, InvestorPortalVehicles, InvestorPortalPayouts

**Organization**: ListOrganizations, GetOrganization, ListBranches

**Other**: ListAdditionalServices, ListExpenseCategories, ListRentalServices

---

## HTTP API Endpoints (all under `/api/v1/`)

### Account (`/account`)

| Method | Path | Handler |
|--------|------|---------|
| POST | `/signup/` | SignUp |
| POST | `/login/` | LogIn |
| POST | `/verify-email/` | VerifyEmail |
| POST | `/resend-verification/` | ResendVerification |
| POST | `/change-password/` | ChangePassword |
| POST | `/logout/` | LogOut |

### Users (`/users`)

| Method | Path | Handler |
|--------|------|---------|
| POST | `/` | CreateUser (201) |
| GET | `/` | ListUsers |
| POST | `/{user_id}/password` | SetUserPassword |
| POST | `/{user_id}/role` | SetUserRole |
| POST | `/{user_id}/activate` | ActivateUser |
| POST | `/{user_id}/deactivate` | DeactivateUser |

### Organizations (`/organizations`)

| Method | Path | Handler |
|--------|------|---------|
| POST | `/` | CreateOrganization (201) |
| GET | `/` | ListOrganizations |
| GET | `/{org_id}` | GetOrganization |
| PUT | `/{org_id}` | UpdateOrganization |

### Branches (`/branches`)

| Method | Path | Handler |
|--------|------|---------|
| POST | `/` | CreateBranch (201) |
| GET | `/` | ListBranches |

### Vehicles (`/vehicles`)

| Method | Path | Handler |
|--------|------|---------|
| POST | `/` | CreateVehicle (201) |
| GET | `/` | ListVehicles |
| GET | `/{vehicle_id}` | GetVehicle |
| PUT | `/{vehicle_id}` | UpdateVehicle |
| POST | `/{vehicle_id}/status` | ChangeVehicleStatus |
| POST | `/bulk-status` | BulkChangeVehicleStatus |
| GET | `/{vehicle_id}/financials` | GetVehicleFinancials |
| GET | `/{vehicle_id}/timeline` | GetVehicleTimeline |
| POST/DELETE | `/{vehicle_id}/photos` | ManagePhotos |

### Vehicle Categories (`/vehicle-categories`)

| Method | Path | Handler |
|--------|------|---------|
| POST | `/` | CreateVehicleCategory (201) |
| GET | `/` | ListVehicleCategories |
| PUT | `/{category_id}` | UpdateVehicleCategory |

### Vehicle Documents (`/vehicle-documents`)

| Method | Path | Handler |
|--------|------|---------|
| POST | `/` | CreateVehicleDocument (201) |
| GET | `/` | ListVehicleDocuments |
| DELETE | `/{doc_id}` | DeleteVehicleDocument |

### Vehicle Pricing (`/vehicle-pricing`)

| Method | Path | Handler |
|--------|------|---------|
| POST | `/` | CreateVehiclePricing (201) |
| GET | `/` | ListVehiclePricing |
| GET | `/{pricing_id}` | GetVehiclePricing |
| PUT | `/{pricing_id}` | UpdateVehiclePricing |

### Clients (`/clients`)

| Method | Path | Handler |
|--------|------|---------|
| POST | `/` | CreateClient (201) |
| GET | `/` | ListClients |
| GET | `/{client_id}` | GetClient |
| PUT | `/{client_id}` | UpdateClient |
| POST | `/{client_id}/verify` | VerifyClient |
| POST | `/{client_id}/blacklist` | BlacklistClient |
| GET | `/{client_id}/rentals` | ClientRentals |
| GET | `/{client_id}/payments` | ClientPayments |

### Rentals (`/rentals`)

| Method | Path | Handler |
|--------|------|---------|
| POST | `/` | CreateRental (201) |
| GET | `/` | ListRentals |
| GET | `/calendar` | GetRentalCalendar |
| GET | `/returns-queue` | GetReturnsQueue |
| GET | `/{rental_id}` | GetRental |
| PATCH | `/{rental_id}` | UpdateRental |
| POST | `/{rental_id}/transition` | TransitionRental |
| POST | `/{rental_id}/checkin` | CheckinRental |
| POST | `/{rental_id}/checkout` | CheckoutRental |
| POST | `/{rental_id}/extend` | ExtendRental |
| POST | `/{rental_id}/cancel` | CancelRental |
| POST | `/{rental_id}/complete` | CompleteRental |

### Payments (`/payments`)

| Method | Path | Handler |
|--------|------|---------|
| POST | `/hold-deposit` | HoldDeposit |
| POST | `/release-deposit` | ReleaseDeposit |
| POST | `/charge` | ChargeClient |
| POST | `/refund` | ProcessRefund |
| GET | `/transactions` | ListTransactions |
| GET | `/transactions/{txn_id}` | GetTransaction |
| PUT | `/transactions/{txn_id}/status` | UpdateTransactionStatus |

### Fines (`/fines`)

| Method | Path | Handler |
|--------|------|---------|
| POST | `/` | CreateFine (201) |
| GET | `/` | ListFines |
| GET | `/{fine_id}` | GetFine |
| POST | `/{fine_id}/charge` | ChargeFineToClient |

### Service Tasks (`/service-tasks`)

| Method | Path | Handler |
|--------|------|---------|
| POST | `/` | CreateServiceTask (201) |
| GET | `/` | ListServiceTasks |
| GET | `/{task_id}` | GetServiceTask |
| PUT | `/{task_id}` | UpdateServiceTask |
| POST | `/{task_id}/complete` | CompleteServiceTask |

### Investors (`/investors`)

| Method | Path | Handler |
|--------|------|---------|
| POST | `/` | CreateInvestor (201) |
| GET | `/` | ListInvestors |
| GET | `/{investor_id}` | GetInvestor |
| PUT | `/{investor_id}` | UpdateInvestor |
| POST | `/{investor_id}/vehicles/bind` | BindVehicleInvestor |
| POST | `/{investor_id}/vehicles/unbind` | UnbindVehicleInvestor |
| GET | `/{investor_id}/vehicles` | ListInvestorVehicles |
| GET | `/{investor_id}/payouts` | ListInvestorPayouts |
| GET | `/{investor_id}/pnl` | GetInvestorPnl |
| POST | `/payouts` | CreateInvestorPayout |
| PUT | `/payouts/{payout_id}/status` | UpdatePayoutStatus |

### Investor Portal (`/investor-portal`)

| Method | Path | Handler |
|--------|------|---------|
| GET | `/dashboard` | InvestorPortalDashboard |
| GET | `/vehicles` | InvestorPortalVehicles |
| GET | `/payouts` | InvestorPortalPayouts |

### Additional Services (`/additional-services`)

| Method | Path | Handler |
|--------|------|---------|
| POST | `/` | CreateAdditionalService (201) |
| GET | `/` | ListAdditionalServices |
| PUT | `/{service_id}` | UpdateAdditionalService |

### Rental Services (`/rental-services`)

| Method | Path | Handler |
|--------|------|---------|
| POST | `/{rental_id}/services` | AddRentalService |
| DELETE | `/{rental_id}/services/{service_id}` | RemoveRentalService |
| GET | `/` | ListRentalServices |

### Expense Categories (`/expense-categories`)

| Method | Path | Handler |
|--------|------|---------|
| POST | `/` | CreateExpenseCategory (201) |
| GET | `/` | ListExpenseCategories |
| PUT | `/{category_id}` | UpdateExpenseCategory |

### Cash Journal (`/cash-journal`)

| Method | Path | Handler |
|--------|------|---------|
| POST | `/` | CreateCashJournalEntry (201) |
| GET | `/` | ListCashJournalEntries |
| GET | `/balance` | GetCashJournalBalance |
| GET | `/{entry_id}` | GetCashJournalEntry |
| PUT | `/{entry_id}` | UpdateCashJournalEntry |
| POST | `/{entry_id}/confirm` | ConfirmCashJournalEntry |
| DELETE | `/{entry_id}` | DeleteCashJournalEntry |

### Dashboard (`/dashboard`)

| Method | Path | Handler |
|--------|------|---------|
| GET | `/kpis` | GetDashboardKpis |
| GET | `/alerts` | GetDashboardAlerts |
| GET | `/active-rentals` | GetDashboardActiveRentals |
| GET | `/revenue-chart` | GetDashboardRevenueChart |

### Reports (`/reports`)

| Method | Path | Handler |
|--------|------|---------|
| GET | `/company-pnl` | GetCompanyPnl |
| GET | `/cash-flow` | GetCashFlow |
| GET | `/vehicles-comparison` | GetVehiclesComparison |

### Invites (`/invites`)

| Method | Path | Handler |
|--------|------|---------|
| POST | `/` | CreateInvite |
| GET | `/{invite_id}` | GetInvite |

### Health (`/health`)

| Method | Path | Handler |
|--------|------|---------|
| GET | `/health` | Health check |

---

## Auth System

**Flow**: Sign-up/Login → bcrypt password verify (HMAC-SHA384 pre-hash with PEPPER) → JWT issued → cookie staged via middleware

- **JWT**: HS256, symmetric secret (32+ chars)
- **Cookie**: `auth_token`, HttpOnly, Secure=true, SameSite=none
- **Session TTL**: 5 min (configurable via `SESSION_TTL_MIN`), auto-refresh at 80% expiry
- **RBAC**: CurrentUserService checks User.role permissions
- **CORS**: explicit origins (`http://localhost:3000`, `https://car-rental-frontend-ruddy-nu.vercel.app`), credentials allowed

---

## Infrastructure Patterns

- **DI**: dishka with APP scope (singletons) and REQUEST scope (per-request)
- **Error handling**: `fastapi_error_map` ErrorAwareRouter with per-endpoint `error_map` dicts mapping exceptions to HTTP status codes
- **Persistence**: imperative SQLAlchemy ORM mapping, async sessions, JSONB for flexible fields (photos, features, metadata)
- **State machines**: `VALID_TRANSITIONS` dicts for Vehicle status, Rental status, Payout status, Task status
- **Partial updates**: `_UNSET` sentinel pattern + Pydantic `model_fields_set` for PATCH endpoints
- **Config**: pydantic-settings with `.env` file, env prefix per section (e.g. `COOKIE_`, `CORS_`, `POSTGRES_`)

---

## Settings (env var prefixes)

| Class | Prefix | Key Fields |
|-------|--------|------------|
| AppSettings | `APP_` | SERVICE_NAME, VERSION, ROOT_PATH, DEBUG_MODE, LOGGING_LEVEL |
| PostgresSettings | `POSTGRES_` | DB, HOST, PORT, USER, PASSWORD |
| SqlaSettings | `SQLA_` | ECHO, POOL_SIZE, MAX_OVERFLOW |
| PasswordHasherSettings | `PASSWORD_` | PEPPER (32+ chars), WORK_FACTOR=11 |
| JwtSettings | `JWT_` | SECRET (32+ chars), ALGORITHM=HS256 |
| SessionSettings | `SESSION_` | TTL_MIN=5, REFRESH_THRESHOLD_RATIO=0.2 |
| CorsSettings | `CORS_` | ALLOWED_ORIGINS |
| CookieSettings | `COOKIE_` | NAME, PATH, HTTPONLY, SECURE, SAMESITE |
| SmtpSettings | `SMTP_` | HOST, PORT, USERNAME, PASSWORD, FROM_EMAIL |
| VerificationSettings | `VERIFICATION_` | CODE_TTL_MIN=10, RESEND_COOLDOWN_SEC=60 |

---

## How to Add a New Feature (Pattern Reference)

### Adding a new endpoint (full CQRS path):

1. **Entity** → `src/app/core/common/entities/` (if new table needed)
2. **Port** → `src/app/core/commands/ports/` (TxStorage) or `src/app/core/queries/ports/` (Reader)
3. **Command/Query** → `src/app/core/commands/` or `src/app/core/queries/`
4. **Query Model** → `src/app/core/queries/models/` (for read endpoints)
5. **Adapter** → `src/app/infrastructure/adapters/` (SQLAlchemy implementation)
6. **Table Mapping** → `src/app/infrastructure/persistence_sqla/mappings/` (if new table)
7. **Migration** → `alembic revision --autogenerate`
8. **HTTP Endpoint** → `src/app/presentation/http/{module}/` (ErrorAwareRouter + error_map with AuthenticationError)
9. **Router Registration** → include in module's `router.py`
10. **DI Registration** → `src/app/main/ioc/core.py` (provide command/query + adapter)
