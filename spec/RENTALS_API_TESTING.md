# Rentals Module — API Testing Guide

> Complete curl-based test plan for all rental endpoints.
> Run the server first, then execute these requests in order.
> Base URL: `http://localhost:8000/api/v1`

---

## 0. Prerequisites

### 0.1 Login

```bash
curl -v -X POST http://localhost:8000/api/v1/account/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "your_password"
  }' \
  -c cookies.txt
```

**Expected:** `204 No Content` + a `Set-Cookie` saved to `cookies.txt`.

> Use `-b cookies.txt` on every subsequent request.

### 0.2 Required IDs

The rentals flow needs four prior IDs. Capture them before starting:

```bash
export ORG_ID="paste-organization-uuid"
export VEHICLE_ID="paste-vehicle-uuid"          # must belong to ORG_ID, not in a current rental
export CLIENT_ID="paste-verified-client-uuid"   # must belong to ORG_ID, blacklist=false
export MANAGER_ID="paste-manager-user-uuid"     # optional, may be null
```

If these don't exist yet, create them via the vehicle and client testing guides first.

### 0.3 State machine cheat sheet

```
        ┌──────────┐
        │ PENDING  │  ◄── create (default initial status)
        └────┬─────┘
             │ transition / implicit
        ┌────▼──────┐
        │ CONFIRMED │
        └────┬──────┘
             │ checkin
        ┌────▼──┐
        │ ACTIVE│
        └────┬──┘
             │ checkout
        ┌────▼──────┐
        │ RETURNING │
        └────┬──────┘
             │ complete
        ┌────▼──────┐
        │ COMPLETED │  ← terminal
        └───────────┘

      Any non-terminal → CANCELLED (terminal) via cancel
      ACTIVE → can extend (stays ACTIVE)
      Any  → DISPUTED (terminal) via transition
```

`InvalidRentalStatusTransitionError` → HTTP **409** for any disallowed move.

---

## 1. Create rental

```
POST /rentals/
Permission: rental.create
```

### 1.1 Create — minimal required fields

```bash
curl -s -X POST http://localhost:8000/api/v1/rentals/ \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d "{
    \"organization_id\": \"$ORG_ID\",
    \"vehicle_id\": \"$VEHICLE_ID\",
    \"client_id\": \"$CLIENT_ID\",
    \"booking_type\": \"daily\",
    \"scheduled_start\": \"2026-07-01T09:00:00Z\",
    \"scheduled_end\":   \"2026-07-05T09:00:00Z\",
    \"base_rate\": \"15000\",
    \"rate_type\": \"per_day\",
    \"estimated_total\": \"60000\",
    \"deposit_type\": \"cash\",
    \"deposit_amount\": \"50000\"
  }" | python3 -m json.tool
```

**Expected:** `201 Created`
```json
{ "id": "uuid", "created_at": "2026-..." }
```

```bash
export RENTAL_ID="paste-uuid-here"
```

### 1.2 Create — full body (all optional fields)

```bash
curl -s -X POST http://localhost:8000/api/v1/rentals/ \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d "{
    \"organization_id\": \"$ORG_ID\",
    \"vehicle_id\": \"$VEHICLE_ID\",
    \"client_id\": \"$CLIENT_ID\",
    \"manager_id\": \"$MANAGER_ID\",
    \"booking_type\": \"daily\",
    \"scheduled_start\": \"2026-08-01T09:00:00Z\",
    \"scheduled_end\":   \"2026-08-08T09:00:00Z\",
    \"base_rate\": \"15000\",
    \"rate_type\": \"per_day\",
    \"estimated_total\": \"105000\",
    \"discount_code\": \"SUMMER10\",
    \"discount_amount\": \"10500\",
    \"deposit_type\": \"card_hold\",
    \"deposit_amount\": \"50000\",
    \"prepayment_amount\": \"30000\",
    \"prepayment_status\": \"paid\",
    \"notes\": \"VIP client, deliver to airport\"
  }" | python3 -m json.tool
```

**Expected:** `201 Created`.

### 1.3 Create — overlapping dates ⇒ 409

Reuse the same `VEHICLE_ID` and a window that overlaps with 1.1.

```bash
curl -s -o /dev/null -w "%{http_code}\n" -X POST http://localhost:8000/api/v1/rentals/ \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d "{
    \"organization_id\": \"$ORG_ID\",
    \"vehicle_id\": \"$VEHICLE_ID\",
    \"client_id\": \"$CLIENT_ID\",
    \"booking_type\": \"daily\",
    \"scheduled_start\": \"2026-07-03T09:00:00Z\",
    \"scheduled_end\":   \"2026-07-04T09:00:00Z\",
    \"base_rate\": \"15000\",
    \"rate_type\": \"per_day\",
    \"estimated_total\": \"15000\",
    \"deposit_type\": \"cash\",
    \"deposit_amount\": \"50000\"
  }"
```

**Expected:** `409` (RentalDateOverlapError).

### 1.4 Create — missing required field ⇒ 422

```bash
curl -s -o /dev/null -w "%{http_code}\n" -X POST http://localhost:8000/api/v1/rentals/ \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d "{ \"organization_id\": \"$ORG_ID\" }"
```

**Expected:** `422 Unprocessable Entity` (FastAPI validation).

### 1.5 Create — unauthenticated ⇒ 401

```bash
curl -s -o /dev/null -w "%{http_code}\n" -X POST http://localhost:8000/api/v1/rentals/ \
  -H "Content-Type: application/json" \
  -d "{ \"organization_id\": \"$ORG_ID\" }"
```

**Expected:** `401`.

### 1.6 Create — user without `rental.create` ⇒ 403

Log in as a viewer-only user, then run 1.1. **Expected:** `403`.

---

## 2. List rentals

```
GET /rentals/
```

### 2.1 List — by org

```bash
curl -s -X GET "http://localhost:8000/api/v1/rentals/?organization_id=$ORG_ID" \
  -b cookies.txt | python3 -m json.tool | head -40
```

**Expected:** `200`, JSON object with a list of rentals.

### 2.2 List — filter by status

```bash
curl -s -X GET "http://localhost:8000/api/v1/rentals/?organization_id=$ORG_ID&status=pending" \
  -b cookies.txt | python3 -m json.tool | head -40
```

**Expected:** `200`. All returned rentals have `status == "pending"`.

### 2.3 List — filter by vehicle

```bash
curl -s -X GET "http://localhost:8000/api/v1/rentals/?organization_id=$ORG_ID&vehicle_id=$VEHICLE_ID" \
  -b cookies.txt | python3 -m json.tool | head -40
```

### 2.4 List — filter by client

```bash
curl -s -X GET "http://localhost:8000/api/v1/rentals/?organization_id=$ORG_ID&client_id=$CLIENT_ID" \
  -b cookies.txt | python3 -m json.tool | head -40
```

### 2.5 List — date window

```bash
curl -s -X GET "http://localhost:8000/api/v1/rentals/?organization_id=$ORG_ID&date_from=2026-07-01T00:00:00Z&date_to=2026-07-31T23:59:59Z" \
  -b cookies.txt | python3 -m json.tool | head -40
```

---

## 3. Get one rental

```
GET /rentals/{rental_id}
```

### 3.1 Existing

```bash
curl -s -X GET "http://localhost:8000/api/v1/rentals/$RENTAL_ID" \
  -b cookies.txt | python3 -m json.tool
```

**Expected:** `200`, full rental object.

### 3.2 Unknown ID ⇒ 404

```bash
curl -s -o /dev/null -w "%{http_code}\n" -X GET \
  "http://localhost:8000/api/v1/rentals/00000000-0000-0000-0000-000000000000" \
  -b cookies.txt
```

**Expected:** `404`.

---

## 4. Booking requests

```
GET /rentals/booking-requests?organization_id=
```

Returns pending bookings awaiting confirmation.

```bash
curl -s -X GET "http://localhost:8000/api/v1/rentals/booking-requests?organization_id=$ORG_ID" \
  -b cookies.txt | python3 -m json.tool | head -40
```

**Expected:** `200`. The rental from 1.1 should appear if it's still `pending`.

---

## 5. Calendar

```
GET /rentals/calendar?organization_id=&month=YYYY-MM
```

### 5.1 Current month

```bash
curl -s -X GET "http://localhost:8000/api/v1/rentals/calendar?organization_id=$ORG_ID&month=2026-07" \
  -b cookies.txt | python3 -m json.tool | head -60
```

**Expected:** `200`. Contains entries for July's rentals.

### 5.2 December edge (year boundary)

```bash
curl -s -X GET "http://localhost:8000/api/v1/rentals/calendar?organization_id=$ORG_ID&month=2026-12" \
  -b cookies.txt | python3 -m json.tool | head -40
```

**Expected:** `200`. Validates the `DECEMBER` branch (`month_end = Jan 1 next year`).

### 5.3 Malformed month ⇒ 422

```bash
curl -s -o /dev/null -w "%{http_code}\n" -X GET \
  "http://localhost:8000/api/v1/rentals/calendar?organization_id=$ORG_ID&month=2026/07" \
  -b cookies.txt
```

**Expected:** `422` or `400` (parser failure).

---

## 6. Returns queue

```
GET /rentals/returns-queue?organization_id=
```

Returns rentals due back within ~48h.

```bash
curl -s -X GET "http://localhost:8000/api/v1/rentals/returns-queue?organization_id=$ORG_ID" \
  -b cookies.txt | python3 -m json.tool | head -40
```

**Expected:** `200`. To populate, create a rental whose `scheduled_end` is within the next 2 days and transition it to `active`.

---

## 7. Update rental (PATCH)

```
PATCH /rentals/{rental_id}
Permission: rental.update
```

### 7.1 Partial update — change notes only

```bash
curl -s -o /dev/null -w "%{http_code}\n" -X PATCH "http://localhost:8000/api/v1/rentals/$RENTAL_ID" \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{ "notes": "Updated notes via PATCH" }'
```

**Expected:** `204`. Re-fetch via 3.1 and confirm.

### 7.2 Partial update — change schedule

```bash
curl -s -o /dev/null -w "%{http_code}\n" -X PATCH "http://localhost:8000/api/v1/rentals/$RENTAL_ID" \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "scheduled_start": "2026-07-01T10:00:00Z",
    "scheduled_end":   "2026-07-06T10:00:00Z",
    "estimated_total": 75000
  }'
```

**Expected:** `204`.

### 7.3 Unknown rental ⇒ 404

```bash
curl -s -o /dev/null -w "%{http_code}\n" -X PATCH \
  "http://localhost:8000/api/v1/rentals/00000000-0000-0000-0000-000000000000" \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{ "notes": "x" }'
```

**Expected:** `404`.

---

## 8. Transition status

```
POST /rentals/{rental_id}/transition
Permission: rental.update
Body: { "status": <RentalStatus> }
```

### 8.1 pending → confirmed

```bash
curl -s -o /dev/null -w "%{http_code}\n" -X POST \
  "http://localhost:8000/api/v1/rentals/$RENTAL_ID/transition" \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{ "status": "confirmed" }'
```

**Expected:** `204`.

### 8.2 confirmed → pending (illegal) ⇒ 409

```bash
curl -s -o /dev/null -w "%{http_code}\n" -X POST \
  "http://localhost:8000/api/v1/rentals/$RENTAL_ID/transition" \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{ "status": "pending" }'
```

**Expected:** `409` (InvalidRentalStatusTransitionError).

### 8.3 Force to disputed

```bash
# Only run against a throwaway rental — disputed is terminal.
curl -s -o /dev/null -w "%{http_code}\n" -X POST \
  "http://localhost:8000/api/v1/rentals/$THROWAWAY_RENTAL_ID/transition" \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{ "status": "disputed" }'
```

**Expected:** `204`.

---

## 9. Checkin (pickup)

```
POST /rentals/{rental_id}/checkin
Permission: rental.update
Body: { "checkin_data": { ...arbitrary JSON... } }
```

Precondition: rental status must be `confirmed`.

```bash
curl -s -o /dev/null -w "%{http_code}\n" -X POST \
  "http://localhost:8000/api/v1/rentals/$RENTAL_ID/checkin" \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "checkin_data": {
      "odometer": 45230,
      "fuel_level": "full",
      "exterior_photos": ["s3://photo1.jpg", "s3://photo2.jpg"],
      "damage_notes": ""
    }
  }'
```

**Expected:** `204`. Status moves to `active`. Re-fetch and confirm.

### 9.1 Checkin in wrong status ⇒ 409

Run 9 against a `pending` rental. **Expected:** `409`.

---

## 10. Checkout (return)

```
POST /rentals/{rental_id}/checkout
Permission: rental.update
Body: { "checkout_data": { ...arbitrary JSON... } }
```

Precondition: status `active`.

```bash
curl -s -o /dev/null -w "%{http_code}\n" -X POST \
  "http://localhost:8000/api/v1/rentals/$RENTAL_ID/checkout" \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "checkout_data": {
      "odometer": 45720,
      "fuel_level": "three_quarters",
      "exterior_photos": ["s3://return1.jpg"],
      "damage_notes": "minor scratch on rear bumper"
    }
  }'
```

**Expected:** `204`. Status moves to `returning`.

---

## 11. Complete rental

```
POST /rentals/{rental_id}/complete
Permission: rental.update
```

Precondition: status `returning`.

```bash
curl -s -o /dev/null -w "%{http_code}\n" -X POST \
  "http://localhost:8000/api/v1/rentals/$RENTAL_ID/complete" \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "actual_total": "78000",
    "late_fee": "3000",
    "mileage_surcharge": "0",
    "fuel_charge": "1500",
    "wash_fee": "1000",
    "damage_charge": "0",
    "fine_charge": "0",
    "deposit_refund_amount": "50000"
  }'
```

**Expected:** `204`. Status moves to `completed`.

### 11.1 Defaults — all charges zero

```bash
curl -s -o /dev/null -w "%{http_code}\n" -X POST \
  "http://localhost:8000/api/v1/rentals/$RENTAL_ID_2/complete" \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{ "actual_total": "60000" }'
```

**Expected:** `204` — all optional fees default to `0`.

---

## 12. Cancel

```
POST /rentals/{rental_id}/cancel
Permission: rental.update
Body: { "reason"?: string }
```

### 12.1 Cancel pending — with reason

```bash
curl -s -o /dev/null -w "%{http_code}\n" -X POST \
  "http://localhost:8000/api/v1/rentals/$PENDING_RENTAL_ID/cancel" \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{ "reason": "Client cancelled - found alternative" }'
```

**Expected:** `204`. Status → `cancelled`.

### 12.2 Cancel completed (illegal) ⇒ 409

```bash
curl -s -o /dev/null -w "%{http_code}\n" -X POST \
  "http://localhost:8000/api/v1/rentals/$COMPLETED_RENTAL_ID/cancel" \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{}'
```

**Expected:** `409`.

---

## 13. Extend (active rental)

```
POST /rentals/{rental_id}/extend
Permission: rental.update
```

Precondition: status `active`.

```bash
curl -s -o /dev/null -w "%{http_code}\n" -X POST \
  "http://localhost:8000/api/v1/rentals/$ACTIVE_RENTAL_ID/extend" \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "new_scheduled_end": "2026-07-08T09:00:00Z",
    "new_estimated_total": "90000"
  }'
```

**Expected:** `204`. Rental stays `active`; an extension request is recorded.

### 13.1 Extend non-active ⇒ 409

```bash
curl -s -o /dev/null -w "%{http_code}\n" -X POST \
  "http://localhost:8000/api/v1/rentals/$PENDING_RENTAL_ID/extend" \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "new_scheduled_end": "2026-07-08T09:00:00Z",
    "new_estimated_total": "90000"
  }'
```

**Expected:** `409`.

---

## 14. Extension requests — list

```
GET /rentals/extension-requests?organization_id=
```

```bash
curl -s -X GET "http://localhost:8000/api/v1/rentals/extension-requests?organization_id=$ORG_ID" \
  -b cookies.txt | python3 -m json.tool | head -40
```

**Expected:** `200`. The extension from §13 should appear.

```bash
export EXT_REQ_ID="paste-extension-request-uuid"
```

---

## 15. Approve / reject extension

> **Note:** the URL path takes a `{rental_id}` placeholder but the handler treats it as the extension-request ID (see `approve_extension.py:37` and `reject_extension.py:45`). Use `EXT_REQ_ID` here.

### 15.1 Approve

```bash
curl -s -o /dev/null -w "%{http_code}\n" -X POST \
  "http://localhost:8000/api/v1/rentals/$EXT_REQ_ID/extension/approve" \
  -b cookies.txt
```

**Expected:** `200`.

### 15.2 Approve again ⇒ 409

```bash
curl -s -o /dev/null -w "%{http_code}\n" -X POST \
  "http://localhost:8000/api/v1/rentals/$EXT_REQ_ID/extension/approve" \
  -b cookies.txt
```

**Expected:** `409` (InvalidExtensionRequestStatusError).

### 15.3 Reject — with rejection reason

```bash
curl -s -o /dev/null -w "%{http_code}\n" -X POST \
  "http://localhost:8000/api/v1/rentals/$EXT_REQ_ID_2/extension/reject" \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{ "rejection_reason": "Vehicle reserved by another client" }'
```

**Expected:** `200`.

### 15.4 Reject — missing rejection_reason ⇒ 422

```bash
curl -s -o /dev/null -w "%{http_code}\n" -X POST \
  "http://localhost:8000/api/v1/rentals/$EXT_REQ_ID_3/extension/reject" \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{}'
```

**Expected:** `422`.

### 15.5 Unknown extension request ⇒ 404

```bash
curl -s -o /dev/null -w "%{http_code}\n" -X POST \
  "http://localhost:8000/api/v1/rentals/00000000-0000-0000-0000-000000000000/extension/approve" \
  -b cookies.txt
```

**Expected:** `404`.

---

## 16. Full happy-path replay (E2E)

Run end-to-end against a fresh rental:

```bash
# 1. Create
RENTAL_ID=$(curl -s -X POST http://localhost:8000/api/v1/rentals/ \
  -H "Content-Type: application/json" -b cookies.txt \
  -d "{ ...minimal-body... }" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")

# 2. Confirm
curl -s -X POST "http://localhost:8000/api/v1/rentals/$RENTAL_ID/transition" \
  -H "Content-Type: application/json" -b cookies.txt -d '{"status":"confirmed"}'

# 3. Checkin
curl -s -X POST "http://localhost:8000/api/v1/rentals/$RENTAL_ID/checkin" \
  -H "Content-Type: application/json" -b cookies.txt \
  -d '{"checkin_data":{"odometer":1000}}'

# 4. Checkout
curl -s -X POST "http://localhost:8000/api/v1/rentals/$RENTAL_ID/checkout" \
  -H "Content-Type: application/json" -b cookies.txt \
  -d '{"checkout_data":{"odometer":1500}}'

# 5. Complete
curl -s -X POST "http://localhost:8000/api/v1/rentals/$RENTAL_ID/complete" \
  -H "Content-Type: application/json" -b cookies.txt \
  -d '{"actual_total":"60000"}'

# 6. Verify terminal state
curl -s "http://localhost:8000/api/v1/rentals/$RENTAL_ID" \
  -b cookies.txt | python3 -m json.tool | grep status
```

Expected final status: `"status": "completed"`.

---

## Coverage matrix

| Endpoint | Method | Section | Golden | 401 | 403 | 404 | 409 | 422 |
|---|---|---|---|---|---|---|---|---|
| `/rentals/` | POST | §1 | 1.1, 1.2 | 1.5 | 1.6 | — | 1.3 | 1.4 |
| `/rentals/` | GET | §2 | 2.1–2.5 | (impl.) | — | — | — | — |
| `/rentals/{id}` | GET | §3 | 3.1 | — | — | 3.2 | — | — |
| `/rentals/booking-requests` | GET | §4 | §4 | — | — | — | — | — |
| `/rentals/calendar` | GET | §5 | 5.1, 5.2 | — | — | — | — | 5.3 |
| `/rentals/returns-queue` | GET | §6 | §6 | — | — | — | — | — |
| `/rentals/{id}` | PATCH | §7 | 7.1, 7.2 | (impl.) | — | 7.3 | — | — |
| `/rentals/{id}/transition` | POST | §8 | 8.1, 8.3 | — | — | — | 8.2 | — |
| `/rentals/{id}/checkin` | POST | §9 | §9 | — | — | — | 9.1 | — |
| `/rentals/{id}/checkout` | POST | §10 | §10 | — | — | — | — | — |
| `/rentals/{id}/complete` | POST | §11 | §11, 11.1 | — | — | — | — | — |
| `/rentals/{id}/cancel` | POST | §12 | 12.1 | — | — | — | 12.2 | — |
| `/rentals/{id}/extend` | POST | §13 | §13 | — | — | — | 13.1 | — |
| `/rentals/extension-requests` | GET | §14 | §14 | — | — | — | — | — |
| `/rentals/{id}/extension/approve` | POST | §15 | 15.1 | — | — | 15.5 | 15.2 | — |
| `/rentals/{id}/extension/reject` | POST | §15 | 15.3 | — | — | — | — | 15.4 |

Authentication (401) is enforced uniformly by the auth-cookie middleware — covered once in §1.5 and assumed for the rest.

---

## Known follow-ups (file in summary)

- Permission test cases (`rental.update` 403s) require a viewer-only seeded user. If none exists, see ROADMAP — `tooling: seed permission-scoped test users`.
- The extension endpoint path uses `{rental_id}` as the placeholder name but operates on extension-request IDs. Consider renaming the path parameter to `{extension_request_id}` in a future cleanup PR for API clarity.
- `Returns queue` window (2 days) is hard-coded — test against a manually-fast-forwarded rental rather than relying on real time.
