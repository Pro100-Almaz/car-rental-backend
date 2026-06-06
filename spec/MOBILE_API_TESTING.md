# Mobile Module — API Testing Guide

> Curl plan covering all 26 `/api/v1/mobile/...` endpoints from the perspective of a signed-up client. Pays special attention to `POST /mobile/rentals` (`submit_booking_request`) and `POST /mobile/rentals/{id}/cancel` (`cancel_own_rental`), both rewired by `USER_CLIENT_LINK_CLEANUP` to look up the client via `clients.user_id`.
>
> Base URL: `http://localhost:8000/api/v1`

## 0. Prerequisites

```bash
export BASE=http://localhost:8000/api/v1
export ORG_ID=019e549b-5ab4-71d1-9290-17de7937b9e3
```

Two cookie jars — one for an **admin** (back-office actions) and one for the **mobile client** (the subject of testing).

```bash
# admin
curl -s -X POST $BASE/account/login/ -H "Content-Type: application/json" \
  -d '{"email":"admin@platform.local","password":"ChangeMe123!"}' -c /tmp/admin.txt

# create + verify a fresh client via signup
EMAIL="mobile-$(date +%s)@example.com"
PASS="StrongPass123!"
PHONE="+770199$RANDOM"

curl -s -X POST $BASE/account/signup/ -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASS\",\"first_name\":\"Mobile\",\"last_name\":\"Tester\",\"phone\":\"$PHONE\"}"

CODE=$(docker exec backend-db_pg-1 psql -U postgres -d clean-example -tA -c \
  "SELECT v.code FROM email_verification_codes v JOIN users u ON u.id=v.user_id WHERE u.email='$EMAIL' ORDER BY v.created_at DESC LIMIT 1;")

curl -s -X POST $BASE/account/verify-email/ -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"code\":\"$CODE\"}"

# admin verifies the client (so submit_booking passes the verification gate)
CID=$(docker exec backend-db_pg-1 psql -U postgres -d clean-example -tA -c \
  "SELECT c.id FROM clients c JOIN users u ON u.id=c.user_id WHERE u.email='$EMAIL';")
curl -s -X POST $BASE/clients/$CID/verify -H "Content-Type: application/json" -b /tmp/admin.txt \
  -d '{"status":"verified"}'

# now login as the mobile client
curl -s -X POST $BASE/account/login/ -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASS\"}" -c /tmp/mobile.txt
```

Endpoint matrix:

| § | Method | Path | Notes |
|---|---|---|---|
| 1 | GET | `/mobile/clients/me` | self profile |
| 2 | PATCH | `/mobile/clients/me` | update self |
| 3 | GET | `/mobile/clients/me/verification` | verification status |
| 4 | GET | `/mobile/clients/me/fines` | self fines list |
| 5 | GET | `/mobile/clients/me/payments` | self payments list |
| 6 | GET | `/mobile/clients/me/outstanding` | self outstanding balance |
| 7 | PATCH | `/mobile/clients/me/notification-preferences` | toggle channels |
| 8a/8b | GET / POST | `/mobile/notifications/` + `/{id}/read` | list + mark read |
| 9 | POST/DEL | `/mobile/devices/register` + `/devices/{token}` | push token registration |
| 10 | GET | `/mobile/organizations` | orgs I belong to |
| 11 | POST | `/mobile/organizations/join` | join (requires invite token) |
| 12 | DELETE | `/mobile/organizations/{org_id}` | leave |
| 13 | GET | `/mobile/vehicles?organization_id=...` | available vehicles |
| 14 | GET | `/mobile/vehicles/{id}?organization_id=...` | one vehicle |
| 15 | GET | `/mobile/vehicles/{id}/availability?scheduled_start=...&scheduled_end=...` | availability check |
| 16 | GET | `/mobile/rentals` | my rentals |
| 17 | POST | `/mobile/rentals` | submit booking ★ regression-critical |
| 18 | GET | `/mobile/rentals/active` | currently-active rental |
| 19 | GET | `/mobile/rentals/{id}` | one rental |
| 20 | POST | `/mobile/rentals/{id}/cancel` | cancel ★ regression-critical |
| 21 | POST | `/mobile/rentals/{id}/extend-request` | request extension |
| 22 | POST | `/mobile/payments/record` | self-record a payment |

Star ★ = endpoints rewired in `USER_CLIENT_LINK_CLEANUP`; these MUST work.

---

## 1–3. Self profile

```bash
curl -s -o /dev/null -w "GET me: %{http_code}\n"             $BASE/mobile/clients/me -b /tmp/mobile.txt
curl -s -X PATCH $BASE/mobile/clients/me -H "Content-Type: application/json" -b /tmp/mobile.txt \
  -d '{"first_name":"MobileRenamed"}' -o /dev/null -w "PATCH me: %{http_code}\n"
curl -s -o /dev/null -w "GET verification: %{http_code}\n"   $BASE/mobile/clients/me/verification -b /tmp/mobile.txt
```

Expected: 200 / 204 / 200.

## 4–6. Self fines / payments / outstanding

```bash
curl -s -o /dev/null -w "fines:       %{http_code}\n"  $BASE/mobile/clients/me/fines -b /tmp/mobile.txt
curl -s -o /dev/null -w "payments:    %{http_code}\n"  $BASE/mobile/clients/me/payments -b /tmp/mobile.txt
curl -s -o /dev/null -w "outstanding: %{http_code}\n"  $BASE/mobile/clients/me/outstanding -b /tmp/mobile.txt
```

Expected: 200 / 200 / 200.

## 7. Notification preferences

```bash
curl -s -X PATCH $BASE/mobile/clients/me/notification-preferences \
  -H "Content-Type: application/json" -b /tmp/mobile.txt \
  -d '{"overdue_alert":false}' -o /dev/null -w "%{http_code}\n"
```

Expected: 204.

## 8. Notifications inbox

```bash
curl -s -o /dev/null -w "list: %{http_code}\n" $BASE/mobile/notifications/ -b /tmp/mobile.txt
# (no notification id yet — covered later via mark-read after we have one)
```

## 9. Push device registration

```bash
TOKEN="dummy-test-token-$(date +%s)"
curl -s -X POST $BASE/mobile/devices/register \
  -H "Content-Type: application/json" -b /tmp/mobile.txt \
  -d "{\"token\":\"$TOKEN\",\"platform\":\"ios\"}" -o /dev/null -w "register: %{http_code}\n"
curl -s -X DELETE $BASE/mobile/devices/$TOKEN -b /tmp/mobile.txt \
  -o /dev/null -w "unregister: %{http_code}\n"
```

Expected: 204 / 204 (or 201 / 204 depending on the handler).

## 10. My organizations

```bash
curl -s -o /dev/null -w "%{http_code}\n" $BASE/mobile/organizations -b /tmp/mobile.txt
```

Expected: 200 (returns at least the org you signed up into).

## 11 & 12. Join / leave organization — skip (requires an invite token; covered in invite spec).

## 13–15. Vehicles

```bash
# 13. List
curl -s -o /dev/null -w "vehicles list: %{http_code}\n" \
  "$BASE/mobile/vehicles?organization_id=$ORG_ID" -b /tmp/mobile.txt

# Pick the first vehicle id (we seeded one earlier)
VID=$(curl -s "$BASE/mobile/vehicles?organization_id=$ORG_ID" -b /tmp/mobile.txt \
  | python3 -c "import sys,json; d=json.load(sys.stdin); items=d.get('vehicles', d.get('items',[])); print(items[0]['id'] if items else '')")

# 14. Get one
curl -s -o /dev/null -w "vehicle one:   %{http_code}\n" \
  "$BASE/mobile/vehicles/$VID?organization_id=$ORG_ID" -b /tmp/mobile.txt

# 15. Availability for a future window
START=$(date -u -v+30d +"%Y-%m-%dT09:00:00Z")
END=$(date -u -v+33d +"%Y-%m-%dT09:00:00Z")
curl -s -o /dev/null -w "availability:  %{http_code}\n" \
  "$BASE/mobile/vehicles/$VID/availability?scheduled_start=$START&scheduled_end=$END" -b /tmp/mobile.txt
```

Expected: 200 / 200 / 200.

## 16–20. Rentals (★ booking flow)

```bash
# 17. Submit booking
RESP=$(curl -s -X POST $BASE/mobile/rentals \
  -H "Content-Type: application/json" -b /tmp/mobile.txt \
  -d "{\"organization_id\":\"$ORG_ID\",\"vehicle_id\":\"$VID\",\"booking_type\":\"daily\",
       \"scheduled_start\":\"$START\",\"scheduled_end\":\"$END\",
       \"base_rate\":\"15000\",\"rate_type\":\"per_day\",\"estimated_total\":\"45000\",
       \"deposit_type\":\"cash\",\"deposit_amount\":\"50000\"}")
RID=$(echo "$RESP" | python3 -c "import sys,json; print(json.load(sys.stdin).get('id',''))")
echo "submit-booking: id=$RID"

# 16. My rentals
curl -s -o /dev/null -w "list my rentals: %{http_code}\n" $BASE/mobile/rentals -b /tmp/mobile.txt

# 18. Active rental — none yet (rental is PENDING, not active)
curl -s -o /dev/null -w "my active:       %{http_code}\n" $BASE/mobile/rentals/active -b /tmp/mobile.txt

# 19. Get one
curl -s -o /dev/null -w "get one:         %{http_code}\n" $BASE/mobile/rentals/$RID -b /tmp/mobile.txt

# 21. Submit extension request
curl -s -X POST $BASE/mobile/rentals/$RID/extend-request \
  -H "Content-Type: application/json" -b /tmp/mobile.txt \
  -d "{\"new_scheduled_end\":\"$(date -u -v+35d +"%Y-%m-%dT09:00:00Z")\",\"reason\":\"need more time\"}" \
  -o /dev/null -w "extend-request:  %{http_code}\n"

# 20. Cancel my rental
curl -s -X POST $BASE/mobile/rentals/$RID/cancel \
  -H "Content-Type: application/json" -b /tmp/mobile.txt \
  -d '{"reason":"plans changed"}' -o /dev/null -w "cancel:          %{http_code}\n"
```

## 22. Self-record payment

```bash
curl -s -X POST $BASE/mobile/payments/record \
  -H "Content-Type: application/json" -b /tmp/mobile.txt \
  -d "{\"organization_id\":\"$ORG_ID\",\"amount\":\"5000\",\"reference\":\"manual-bank-xfer\"}" \
  -o /dev/null -w "record-payment:  %{http_code}\n"
```

## Acceptance criteria

- All authenticated endpoints return 2xx (or the documented domain-specific status).
- §17 submit_booking and §20 cancel — must not 500 (these are the regression-critical ones).
- DB confirms: the booking created in §17 has `client_id` = the test client's id, and that the cancel in §20 flipped status to `cancelled`.
