#!/usr/bin/env bash
# Rental lifecycle E2E — see spec/RENTAL_LIFECYCLE_E2E.md.
#
# Walks the full chain: discover -> book -> approve -> checkout -> extension ->
# checkin -> complete, plus 4 branches (client cancel, manager reject, date
# overlap, extension reject+retry).
#
# Usage:
#   ./scripts/qa/rental_lifecycle_e2e.sh         # all scenarios
#   ./scripts/qa/rental_lifecycle_e2e.sh A       # one scenario
#
# Requirements: bash 3.2+, curl, jq, docker (backend stack already running).
#
# Container names:
#   backend-app-1    FastAPI app (port 8000)
#   backend-db_pg-1  PostgreSQL  (db: clean-example, user: postgres)
#   backend-redis-1  Redis
#
# --- Bash 3.2 compatibility note ---
# macOS ships bash 3.2 which has a parser bug: when a string argument ending
# with "}" is passed to a function call that is the last statement before a
# function's closing "}", bash appends the closing "}" to the argument.
# Workaround: request body is communicated via the global POST_BODY variable
# rather than as a positional argument to api_post(). This avoids the
# argument-passing path entirely.
#
# --- stdout / stderr discipline ---
# ALL diagnostic output (step lines, errors, summary) goes to stderr (>&2).
# login_admin() and signup_and_login_client() print ONLY the bare token to
# stdout so callers can safely do:  token=$(login_admin)
#
# --- Rate-limit strategy ---
# login:  5/minute;30/hour per IP  — we restart the app before each scenario
#         which resets in-memory state; Redis is also FLUSHALL-ed so the
#         Redis-backed counters are cleared too.
# signup: 3/hour;10/day per IP    — same: flush+restart between scenarios.
set -euo pipefail

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
API="${API:-http://localhost:8000/api/v1}"
ADMIN_EMAIL="${ADMIN_EMAIL:-admin@platform.local}"
ADMIN_PASS="${ADMIN_PASS:-ChangeMe123!}"
DEFAULT_ORG_ID="${DEFAULT_ORG_ID:-019e549b-5ab4-71d1-9290-17de7937b9e3}"
DB_CONTAINER="${DB_CONTAINER:-backend-db_pg-1}"
APP_CONTAINER="${APP_CONTAINER:-backend-app-1}"
REDIS_CONTAINER="${REDIS_CONTAINER:-backend-redis-1}"
DB_NAME="${DB_NAME:-clean-example}"
DB_USER="${DB_USER:-postgres}"

EXPECT_FAIL=0   # set to 1 before calls expected to return non-2xx

# ---------------------------------------------------------------------------
# Colours (all output -> stderr)
# ---------------------------------------------------------------------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

say() { printf "\n${CYAN}${BOLD}%s${RESET}\n" "$*" >&2; }
ok()  { printf "${GREEN}OK${RESET}\n" >&2; }

# ---------------------------------------------------------------------------
# psql helper  (stdout = trimmed result only)
# ---------------------------------------------------------------------------
psql_exec() {
    docker exec "$DB_CONTAINER" \
        psql -U "$DB_USER" -d "$DB_NAME" -tAc "$1" 2>/dev/null \
        | tr -d '[:space:]'
}

# ---------------------------------------------------------------------------
# Rate-limit reset: flush Redis then restart app, wait for /livez/ health.
# This clears both Redis-backed counters AND in-memory fallback counters.
# ---------------------------------------------------------------------------
reset_rate_limits() {
    printf "  [reset] flushing Redis ..." >&2
    docker exec "$REDIS_CONTAINER" redis-cli FLUSHALL >/dev/null 2>&1 || true
    printf " done. restarting app ..." >&2
    docker restart "$APP_CONTAINER" >/dev/null 2>&1

    local attempts=0
    until curl -sf "http://localhost:8000/livez/" >/dev/null 2>&1; do
        sleep 1
        attempts=$(( attempts + 1 ))
        if [ "$attempts" -ge 45 ]; then
            printf "\n${RED}FAIL: app did not come up after restart${RESET}\n" >&2
            exit 1
        fi
    done
    printf " ${GREEN}ready${RESET}\n" >&2
}

# ---------------------------------------------------------------------------
# HTTP helpers
#
# POST_BODY (global) holds the request body; set it before calling api_post.
# This avoids the bash 3.2 argument-passing bug with strings ending in '}'.
#
# LAST_BODY and LAST_HTTP_STATUS are populated after each call.
# All diagnostic output -> stderr.
# ---------------------------------------------------------------------------
POST_BODY="{}"
LAST_HTTP_STATUS=0
LAST_BODY=""

api_post() {
    # api_post <path> [bearer]
    # Reads request body from global POST_BODY.
    local path="$1"
    local bearer="${2:-}"
    local body="$POST_BODY"
    local tmpfile
    tmpfile=$(mktemp)

    local http_code
    if [ -n "$bearer" ]; then
        http_code=$(printf '%s' "$body" | curl -s -o "$tmpfile" -w "%{http_code}" \
            -X POST \
            -H "Content-Type: application/json" \
            -H "Authorization: Bearer ${bearer}" \
            --data-binary @- \
            "${API}${path}")
    else
        http_code=$(printf '%s' "$body" | curl -s -o "$tmpfile" -w "%{http_code}" \
            -X POST \
            -H "Content-Type: application/json" \
            --data-binary @- \
            "${API}${path}")
    fi

    LAST_BODY=$(cat "$tmpfile")
    rm -f "$tmpfile"
    LAST_HTTP_STATUS="$http_code"

    if [ "$EXPECT_FAIL" -eq 1 ]; then
        return 0
    fi

    if [ "$http_code" -lt 200 ] || [ "$http_code" -gt 299 ]; then
        printf "\n${RED}FAIL POST %s${RESET}\n" "${API}${path}" >&2
        printf "  HTTP %s\n" "$http_code" >&2
        printf "  Body: %s\n" "$LAST_BODY" >&2
        exit 1
    fi
}

api_get() {
    # api_get <path_with_querystring> <bearer>
    local path="$1"
    local bearer="${2:-}"
    local tmpfile
    tmpfile=$(mktemp)

    local http_code
    if [ -n "$bearer" ]; then
        http_code=$(curl -s -o "$tmpfile" -w "%{http_code}" \
            -H "Authorization: Bearer ${bearer}" \
            "${API}${path}")
    else
        http_code=$(curl -s -o "$tmpfile" -w "%{http_code}" \
            "${API}${path}")
    fi

    LAST_BODY=$(cat "$tmpfile")
    rm -f "$tmpfile"
    LAST_HTTP_STATUS="$http_code"

    if [ "$EXPECT_FAIL" -eq 1 ]; then
        return 0
    fi

    if [ "$http_code" -lt 200 ] || [ "$http_code" -gt 299 ]; then
        printf "\n${RED}FAIL GET %s${RESET}\n" "${API}${path}" >&2
        printf "  HTTP %s\n" "$http_code" >&2
        printf "  Body: %s\n" "$LAST_BODY" >&2
        exit 1
    fi
}

# ---------------------------------------------------------------------------
# Assertion helpers (all output -> stderr)
# ---------------------------------------------------------------------------
assert_eq() {
    local label="$1" actual="$2" expected="$3"
    if [ "$actual" != "$expected" ]; then
        printf "\n${RED}ASSERT FAIL: %s${RESET}\n" "$label" >&2
        printf "  expected: %s\n" "$expected" >&2
        printf "  actual:   %s\n" "$actual" >&2
        exit 1
    fi
}

assert_in() {
    local label="$1" haystack="$2" needle="$3"
    case "$haystack" in
        *"$needle"*) return 0 ;;
        *)
            printf "\n${RED}ASSERT FAIL: %s${RESET}\n" "$label" >&2
            printf "  needle:   %s\n" "$needle" >&2
            printf "  haystack: %.300s...\n" "$haystack" >&2
            exit 1
            ;;
    esac
}

assert_not_in() {
    local label="$1" haystack="$2" needle="$3"
    case "$haystack" in
        *"$needle"*)
            printf "\n${RED}ASSERT FAIL (should NOT contain): %s${RESET}\n" "$label" >&2
            printf "  needle: %s\n" "$needle" >&2
            exit 1
            ;;
        *) return 0 ;;
    esac
}

assert_http() {
    local label="$1" expected_code="$2"
    if [ "$LAST_HTTP_STATUS" != "$expected_code" ]; then
        printf "\n${RED}ASSERT FAIL: %s${RESET}\n" "$label" >&2
        printf "  expected HTTP: %s\n" "$expected_code" >&2
        printf "  actual HTTP:   %s\n" "$LAST_HTTP_STATUS" >&2
        printf "  body:          %s\n" "$LAST_BODY" >&2
        exit 1
    fi
}

# ---------------------------------------------------------------------------
# Auth helpers
# Print ONLY the access token to stdout; all other output -> stderr.
# Use POST_BODY global to pass request body (avoids bash 3.2 arg-passing bug).
#
# IMPORTANT: signup_and_login_client() is called inside $() subshells so it
# cannot set globals in the parent process. Instead it writes the client email
# to a temp file (_CLIENT_EMAIL_FILE) so the parent can read it back.
# ---------------------------------------------------------------------------
_CLIENT_EMAIL_FILE=$(mktemp)
trap 'rm -f "$_CLIENT_EMAIL_FILE"' EXIT

login_admin() {
    POST_BODY="{\"email\":\"${ADMIN_EMAIL}\",\"password\":\"${ADMIN_PASS}\"}"
    api_post "/account/login/"
    printf '%s' "$LAST_BODY" | jq -r '.access_token'
}

signup_and_login_client() {
    local ts rand email phone code
    ts=$(date +%s)
    rand=$(od -An -N2 -tu2 /dev/urandom 2>/dev/null | tr -d ' ' || printf "%d" "$$")
    email="e2e-${ts}-${rand}@example.com"
    phone="+7700$(printf '%s' "$ts" | tail -c 7)"

    # Write email to file so parent process can read it (subshell cannot set globals)
    printf '%s' "$email" > "$_CLIENT_EMAIL_FILE"

    # 1. Signup
    POST_BODY="{\"email\":\"${email}\",\"password\":\"Pass1234!\",\"first_name\":\"E2E\",\"last_name\":\"Test\",\"phone\":\"${phone}\"}"
    api_post "/account/signup/"

    # 2. Pull verification code from DB
    code=$(psql_exec "SELECT code FROM email_verification_codes WHERE user_id = (SELECT id FROM users WHERE email = '${email}') ORDER BY created_at DESC LIMIT 1;")
    if [ -z "$code" ]; then
        printf "\n${RED}FAIL: no verification code for %s${RESET}\n" "$email" >&2
        exit 1
    fi

    # 3. Verify email
    POST_BODY="{\"email\":\"${email}\",\"code\":\"${code}\"}"
    api_post "/account/verify-email/"

    # 4. Login — print only the token to stdout
    POST_BODY="{\"email\":\"${email}\",\"password\":\"Pass1234!\"}"
    api_post "/account/login/"
    printf '%s' "$LAST_BODY" | jq -r '.access_token'
}

# Read the last client email written by signup_and_login_client()
last_client_email() {
    cat "$_CLIENT_EMAIL_FILE"
}

# ---------------------------------------------------------------------------
# verify_client_as_admin <admin_bearer> <client_email>
# Looks up the client profile by email and sets verification_status=verified.
# ---------------------------------------------------------------------------
verify_client_as_admin() {
    local admin_bearer="$1"
    local client_email="$2"
    local client_id
    client_id=$(psql_exec "SELECT id FROM clients WHERE user_id = (SELECT id FROM users WHERE email = '${client_email}') LIMIT 1;")
    if [ -z "$client_id" ]; then
        printf "\n${RED}FAIL: client profile not found for %s${RESET}\n" "$client_email" >&2
        exit 1
    fi
    POST_BODY='{"status":"verified"}'
    api_post "/clients/${client_id}/verify" "$admin_bearer"
}

# ---------------------------------------------------------------------------
# Seed vehicles (idempotent)
# ---------------------------------------------------------------------------
V1="00000000-0000-0000-0000-000000000e01"
V2="00000000-0000-0000-0000-000000000e02"
V3="00000000-0000-0000-0000-000000000e03"

seed_vehicles_if_missing() {
    docker exec "$DB_CONTAINER" \
        psql -U "$DB_USER" -d "$DB_NAME" -tAc "
INSERT INTO vehicles (
    id, organization_id, make, model, year, license_plate,
    color, category, status, fuel_type, transmission,
    current_mileage, created_at, updated_at
) VALUES
    ('${V1}','${DEFAULT_ORG_ID}','Toyota','Camry',2022,'E2E-001','White','sedan','available','petrol','automatic',0,now(),now()),
    ('${V2}','${DEFAULT_ORG_ID}','Toyota','Camry',2022,'E2E-002','Black','sedan','available','petrol','automatic',0,now(),now()),
    ('${V3}','${DEFAULT_ORG_ID}','Toyota','Camry',2022,'E2E-003','Silver','sedan','available','petrol','automatic',0,now(),now())
ON CONFLICT (id) DO NOTHING;
" >/dev/null 2>&1
    # Cancel any stale non-terminal rentals so overlap checks start clean.
    docker exec "$DB_CONTAINER" \
        psql -U "$DB_USER" -d "$DB_NAME" -tAc "
UPDATE rentals SET status='cancelled'
WHERE vehicle_id IN ('${V1}','${V2}','${V3}')
  AND status NOT IN ('cancelled','completed');
" >/dev/null 2>&1
    # Ensure vehicles are in 'available' status for this run.
    docker exec "$DB_CONTAINER" \
        psql -U "$DB_USER" -d "$DB_NAME" -tAc "
UPDATE vehicles SET status='available' WHERE id IN ('${V1}','${V2}','${V3}');
" >/dev/null 2>&1
}

# ---------------------------------------------------------------------------
# Step / scenario tracking  (bash 3.2 — no declare -A)
# ---------------------------------------------------------------------------
CURRENT_STEP=0
RESULT_A="SKIP"; STEPS_A=0; TIME_A="N/A"
RESULT_B="SKIP"; STEPS_B=0; TIME_B="N/A"
RESULT_C="SKIP"; STEPS_C=0; TIME_C="N/A"
RESULT_D="SKIP"; STEPS_D=0; TIME_D="N/A"
RESULT_E="SKIP"; STEPS_E=0; TIME_E="N/A"

_set_result() {
    eval "RESULT_${1}=\"${2}\""
    eval "STEPS_${1}=\"${3}\""
    eval "TIME_${1}=\"${4}\""
}

step() {
    CURRENT_STEP=$(( CURRENT_STEP + 1 ))
    printf "  [%2s] %-66s" "$CURRENT_STEP" "$1" >&2
}

run_scenario() {
    local letter="$1" name="$2" fn="$3"
    printf "\n${BOLD}${CYAN}=== Scenario %s --- %s ===${RESET}\n" "$letter" "$name" >&2

    # Reset rate limits before each scenario so signup (3/hour) and
    # login (5/minute) counters are always fresh.
    reset_rate_limits
    seed_vehicles_if_missing

    CURRENT_STEP=0
    local t_start t_end
    t_start=$(date +%s)
    if "$fn"; then
        t_end=$(date +%s)
        _set_result "$letter" "PASS" "$CURRENT_STEP" "$(( t_end - t_start ))s"
    else
        _set_result "$letter" "FAIL" "$CURRENT_STEP" "N/A"
    fi
}

# ---------------------------------------------------------------------------
# SCENARIO A — Happy path
# ---------------------------------------------------------------------------
scenario_a() {
    local client_bearer admin_bearer rental_id ext_id status_val db_status

    step "client signup + verify + login"
    client_bearer=$(signup_and_login_client)
    ok

    step "admin login + verify client"
    admin_bearer=$(login_admin)
    verify_client_as_admin "$admin_bearer" "$(last_client_email)"
    ok

    step "client lists vehicles (>= 1)"
    api_get "/mobile/vehicles?organization_id=${DEFAULT_ORG_ID}" "$client_bearer"
    local vc
    vc=$(printf '%s' "$LAST_BODY" | jq '.vehicles | length' 2>/dev/null || printf '%s' "$LAST_BODY" | jq 'length')
    if [ "${vc:-0}" -lt 1 ]; then
        printf "\n${RED}FAIL: no vehicles. Body: %s${RESET}\n" "$LAST_BODY" >&2; return 1
    fi
    ok

    step "client books E2E-001 -> 201 pending"
    local tomorrow day_after
    tomorrow=$(date -v+1d '+%Y-%m-%dT10:00:00Z' 2>/dev/null || date -d '+1 day' '+%Y-%m-%dT10:00:00Z')
    day_after=$(date -v+2d '+%Y-%m-%dT10:00:00Z' 2>/dev/null || date -d '+2 days' '+%Y-%m-%dT10:00:00Z')
    POST_BODY="{\"organization_id\":\"${DEFAULT_ORG_ID}\",\"vehicle_id\":\"${V1}\",\"booking_type\":\"daily\",\"scheduled_start\":\"${tomorrow}\",\"scheduled_end\":\"${day_after}\",\"base_rate\":\"100.00\",\"rate_type\":\"per_day\",\"estimated_total\":\"200.00\",\"deposit_type\":\"cash\",\"deposit_amount\":\"500.00\"}"
    api_post "/mobile/rentals" "$client_bearer"
    assert_http "submit booking" "201"
    rental_id=$(printf '%s' "$LAST_BODY" | jq -r '.id')
    db_status=$(psql_exec "SELECT status FROM rentals WHERE id='${rental_id}';")
    assert_eq "initial status=pending" "$db_status" "pending"
    ok

    step "admin sees rental in booking-requests"
    api_get "/rentals/booking-requests?organization_id=${DEFAULT_ORG_ID}" "$admin_bearer"
    assert_in "rental in queue" "$LAST_BODY" "$rental_id"
    ok

    step "admin approves -> DB confirmed + manager_id set"
    POST_BODY="{}"
    api_post "/rentals/${rental_id}/approve" "$admin_bearer"
    assert_http "approve" "200"
    db_status=$(psql_exec "SELECT status FROM rentals WHERE id='${rental_id}';")
    assert_eq "DB confirmed" "$db_status" "confirmed"
    local mgr
    mgr=$(psql_exec "SELECT manager_id FROM rentals WHERE id='${rental_id}';")
    if [ -z "$mgr" ]; then
        printf "\n${RED}FAIL: manager_id not set${RESET}\n" >&2; return 1
    fi
    ok

    step "client sees status=confirmed"
    api_get "/mobile/rentals/${rental_id}" "$client_bearer"
    status_val=$(printf '%s' "$LAST_BODY" | jq -r '.status')
    assert_eq "client confirmed" "$status_val" "confirmed"
    ok

    step "admin checkin (confirmed->active) -> DB active"
    POST_BODY='{"checkin_data":{"mileage":0,"fuel_level":100}}'
    api_post "/rentals/${rental_id}/checkin" "$admin_bearer"
    assert_http "checkin" "204"
    db_status=$(psql_exec "SELECT status FROM rentals WHERE id='${rental_id}';")
    assert_eq "DB active" "$db_status" "active"
    ok

    step "client GET /mobile/rentals/active -> this rental"
    api_get "/mobile/rentals/active" "$client_bearer"
    assert_in "active rental" "$LAST_BODY" "$rental_id"
    ok

    step "client submits extension +1 day -> 201 pending"
    local new_end ext_status
    new_end=$(date -v+3d '+%Y-%m-%dT10:00:00Z' 2>/dev/null || date -d '+3 days' '+%Y-%m-%dT10:00:00Z')
    POST_BODY="{\"new_end_date\":\"${new_end}\",\"additional_cost\":\"100.00\"}"
    api_post "/mobile/rentals/${rental_id}/extend-request" "$client_bearer"
    assert_http "ext request" "201"
    ext_id=$(printf '%s' "$LAST_BODY" | jq -r '.id')
    ext_status=$(psql_exec "SELECT status FROM extension_requests WHERE id='${ext_id}';")
    assert_eq "ext pending" "$ext_status" "pending"
    ok

    step "admin approves extension -> DB ext=approved"
    POST_BODY="{}"
    api_post "/rentals/${ext_id}/extension/approve" "$admin_bearer"
    assert_http "approve ext" "200"
    local db_ext
    db_ext=$(psql_exec "SELECT status FROM extension_requests WHERE id='${ext_id}';")
    assert_eq "DB ext approved" "$db_ext" "approved"
    ok

    step "admin checkout (active->returning) -> DB returning"
    POST_BODY='{"checkout_data":{"mileage":150,"fuel_level":80}}'
    api_post "/rentals/${rental_id}/checkout" "$admin_bearer"
    assert_http "checkout" "204"
    db_status=$(psql_exec "SELECT status FROM rentals WHERE id='${rental_id}';")
    assert_eq "DB returning" "$db_status" "returning"
    ok

    step "admin complete -> DB completed"
    POST_BODY='{"actual_total":"200.00"}'
    api_post "/rentals/${rental_id}/complete" "$admin_bearer"
    assert_http "complete" "204"
    db_status=$(psql_exec "SELECT status FROM rentals WHERE id='${rental_id}';")
    assert_eq "DB completed" "$db_status" "completed"
    ok

    step "client sees status=completed"
    api_get "/mobile/rentals/${rental_id}" "$client_bearer"
    status_val=$(printf '%s' "$LAST_BODY" | jq -r '.status')
    assert_eq "client completed" "$status_val" "completed"
    ok

    step "audit log: approved + checked_out + checked_in + completed"
    local logs
    logs=$(docker logs "$APP_CONTAINER" --since 10m 2>&1 || true)
    assert_in "log approved"     "$logs" "rental.booking.approved"
    assert_in "log checked_out"  "$logs" "rental.checked_out"
    assert_in "log checked_in"   "$logs" "rental.checked_in"
    assert_in "log completed"    "$logs" "rental.completed"
    ok

    return 0
}

# ---------------------------------------------------------------------------
# SCENARIO B — Client cancels before approval
# ---------------------------------------------------------------------------
scenario_b() {
    local client_bearer admin_bearer rental_id

    step "client signup + admin login + verify client"
    client_bearer=$(signup_and_login_client)
    admin_bearer=$(login_admin)
    verify_client_as_admin "$admin_bearer" "$(last_client_email)"
    ok

    step "client books E2E-001 next-week -> pending"
    local start end
    start=$(date -v+7d  '+%Y-%m-%dT10:00:00Z' 2>/dev/null || date -d '+7 days'  '+%Y-%m-%dT10:00:00Z')
    end=$(date   -v+9d  '+%Y-%m-%dT10:00:00Z' 2>/dev/null || date -d '+9 days'  '+%Y-%m-%dT10:00:00Z')
    POST_BODY="{\"organization_id\":\"${DEFAULT_ORG_ID}\",\"vehicle_id\":\"${V1}\",\"booking_type\":\"daily\",\"scheduled_start\":\"${start}\",\"scheduled_end\":\"${end}\",\"base_rate\":\"100.00\",\"rate_type\":\"per_day\",\"estimated_total\":\"200.00\",\"deposit_type\":\"cash\",\"deposit_amount\":\"500.00\"}"
    api_post "/mobile/rentals" "$client_bearer"
    assert_http "booking" "201"
    rental_id=$(printf '%s' "$LAST_BODY" | jq -r '.id')
    ok

    step "client cancels -> 204"
    POST_BODY='{"reason":"changed my plans"}'
    api_post "/mobile/rentals/${rental_id}/cancel" "$client_bearer"
    assert_http "cancel" "204"
    ok

    step "DB status=cancelled"
    local db_status
    db_status=$(psql_exec "SELECT status FROM rentals WHERE id='${rental_id}';")
    assert_eq "DB cancelled" "$db_status" "cancelled"
    ok

    step "booking-requests does NOT contain cancelled rental"
    api_get "/rentals/booking-requests?organization_id=${DEFAULT_ORG_ID}" "$admin_bearer"
    assert_not_in "not in queue" "$LAST_BODY" "$rental_id"
    ok

    step "admin approve after cancel -> 409"
    EXPECT_FAIL=1
    POST_BODY="{}"
    api_post "/rentals/${rental_id}/approve" "$admin_bearer"
    EXPECT_FAIL=0
    assert_http "approve 409" "409"
    ok

    return 0
}

# ---------------------------------------------------------------------------
# SCENARIO C — Manager rejects
# ---------------------------------------------------------------------------
scenario_c() {
    local client_bearer admin_bearer rental_id

    step "client signup + admin login + verify client"
    client_bearer=$(signup_and_login_client)
    admin_bearer=$(login_admin)
    verify_client_as_admin "$admin_bearer" "$(last_client_email)"
    ok

    step "client books E2E-001 -> pending"
    local start end
    start=$(date -v+14d '+%Y-%m-%dT10:00:00Z' 2>/dev/null || date -d '+14 days' '+%Y-%m-%dT10:00:00Z')
    end=$(date   -v+16d '+%Y-%m-%dT10:00:00Z' 2>/dev/null || date -d '+16 days' '+%Y-%m-%dT10:00:00Z')
    POST_BODY="{\"organization_id\":\"${DEFAULT_ORG_ID}\",\"vehicle_id\":\"${V1}\",\"booking_type\":\"daily\",\"scheduled_start\":\"${start}\",\"scheduled_end\":\"${end}\",\"base_rate\":\"100.00\",\"rate_type\":\"per_day\",\"estimated_total\":\"200.00\",\"deposit_type\":\"cash\",\"deposit_amount\":\"500.00\"}"
    api_post "/mobile/rentals" "$client_bearer"
    assert_http "booking" "201"
    rental_id=$(printf '%s' "$LAST_BODY" | jq -r '.id')
    ok

    step "admin rejects -> 200"
    POST_BODY='{"rejection_reason":"vehicle in service"}'
    api_post "/rentals/${rental_id}/reject" "$admin_bearer"
    assert_http "reject" "200"
    ok

    step "DB: cancelled + rejection_reason + manager_id"
    local db_status db_reason db_mgr
    db_status=$(psql_exec "SELECT status FROM rentals WHERE id='${rental_id}';")
    assert_eq "DB cancelled" "$db_status" "cancelled"
    db_reason=$(psql_exec "SELECT rejection_reason FROM rentals WHERE id='${rental_id}';")
    assert_in "rejection_reason set" "$db_reason" "vehicle"
    db_mgr=$(psql_exec "SELECT manager_id FROM rentals WHERE id='${rental_id}';")
    if [ -z "$db_mgr" ]; then
        printf "\n${RED}FAIL: manager_id not set after reject${RESET}\n" >&2; return 1
    fi
    ok

    step "client sees cancelled + rejection_reason"
    api_get "/mobile/rentals/${rental_id}" "$client_bearer"
    local status_val
    status_val=$(printf '%s' "$LAST_BODY" | jq -r '.status')
    assert_eq "client cancelled" "$status_val" "cancelled"
    assert_in "client sees reason" "$LAST_BODY" "vehicle"
    ok

    step "audit log: rental.booking.rejected"
    local logs
    logs=$(docker logs "$APP_CONTAINER" --since 10m 2>&1 || true)
    assert_in "log rejected" "$logs" "rental.booking.rejected"
    ok

    return 0
}

# ---------------------------------------------------------------------------
# SCENARIO D — Date overlap caught at approval
# ---------------------------------------------------------------------------
scenario_d() {
    local client_a_bearer client_b_bearer admin_bearer rental_a rental_b

    step "client_A signup + login"
    client_a_bearer=$(signup_and_login_client)
    local client_a_email
    client_a_email=$(last_client_email)
    ok

    step "admin login + verify client_A"
    admin_bearer=$(login_admin)
    verify_client_as_admin "$admin_bearer" "$client_a_email"
    ok

    # client_B needs its own signup — both fresh after reset_rate_limits.
    step "client_B signup + login + verify"
    client_b_bearer=$(signup_and_login_client)
    verify_client_as_admin "$admin_bearer" "$(last_client_email)"
    ok

    local start_a="2026-07-01T10:00:00Z"
    local end_a="2026-07-03T10:00:00Z"
    local start_b="2026-07-02T10:00:00Z"
    local end_b="2026-07-04T10:00:00Z"

    step "client_A books E2E-002 Jul-01..Jul-03 -> pending"
    POST_BODY="{\"organization_id\":\"${DEFAULT_ORG_ID}\",\"vehicle_id\":\"${V2}\",\"booking_type\":\"daily\",\"scheduled_start\":\"${start_a}\",\"scheduled_end\":\"${end_a}\",\"base_rate\":\"100.00\",\"rate_type\":\"per_day\",\"estimated_total\":\"200.00\",\"deposit_type\":\"cash\",\"deposit_amount\":\"500.00\"}"
    api_post "/mobile/rentals" "$client_a_bearer"
    assert_http "booking A" "201"
    rental_a=$(printf '%s' "$LAST_BODY" | jq -r '.id')
    ok

    step "admin approves rental_A -> confirmed"
    POST_BODY="{}"
    api_post "/rentals/${rental_a}/approve" "$admin_bearer"
    assert_http "approve A" "200"
    local db_a
    db_a=$(psql_exec "SELECT status FROM rentals WHERE id='${rental_a}';")
    assert_eq "A confirmed" "$db_a" "confirmed"
    ok

    step "client_B books same vehicle Jul-02..Jul-04 -> 409 overlap at booking"
    EXPECT_FAIL=1
    POST_BODY="{\"organization_id\":\"${DEFAULT_ORG_ID}\",\"vehicle_id\":\"${V2}\",\"booking_type\":\"daily\",\"scheduled_start\":\"${start_b}\",\"scheduled_end\":\"${end_b}\",\"base_rate\":\"100.00\",\"rate_type\":\"per_day\",\"estimated_total\":\"200.00\",\"deposit_type\":\"cash\",\"deposit_amount\":\"500.00\"}"
    api_post "/mobile/rentals" "$client_b_bearer"
    EXPECT_FAIL=0
    assert_http "overlap 409" "409"
    ok

    step "rental_A still confirmed in DB"
    local db_b
    db_b=$(psql_exec "SELECT status FROM rentals WHERE id='${rental_a}';")
    assert_eq "A still confirmed" "$db_b" "confirmed"
    ok

    return 0
}

# ---------------------------------------------------------------------------
# SCENARIO E — Extension reject then retry
# ---------------------------------------------------------------------------
scenario_e() {
    local client_bearer admin_bearer rental_id ext_id_1 ext_id_2

    step "client signup + admin login + verify client"
    client_bearer=$(signup_and_login_client)
    admin_bearer=$(login_admin)
    verify_client_as_admin "$admin_bearer" "$(last_client_email)"
    ok

    step "client books E2E-003 -> pending"
    local start end
    start=$(date -v+21d '+%Y-%m-%dT10:00:00Z' 2>/dev/null || date -d '+21 days' '+%Y-%m-%dT10:00:00Z')
    end=$(date   -v+23d '+%Y-%m-%dT10:00:00Z' 2>/dev/null || date -d '+23 days' '+%Y-%m-%dT10:00:00Z')
    POST_BODY="{\"organization_id\":\"${DEFAULT_ORG_ID}\",\"vehicle_id\":\"${V3}\",\"booking_type\":\"daily\",\"scheduled_start\":\"${start}\",\"scheduled_end\":\"${end}\",\"base_rate\":\"100.00\",\"rate_type\":\"per_day\",\"estimated_total\":\"200.00\",\"deposit_type\":\"cash\",\"deposit_amount\":\"500.00\"}"
    api_post "/mobile/rentals" "$client_bearer"
    assert_http "booking E" "201"
    rental_id=$(printf '%s' "$LAST_BODY" | jq -r '.id')
    ok

    step "admin approves + checkin -> active"
    POST_BODY="{}"
    api_post "/rentals/${rental_id}/approve" "$admin_bearer"
    assert_http "approve E" "200"
    POST_BODY='{"checkin_data":{"mileage":0,"fuel_level":100}}'
    api_post "/rentals/${rental_id}/checkin" "$admin_bearer"
    assert_http "checkin E" "204"
    local db_status
    db_status=$(psql_exec "SELECT status FROM rentals WHERE id='${rental_id}';")
    assert_eq "active" "$db_status" "active"
    ok

    step "client requests extension +1 day -> pending"
    local new_end_1 ext_status
    new_end_1=$(date -v+24d '+%Y-%m-%dT10:00:00Z' 2>/dev/null || date -d '+24 days' '+%Y-%m-%dT10:00:00Z')
    POST_BODY="{\"new_end_date\":\"${new_end_1}\",\"additional_cost\":\"100.00\"}"
    api_post "/mobile/rentals/${rental_id}/extend-request" "$client_bearer"
    assert_http "ext 1" "201"
    ext_id_1=$(printf '%s' "$LAST_BODY" | jq -r '.id')
    ext_status=$(psql_exec "SELECT status FROM extension_requests WHERE id='${ext_id_1}';")
    assert_eq "ext_1 pending" "$ext_status" "pending"
    ok

    step "admin rejects ext_1 -> rejected; scheduled_end unchanged"
    local original_end
    original_end=$(psql_exec "SELECT scheduled_end FROM rentals WHERE id='${rental_id}';")
    POST_BODY='{"rejection_reason":"vehicle booked next"}'
    api_post "/rentals/${ext_id_1}/extension/reject" "$admin_bearer"
    assert_http "reject ext_1" "200"
    local db_ext1
    db_ext1=$(psql_exec "SELECT status FROM extension_requests WHERE id='${ext_id_1}';")
    assert_eq "ext_1 rejected" "$db_ext1" "rejected"
    local after_end
    after_end=$(psql_exec "SELECT scheduled_end FROM rentals WHERE id='${rental_id}';")
    assert_eq "scheduled_end unchanged" "$after_end" "$original_end"
    ok

    step "client submits ext_2 (+2 days) -> pending"
    local new_end_2
    new_end_2=$(date -v+25d '+%Y-%m-%dT10:00:00Z' 2>/dev/null || date -d '+25 days' '+%Y-%m-%dT10:00:00Z')
    POST_BODY="{\"new_end_date\":\"${new_end_2}\",\"additional_cost\":\"200.00\"}"
    api_post "/mobile/rentals/${rental_id}/extend-request" "$client_bearer"
    assert_http "ext 2" "201"
    ext_id_2=$(printf '%s' "$LAST_BODY" | jq -r '.id')
    ext_status=$(psql_exec "SELECT status FROM extension_requests WHERE id='${ext_id_2}';")
    assert_eq "ext_2 pending" "$ext_status" "pending"
    ok

    step "admin approves ext_2 -> approved"
    POST_BODY="{}"
    api_post "/rentals/${ext_id_2}/extension/approve" "$admin_bearer"
    assert_http "approve ext_2" "200"
    local db_ext2
    db_ext2=$(psql_exec "SELECT status FROM extension_requests WHERE id='${ext_id_2}';")
    assert_eq "ext_2 approved" "$db_ext2" "approved"
    ok

    return 0
}

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
print_summary() {
    local total_start="$1"
    local all_pass=true

    printf "\n${BOLD}=== Summary ===${RESET}\n" >&2

    _line() {
        local letter="$1" name="$2"
        local result steps elapsed
        eval "result=\"\$RESULT_${letter}\""
        eval "steps=\"\$STEPS_${letter}\""
        eval "elapsed=\"\$TIME_${letter}\""
        case "$result" in
            PASS) printf "  ${GREEN}%-4s %-46s PASS  (%s steps, %s)${RESET}\n" \
                      "$letter" "$name" "$steps" "$elapsed" >&2 ;;
            FAIL) printf "  ${RED}%-4s %-46s FAIL${RESET}\n" \
                      "$letter" "$name" >&2; all_pass=false ;;
            *)    printf "  ${YELLOW}%-4s %-46s SKIP${RESET}\n" \
                      "$letter" "$name" >&2 ;;
        esac
    }

    _line A "Happy path"
    _line B "Client cancels before approval"
    _line C "Manager rejects"
    _line D "Date overlap caught at approval"
    _line E "Extension reject then retry"

    local total_end
    total_end=$(date +%s)
    local total_elapsed=$(( total_end - total_start ))

    printf "\n" >&2
    if $all_pass; then
        printf "${GREEN}${BOLD}All scenarios green in %ss.${RESET}\n" "$total_elapsed" >&2
    else
        printf "${RED}${BOLD}One or more scenarios FAILED.${RESET}\n" >&2
        exit 1
    fi
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
SCENARIOS="${1:-ABCDE}"
CURRENT_STEP=0
TOTAL_START=$(date +%s)

case "$SCENARIOS" in *A*) run_scenario A "Happy path"                      scenario_a ;; esac
case "$SCENARIOS" in *B*) run_scenario B "Client cancels before approval"  scenario_b ;; esac
case "$SCENARIOS" in *C*) run_scenario C "Manager rejects"                 scenario_c ;; esac
case "$SCENARIOS" in *D*) run_scenario D "Date overlap caught at approval" scenario_d ;; esac
case "$SCENARIOS" in *E*) run_scenario E "Extension reject then retry"     scenario_e ;; esac

print_summary "$TOTAL_START"
