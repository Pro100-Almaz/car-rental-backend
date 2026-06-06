# Clients Module — API Testing Guide

> Curl-driven integration test plan for all client endpoints. Run against a live local server.
> Base URL: `http://localhost:8000/api/v1`.

## 0. Prerequisites

```bash
# login as super-admin (5-min session lifetime in dev)
curl -s -X POST http://localhost:8000/api/v1/account/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@platform.local","password":"ChangeMe123!"}' \
  -c /tmp/cookies.txt

# vars used throughout
export ORG_ID="019e549b-5ab4-71d1-9290-17de7937b9e3"   # AutoFleet Test (set via APP_DEFAULT_ORGANIZATION_ID)
export BASE=http://localhost:8000/api/v1
```

Endpoint matrix:

| § | Method | Path | Notes |
|---|---|---|---|
| 1 | POST | `/clients/` | manager-creates a client (admin/back-office side) |
| 2 | GET | `/clients/?organization_id=&...` | list with filters |
| 3 | GET | `/clients/{client_id}` | one |
| 4 | PATCH | `/clients/{client_id}` | partial update (whitelist of fields) |
| 5 | POST | `/clients/{client_id}/verify` | sets `verification_status` |
| 6a | POST | `/clients/{client_id}/blacklist` | blacklist |
| 6b | DELETE | `/clients/{client_id}/blacklist` | unblacklist |
| 7 | GET | `/clients/{client_id}/rentals` | client subresource |
| 8 | GET | `/clients/{client_id}/payments` | client subresource |
| 9 | POST | `/clients/{client_id}/send-reminder` | sends a debt-reminder notification (silent skip when client has no `user_id`) |

---

## 1. Create client

### 1.1 Minimal fields → 201
```bash
curl -s -X POST $BASE/clients/ -H "Content-Type: application/json" -b /tmp/cookies.txt \
  -d "{\"organization_id\":\"$ORG_ID\",\"first_name\":\"Test\",\"last_name\":\"One\",\"phone\":\"+77011000$$\",\"iin\":\"900101300101\",\"id_document_type\":\"id_card\",\"id_document_number\":\"111111111\"}"
# expect: 201, response { "id": <uuid>, "created_at": <ts> }
```

Save the returned id as `CLIENT_ID`.

### 1.2 Missing required field → 422
```bash
curl -s -X POST $BASE/clients/ -H "Content-Type: application/json" -b /tmp/cookies.txt \
  -d "{\"organization_id\":\"$ORG_ID\"}"
# expect: 422
```

### 1.3 Unauthenticated → 401
```bash
curl -s -X POST $BASE/clients/ -H "Content-Type: application/json" \
  -d "{\"organization_id\":\"$ORG_ID\",\"first_name\":\"X\",\"last_name\":\"Y\",\"phone\":\"+77011111111\",\"iin\":\"111\",\"id_document_type\":\"id_card\",\"id_document_number\":\"1\"}"
# expect: 401
```

### 1.4 Duplicate phone in same org → 503 (`Database constraint violation`)
Re-send 1.1 unchanged → expect 503. (After the `CLIENT_PHONE_PARTIAL_UNIQUE` migration, only non-empty phones collide.)

---

## 2. List clients

```bash
curl -s "$BASE/clients/?organization_id=$ORG_ID" -b /tmp/cookies.txt
# expect: 200, JSON list including CLIENT_ID
```

### 2.x filter variants
- `?organization_id=$ORG_ID&verification_status=pending` → 200, only pending clients.
- `?organization_id=$ORG_ID&is_blacklisted=true` → 200, only blacklisted.
- `?organization_id=$ORG_ID&search=Test` → 200, hits the new client by first_name.

---

## 3. Get one

### 3.1 Existing → 200
```bash
curl -s $BASE/clients/$CLIENT_ID -b /tmp/cookies.txt
```

### 3.2 Unknown UUID → 404 (after HTTPException burndown — this is one of the routes we fixed)
```bash
curl -s -o /dev/null -w "%{http_code}\n" $BASE/clients/00000000-0000-0000-0000-000000000000 -b /tmp/cookies.txt
# expect: 404
```

---

## 4. PATCH (partial update)

### 4.1 Update first_name → 204
```bash
curl -s -X PATCH $BASE/clients/$CLIENT_ID -H "Content-Type: application/json" -b /tmp/cookies.txt \
  -d '{"first_name":"Renamed"}'
# expect: 204
# then GET $CLIENT_ID and verify first_name = "Renamed"
```

### 4.2 Update unknown id → 404
```bash
curl -s -o /dev/null -w "%{http_code}\n" -X PATCH $BASE/clients/00000000-0000-0000-0000-000000000000 \
  -H "Content-Type: application/json" -b /tmp/cookies.txt -d '{"first_name":"x"}'
# expect: 404
```

---

## 5. Verify

### 5.1 Set verified → 204
```bash
curl -s -X POST $BASE/clients/$CLIENT_ID/verify -H "Content-Type: application/json" -b /tmp/cookies.txt \
  -d '{"status":"verified"}'
# verify with GET → verification_status = "verified"
```

### 5.2 Invalid status enum → 422
```bash
curl -s -o /dev/null -w "%{http_code}\n" -X POST $BASE/clients/$CLIENT_ID/verify \
  -H "Content-Type: application/json" -b /tmp/cookies.txt -d '{"status":"banana"}'
# expect: 422
```

### 5.3 Verify unknown id → 404
Same shape — unknown UUID → 404.

---

## 6. Blacklist / Unblacklist

### 6.1 Blacklist → 204
```bash
curl -s -X POST $BASE/clients/$CLIENT_ID/blacklist -H "Content-Type: application/json" -b /tmp/cookies.txt \
  -d '{"reason":"fraud attempt"}'
# GET → is_blacklisted=true, blacklist_reason="fraud attempt"
```

### 6.2 Unblacklist (DELETE) → 204
```bash
curl -s -X DELETE $BASE/clients/$CLIENT_ID/blacklist -b /tmp/cookies.txt
# GET → is_blacklisted=false
```

### 6.3 Blacklist with missing `reason` → 422

---

## 7. Client → Rentals subresource

```bash
curl -s $BASE/clients/$CLIENT_ID/rentals?organization_id=$ORG_ID -b /tmp/cookies.txt
# expect: 200, list (possibly empty)
```

---

## 8. Client → Payments subresource

```bash
curl -s $BASE/clients/$CLIENT_ID/payments?organization_id=$ORG_ID -b /tmp/cookies.txt
# expect: 200, list (possibly empty)
```

---

## 9. Send debt reminder

### 9.1 Client without user_id → 404 (`ClientNotFoundError("Client has no linked user account.")`)
Manager-created clients have `user_id=NULL`, so the handler hard-fails (this is the documented behaviour — distinct from system reminders which silently skip).

```bash
curl -s -X POST $BASE/clients/$CLIENT_ID/send-reminder -H "Content-Type: application/json" -b /tmp/cookies.txt \
  -d '{"message":"You have an outstanding balance."}'
# expect: 404
```

### 9.2 Client WITH user_id (one created by `/signup/`) → 200
Use a client that came in via signup (has `user_id` set):
```bash
curl -s -o /dev/null -w "%{http_code}\n" -X POST $BASE/clients/$SIGNUP_CLIENT_ID/send-reminder \
  -H "Content-Type: application/json" -b /tmp/cookies.txt -d '{}'
# expect: 200, notification row visible in DB:
#   SELECT * FROM notifications WHERE type='debt_reminder' ORDER BY created_at DESC LIMIT 1;
```

---

## Tear-down

No tear-down — leave test clients in place. Rerunning the spec creates fresh clients (the unique phone is appended with `$$`).
