# Vehicle Module — API Testing Guide

> Complete curl-based test plan for all vehicle endpoints.
> Run the server first, then execute these requests in order.
> Base URL: `http://localhost:8000/api/v1`

---

## 0. Prerequisites: Authentication

All vehicle endpoints require authentication. First, log in to get a session cookie.

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

**Expected:** `204 No Content` + a `Set-Cookie` header saved to `cookies.txt`

> Use `-b cookies.txt` on all subsequent requests.

---

## 1. Create Vehicle

```
POST /vehicles/
Permission: fleet.create
```

### 1.1 Create vehicle — minimal required fields

```bash
curl -s -X POST http://localhost:8000/api/v1/vehicles/ \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "organization_id": "YOUR_ORG_ID",
    "make": "Hyundai",
    "model": "Accent",
    "year": 2023,
    "license_plate": "066 ABC 01",
    "color": "white",
    "category": "Эконом",
    "fuel_type": "petrol",
    "transmission": "automatic"
  }' | python3 -m json.tool
```

**Expected:** `201 Created`
```json
{
  "id": "uuid-of-new-vehicle",
  "created_at": "2026-05-19T..."
}
```

**Save the returned `id` — you'll need it for all subsequent tests:**
```bash
export VEHICLE_ID="paste-uuid-here"
```

### 1.2 Create vehicle — all fields

```bash
curl -s -X POST http://localhost:8000/api/v1/vehicles/ \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "organization_id": "YOUR_ORG_ID",
    "nickname": "Камри 777",
    "make": "Toyota",
    "model": "Camry",
    "year": 2024,
    "vin": "JTDKN3DU5A0000001",
    "license_plate": "777 KAM 01",
    "color": "black",
    "category": "Бизнес",
    "fuel_type": "petrol",
    "transmission": "automatic",
    "current_mileage": 15000,
    "purchase_price": 12500000,
    "purchase_date": "2024-01-15",
    "insurance_expiry": "2026-01-15",
    "inspection_expiry": "2026-06-15",
    "gps_device_id": "GPS-001",
    "branch_id": null,
    "photos": ["https://example.com/photo1.jpg"],
    "features": {"sunroof": true, "heated_seats": true},
    "pricing_override": {"per_day": 25000}
  }' | python3 -m json.tool
```

**Expected:** `201 Created`

### 1.3 Create vehicle — validation errors

**Missing required field `make`:**
```bash
curl -s -X POST http://localhost:8000/api/v1/vehicles/ \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "organization_id": "YOUR_ORG_ID",
    "model": "Accent",
    "year": 2023,
    "license_plate": "001 TEST 01",
    "color": "white",
    "category": "Эконом",
    "fuel_type": "petrol",
    "transmission": "automatic"
  }' | python3 -m json.tool
```

**Expected:** `422 Unprocessable Entity` with validation details

**Invalid fuel_type:**
```bash
curl -s -X POST http://localhost:8000/api/v1/vehicles/ \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "organization_id": "YOUR_ORG_ID",
    "make": "Hyundai",
    "model": "Accent",
    "year": 2023,
    "license_plate": "002 TEST 01",
    "color": "white",
    "category": "Эконом",
    "fuel_type": "nuclear",
    "transmission": "automatic"
  }' | python3 -m json.tool
```

**Expected:** `422` — fuel_type must be one of: `petrol`, `diesel`, `gas`, `electric`, `hybrid`

**Invalid transmission:**
```bash
# transmission must be: "manual" or "automatic"
```

---

## 2. List Vehicles

```
GET /vehicles/
Permission: (read, authenticated)
```

### 2.1 List all vehicles for organization

```bash
curl -s "http://localhost:8000/api/v1/vehicles/?organization_id=YOUR_ORG_ID" \
  -b cookies.txt | python3 -m json.tool
```

**Expected:** `200 OK`
```json
{
  "vehicles": [
    {
      "id": "uuid",
      "organization_id": "uuid",
      "nickname": "Камри 777",
      "make": "Toyota",
      "model": "Camry",
      "year": 2024,
      "vin": "JTDKN3DU5A0000001",
      "license_plate": "777 KAM 01",
      "color": "black",
      "category": "Бизнес",
      "status": "available",
      "fuel_type": "petrol",
      "transmission": "automatic",
      "current_mileage": 15000,
      "purchase_price": "12500000",
      "purchase_date": "2024-01-15",
      "insurance_expiry": "2026-01-15",
      "inspection_expiry": "2026-06-15",
      "gps_device_id": "GPS-001",
      "current_latitude": null,
      "current_longitude": null,
      "current_fuel_level": null,
      "branch_id": null,
      "photos": ["https://example.com/photo1.jpg"],
      "features": {"sunroof": true, "heated_seats": true},
      "pricing_override": {"per_day": 25000},
      "created_at": "2026-05-19T...",
      "updated_at": "2026-05-19T..."
    }
  ],
  "total": 2
}
```

### 2.2 Filter by status

```bash
curl -s "http://localhost:8000/api/v1/vehicles/?organization_id=YOUR_ORG_ID&status=available" \
  -b cookies.txt | python3 -m json.tool
```

**Valid status values:** `available`, `reserved`, `rented`, `returning`, `in_service`, `in_wash`, `decommissioned`, `sold`

### 2.3 Filter by category

```bash
curl -s "http://localhost:8000/api/v1/vehicles/?organization_id=YOUR_ORG_ID&category=Эконом" \
  -b cookies.txt | python3 -m json.tool
```

### 2.4 Search by text

```bash
curl -s "http://localhost:8000/api/v1/vehicles/?organization_id=YOUR_ORG_ID&search=Camry" \
  -b cookies.txt | python3 -m json.tool
```

### 2.5 Filter by branch

```bash
curl -s "http://localhost:8000/api/v1/vehicles/?organization_id=YOUR_ORG_ID&branch_id=BRANCH_UUID" \
  -b cookies.txt | python3 -m json.tool
```

### 2.6 Filter by investor

```bash
curl -s "http://localhost:8000/api/v1/vehicles/?organization_id=YOUR_ORG_ID&investor_id=INVESTOR_UUID" \
  -b cookies.txt | python3 -m json.tool
```

### 2.7 Combine filters

```bash
curl -s "http://localhost:8000/api/v1/vehicles/?organization_id=YOUR_ORG_ID&status=available&category=Бизнес&search=Toyota" \
  -b cookies.txt | python3 -m json.tool
```

### 2.8 Missing organization_id

```bash
curl -s "http://localhost:8000/api/v1/vehicles/" \
  -b cookies.txt | python3 -m json.tool
```

**Expected:** `422` — organization_id is required

---

## 3. Get Vehicle by ID

```
GET /vehicles/{vehicle_id}
Permission: (read, authenticated)
```

### 3.1 Get existing vehicle

```bash
curl -s "http://localhost:8000/api/v1/vehicles/$VEHICLE_ID" \
  -b cookies.txt | python3 -m json.tool
```

**Expected:** `200 OK` with full VehicleQm object (same shape as list item)

### 3.2 Get non-existent vehicle

```bash
curl -s "http://localhost:8000/api/v1/vehicles/00000000-0000-0000-0000-000000000000" \
  -b cookies.txt | python3 -m json.tool
```

**Expected:** `404 Not Found`
```json
{
  "detail": "Vehicle not found."
}
```

### 3.3 Invalid UUID format

```bash
curl -s "http://localhost:8000/api/v1/vehicles/not-a-uuid" \
  -b cookies.txt | python3 -m json.tool
```

**Expected:** `422 Unprocessable Entity`

---

## 4. Update Vehicle (Partial)

```
PATCH /vehicles/{vehicle_id}
Permission: fleet.update
```

### 4.1 Update single field

```bash
curl -s -X PATCH "http://localhost:8000/api/v1/vehicles/$VEHICLE_ID" \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "nickname": "Акцент 066 Updated"
  }'
```

**Expected:** `204 No Content`

**Verify:**
```bash
curl -s "http://localhost:8000/api/v1/vehicles/$VEHICLE_ID" \
  -b cookies.txt | python3 -m json.tool | grep nickname
```

### 4.2 Update multiple fields

```bash
curl -s -X PATCH "http://localhost:8000/api/v1/vehicles/$VEHICLE_ID" \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "color": "silver",
    "current_mileage": 25000,
    "insurance_expiry": "2027-01-15",
    "gps_device_id": "GPS-002"
  }'
```

**Expected:** `204 No Content`

### 4.3 Update nullable fields to null

```bash
curl -s -X PATCH "http://localhost:8000/api/v1/vehicles/$VEHICLE_ID" \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "nickname": null,
    "vin": null,
    "gps_device_id": null
  }'
```

**Expected:** `204 No Content`

### 4.4 Update features and pricing_override (JSON fields)

```bash
curl -s -X PATCH "http://localhost:8000/api/v1/vehicles/$VEHICLE_ID" \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "features": {"sunroof": true, "leather": true, "navigation": true},
    "pricing_override": {"per_day": 20000, "per_week": 120000}
  }'
```

**Expected:** `204 No Content`

### 4.5 Update non-existent vehicle

```bash
curl -s -X PATCH "http://localhost:8000/api/v1/vehicles/00000000-0000-0000-0000-000000000000" \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{"color": "red"}'
```

**Expected:** `404 Not Found`

### 4.6 Empty body (no fields set)

```bash
curl -s -X PATCH "http://localhost:8000/api/v1/vehicles/$VEHICLE_ID" \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{}'
```

**Expected:** `204 No Content` (no-op, nothing changes)

---

## 5. Change Vehicle Status

```
PATCH /vehicles/{vehicle_id}/status
Permission: fleet.update
```

### Status Transition Map

```
available → reserved, in_service, in_wash, decommissioned, sold
reserved  → rented, available
rented    → returning
returning → available, in_service, in_wash
in_service → available, decommissioned, sold
in_wash   → available
decommissioned → sold
sold      → (nothing — terminal state)
```

### 5.1 Valid transition: available → reserved

```bash
curl -s -X PATCH "http://localhost:8000/api/v1/vehicles/$VEHICLE_ID/status" \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{"status": "reserved"}'
```

**Expected:** `204 No Content`

### 5.2 Valid transition: reserved → rented

```bash
curl -s -X PATCH "http://localhost:8000/api/v1/vehicles/$VEHICLE_ID/status" \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{"status": "rented"}'
```

**Expected:** `204 No Content`

### 5.3 Valid transition: rented → returning

```bash
curl -s -X PATCH "http://localhost:8000/api/v1/vehicles/$VEHICLE_ID/status" \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{"status": "returning"}'
```

**Expected:** `204 No Content`

### 5.4 Valid transition: returning → available

```bash
curl -s -X PATCH "http://localhost:8000/api/v1/vehicles/$VEHICLE_ID/status" \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{"status": "available"}'
```

**Expected:** `204 No Content`

### 5.5 Invalid transition: available → rented (must go through reserved first)

```bash
curl -s -X PATCH "http://localhost:8000/api/v1/vehicles/$VEHICLE_ID/status" \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{"status": "rented"}'
```

**Expected:** `409 Conflict`
```json
{
  "detail": "Cannot transition from 'available' to 'rented'."
}
```

### 5.6 Invalid transition: available → returning

```bash
curl -s -X PATCH "http://localhost:8000/api/v1/vehicles/$VEHICLE_ID/status" \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{"status": "returning"}'
```

**Expected:** `409 Conflict`

### 5.7 Service flow: available → in_service → available

```bash
# Send to service
curl -s -X PATCH "http://localhost:8000/api/v1/vehicles/$VEHICLE_ID/status" \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{"status": "in_service"}'
# Expected: 204

# Return from service
curl -s -X PATCH "http://localhost:8000/api/v1/vehicles/$VEHICLE_ID/status" \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{"status": "available"}'
# Expected: 204
```

### 5.8 Wash flow: available → in_wash → available

```bash
curl -s -X PATCH "http://localhost:8000/api/v1/vehicles/$VEHICLE_ID/status" \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{"status": "in_wash"}'
# Expected: 204

curl -s -X PATCH "http://localhost:8000/api/v1/vehicles/$VEHICLE_ID/status" \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{"status": "available"}'
# Expected: 204
```

### 5.9 Decommission and sell flow

```bash
curl -s -X PATCH "http://localhost:8000/api/v1/vehicles/$VEHICLE_ID/status" \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{"status": "decommissioned"}'
# Expected: 204

curl -s -X PATCH "http://localhost:8000/api/v1/vehicles/$VEHICLE_ID/status" \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{"status": "sold"}'
# Expected: 204

# sold is terminal — any further transition should fail
curl -s -X PATCH "http://localhost:8000/api/v1/vehicles/$VEHICLE_ID/status" \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{"status": "available"}'
# Expected: 409 Conflict
```

### 5.10 Invalid status value

```bash
curl -s -X PATCH "http://localhost:8000/api/v1/vehicles/$VEHICLE_ID/status" \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{"status": "destroyed"}'
```

**Expected:** `422` — invalid enum value

---

## 6. Bulk Change Status

```
POST /vehicles/bulk-status
Permission: fleet.update
```

### 6.1 Bulk change — all succeed

```bash
curl -s -X POST "http://localhost:8000/api/v1/vehicles/bulk-status" \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "vehicle_ids": ["VEHICLE_UUID_1", "VEHICLE_UUID_2"],
    "status": "in_service"
  }' | python3 -m json.tool
```

**Expected:** `200 OK`
```json
{
  "results": [
    {"vehicle_id": "uuid1", "success": true, "error": null},
    {"vehicle_id": "uuid2", "success": true, "error": null}
  ],
  "succeeded": 2,
  "failed": 0
}
```

### 6.2 Bulk change — partial failure

```bash
curl -s -X POST "http://localhost:8000/api/v1/vehicles/bulk-status" \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "vehicle_ids": ["VALID_UUID", "00000000-0000-0000-0000-000000000000"],
    "status": "available"
  }' | python3 -m json.tool
```

**Expected:** `200 OK` with mixed results — one success, one "Vehicle not found"

### 6.3 Bulk change — invalid transition for some

If some vehicles are `available` and you try to set `returning`, those will fail with transition errors while valid ones succeed.

---

## 7. Vehicle Photos

```
POST   /vehicles/{vehicle_id}/photos        — Add photo
DELETE /vehicles/{vehicle_id}/photos/{index} — Remove photo
Permission: fleet.update
Max photos: 10
```

### 7.1 Add a photo

```bash
curl -s -X POST "http://localhost:8000/api/v1/vehicles/$VEHICLE_ID/photos" \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{"url": "https://example.com/car-front.jpg"}' | python3 -m json.tool
```

**Expected:** `200 OK` — returns the full photos array
```json
["https://example.com/car-front.jpg"]
```

### 7.2 Add more photos

```bash
curl -s -X POST "http://localhost:8000/api/v1/vehicles/$VEHICLE_ID/photos" \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{"url": "https://example.com/car-side.jpg"}' | python3 -m json.tool

curl -s -X POST "http://localhost:8000/api/v1/vehicles/$VEHICLE_ID/photos" \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{"url": "https://example.com/car-back.jpg"}' | python3 -m json.tool
```

**Expected:** Array grows: `["car-front.jpg", "car-side.jpg", "car-back.jpg"]`

### 7.3 Remove photo by index

```bash
# Remove the second photo (index 1)
curl -s -X DELETE "http://localhost:8000/api/v1/vehicles/$VEHICLE_ID/photos/1" \
  -b cookies.txt | python3 -m json.tool
```

**Expected:** `200 OK` — returns array without the removed photo
```json
["https://example.com/car-front.jpg", "https://example.com/car-back.jpg"]
```

### 7.4 Remove photo — invalid index

```bash
curl -s -X DELETE "http://localhost:8000/api/v1/vehicles/$VEHICLE_ID/photos/99" \
  -b cookies.txt | python3 -m json.tool
```

**Expected:** `404 Not Found`

### 7.5 Add photo — exceeds limit (10)

Add 10 photos, then try an 11th:

```bash
# After 10 photos exist:
curl -s -X POST "http://localhost:8000/api/v1/vehicles/$VEHICLE_ID/photos" \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{"url": "https://example.com/photo-11.jpg"}' | python3 -m json.tool
```

**Expected:** `400 Bad Request`

---

## 8. Vehicle Financials

```
GET /vehicles/{vehicle_id}/financials?date_from=YYYY-MM-DD&date_to=YYYY-MM-DD
Permission: (read, authenticated)
```

### 8.1 Get financials for a period

```bash
curl -s "http://localhost:8000/api/v1/vehicles/$VEHICLE_ID/financials?date_from=2026-01-01&date_to=2026-05-19" \
  -b cookies.txt | python3 -m json.tool
```

**Expected:** `200 OK`
```json
{
  "total_revenue": "0.00",
  "total_expenses": "0.00",
  "net_profit": "0.00",
  "total_rentals": 0,
  "days_rented": 0,
  "days_in_period": 139,
  "utilization_percent": "0.00"
}
```

### 8.2 Missing date params

```bash
curl -s "http://localhost:8000/api/v1/vehicles/$VEHICLE_ID/financials" \
  -b cookies.txt | python3 -m json.tool
```

**Expected:** `422` — date_from and date_to are required

---

## 9. Vehicle Timeline

```
GET /vehicles/{vehicle_id}/timeline
Permission: (read, authenticated)
```

### 9.1 Get timeline

```bash
curl -s "http://localhost:8000/api/v1/vehicles/$VEHICLE_ID/timeline" \
  -b cookies.txt | python3 -m json.tool
```

**Expected:** `200 OK`
```json
{
  "events": [
    {
      "id": "uuid",
      "event_type": "rental",
      "event_date": "2026-05-10T...",
      "title": "Rental #...",
      "description": "...",
      "amount": "15000.00",
      "metadata": {}
    }
  ],
  "total": 1
}
```

For a new vehicle, `events` will be empty and `total` will be `0`.

---

## 10. Authentication & Permission Errors

### 10.1 No cookie / unauthenticated

```bash
curl -s -X GET "http://localhost:8000/api/v1/vehicles/?organization_id=YOUR_ORG_ID" \
  | python3 -m json.tool
```

**Expected:** `401 Unauthorized` or `403 Forbidden`

### 10.2 Insufficient permissions

If logged in as a user without `fleet.create`:

```bash
curl -s -X POST http://localhost:8000/api/v1/vehicles/ \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "organization_id": "YOUR_ORG_ID",
    "make": "Test",
    "model": "Car",
    "year": 2024,
    "license_plate": "TEST 001",
    "color": "red",
    "category": "test",
    "fuel_type": "petrol",
    "transmission": "manual"
  }' | python3 -m json.tool
```

**Expected:** `403 Forbidden`

---

## Quick Reference: Field Types & Enums

### CreateVehicleRequest fields

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `organization_id` | UUID | Yes | |
| `nickname` | string | No | Display name like "Камри 777" |
| `make` | string | Yes | Brand: "Hyundai", "Toyota" |
| `model` | string | Yes | "Accent", "Camry" |
| `year` | int | Yes | |
| `vin` | string | No | 17-char VIN |
| `license_plate` | string | Yes | |
| `color` | string | Yes | |
| `category` | string | Yes | Matches vehicle_categories |
| `fuel_type` | enum | Yes | `petrol`, `diesel`, `gas`, `electric`, `hybrid` |
| `transmission` | enum | Yes | `manual`, `automatic` |
| `current_mileage` | int | No | Default: 0 |
| `purchase_price` | decimal | No | |
| `purchase_date` | date | No | `YYYY-MM-DD` |
| `insurance_expiry` | date | No | `YYYY-MM-DD` |
| `inspection_expiry` | date | No | `YYYY-MM-DD` |
| `gps_device_id` | string | No | |
| `branch_id` | UUID | No | |
| `photos` | string[] | No | URLs |
| `features` | object | No | Free-form JSON |
| `pricing_override` | object | No | Free-form JSON |

### Vehicle statuses

| Status | Description |
|--------|-------------|
| `available` | Ready for rental (default on creation) |
| `reserved` | Booked but not yet picked up |
| `rented` | Currently with a client |
| `returning` | Client returning, pending inspection |
| `in_service` | Undergoing maintenance/repair |
| `in_wash` | Being washed/cleaned |
| `decommissioned` | Retired from fleet |
| `sold` | Sold — terminal state |

### Status transition diagram

```
                    ┌──────────────┐
                    │  available   │
                    └──┬──┬──┬──┬─┘
          ┌───────────┘  │  │  └──────────────┐
          ▼              ▼  ▼                  ▼
     ┌─────────┐   ┌─────────┐  ┌─────────┐  ┌──────┐
     │reserved │   │in_service│  │ in_wash │  │decom.│
     └────┬────┘   └────┬──┬─┘  └────┬────┘  └──┬───┘
          │             │  │         │           │
     ┌────▼────┐        │  │    ┌────▼────┐  ┌──▼───┐
     │ rented  │        │  └───►│available│  │ sold │
     └────┬────┘        │      └─────────┘  └──────┘
          │             │
     ┌────▼─────┐       │
     │returning ├───────┘
     └──┬───┬───┘
        │   │
        │   └──► in_wash ──► available
        └──────► available
```

---

## Checklist for Frontend Integration

- [ ] **Auth:** Login works, cookie is set and persists
- [ ] **Create:** Minimal + full payload both return `201` with `{id, created_at}`
- [ ] **Create validation:** Missing fields → `422`, invalid enums → `422`
- [ ] **List:** Returns `{vehicles: [...], total: N}`
- [ ] **List filters:** status, category, branch_id, investor_id, search all work
- [ ] **List combined filters:** Multiple filters at once
- [ ] **Get by ID:** Returns full vehicle object with all fields
- [ ] **Get 404:** Non-existent UUID → `404`
- [ ] **Update partial:** Single field update → `204`, verify change
- [ ] **Update null:** Setting nullable fields to null works
- [ ] **Update JSON fields:** features, pricing_override update correctly
- [ ] **Update 404:** Non-existent vehicle → `404`
- [ ] **Status change:** All valid transitions work → `204`
- [ ] **Status invalid:** Invalid transitions → `409`
- [ ] **Status terminal:** `sold` cannot transition → `409`
- [ ] **Bulk status:** Mixed success/failure returns per-item results
- [ ] **Photos add:** Returns updated array, up to 10
- [ ] **Photos remove:** By index, returns updated array
- [ ] **Photos limit:** 11th photo → `400`
- [ ] **Financials:** Returns revenue/expense/utilization for date range
- [ ] **Timeline:** Returns chronological events list
- [ ] **No auth:** All endpoints reject unauthenticated requests
- [ ] **No permission:** Write endpoints reject unauthorized users
