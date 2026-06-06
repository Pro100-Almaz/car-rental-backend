# JWT Auth Mobile — React Native / Expo Implementation Plan

> Client-side counterpart to `spec/AUTH_JWT_BACKEND.md`. Defines how the mobile app stores tokens, attaches them to requests, recovers from access-token expiry, and handles the long-tail UX edges (background resume, offline, biometric unlock, push token rotation).
>
> Estimated effort: **~1.5 days** (one PR in the mobile repo).
> Risk: **Medium** — every API call now flows through a new interceptor; a bug here logs every user out at once.
>
> Depends on: backend ships `/account/login/`, `/account/refresh/`, `/account/logout/` per the backend spec.

## Why

The current backend rolls a `Set-Cookie` on every response when the session is past 80% of its TTL. React Native does not have a cookie jar that automatically participates in this dance; even if it did, sharing cookies across the app's lifecycle (fetch, WebSocket, push registration, file uploads) is messy. The body-based bearer model is the standard mobile contract: store two strings securely, attach one to every request, swap them when one expires.

Target stack: **React Native + Expo SDK**, TypeScript, `expo-secure-store` superseded by direct Keychain/Keystore access for tokens (see "Token storage"). If/when the codebase moves off Expo, this spec works the same on bare RN.

## Token storage

Tokens are bearer credentials. Anything that reads them can impersonate the user for the lifetime of the token. We pick the strongest storage the platform offers.

| Storage | Use for refresh token | Use for access token | Why |
|---|---|---|---|
| iOS Keychain (Generic Password, `kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly`) | yes | yes | Hardware-backed where available, not in iCloud Backup, not readable while device is locked, not transferable to a new device. |
| Android Keystore + EncryptedSharedPreferences | yes | yes | AES-256-GCM with hardware-bound key. Stays encrypted at rest. |
| `AsyncStorage` / `expo-secure-store` (Expo's RN wrapper) | **no** | acceptable only as the in-memory cache backing | `AsyncStorage` is plaintext. `expo-secure-store` is fine on simulators and decent on device, but lacks the `kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly` knob and the `setUserAuthenticationRequired` Android Keystore knob, so we use the platform modules directly when we need those guarantees. For dev/MVP, `expo-secure-store` is acceptable provided it is documented as a downgrade. |
| In-memory (`useRef` / Zustand store) | as cache only | yes | Survives the app lifetime, cleared on cold start (forces a re-read from Keychain on launch). Good for the access token because the hot path is "attach to header." |

**Recommendation, in order**:

1. **Production**: native modules — `react-native-keychain` (iOS Keychain + Android Keystore) for both tokens. The wrapper handles the access-control flags. Both tokens in one keychain item as a JSON blob `{access, refresh, accessExp, refreshExp}` so a successful read returns the full auth state.
2. **MVP / dev**: `expo-secure-store` is acceptable. Document the downgrade in the PR.
3. Access token additionally cached in an in-memory store (Zustand / Jotai / a plain module-level ref) so the hot path does not hit the keychain on every request.

Never put tokens in `AsyncStorage`, Redux Persist with default storage, or any logging output. The HTTP interceptor strips the `Authorization` header from any error report sent to Sentry/Bugsnag.

## Auth client layer

One module. Everything goes through it. Recommended primitive: `axios` because the interceptor model is clean. If the rest of the app uses `fetch`, wrap it the same way.

### Components

```
authClient/
  storage.ts         // keychain read/write/clear, exposes get/set/clear
  tokens.ts          // in-memory access cache + helpers (isAccessExpiringSoon, getAccess, getRefresh)
  refresh.ts         // single-flight refresh (the mutex — see below)
  api.ts             // axios instance with request + response interceptors
  events.ts          // emits "logged-out" so the UI can react
```

### Request interceptor

For every outbound request:

1. If a logout is in progress, abort the request.
2. Read the in-memory access token. If absent, read from keychain (cold-start path) and warm the cache.
3. If `access.expiresAt - now < 30s`, proactively call the refresh flow before sending. This pre-emptive refresh avoids most 401-retry loops and is cheap.
4. Set `Authorization: Bearer <access>`.

### Response interceptor

On every response:

- If status != 401 → pass through.
- If status == 401 **and** the request URL is not itself `/account/refresh/` or `/account/login/` **and** this request has not already been retried (mark with a `_retried` flag on the config):
  1. Call the single-flight refresh.
  2. If refresh succeeds → mutate the original request's `Authorization` header to the new access token and retry once.
  3. If refresh fails → trigger logout, propagate the original 401 up. The UI navigates to `/login`.
- If the failing request *is* `/account/refresh/` returning 401 → trigger logout immediately.

### Logout-on-401-from-refresh — the recovery flow

```
trigger logout
  → clear in-memory access
  → clear keychain
  → best-effort POST /account/logout/ (don't await; don't error if it fails)
  → unregister push token (see "Push notifications")
  → emit "logged-out" → AppNavigator listens, swaps to AuthStack
```

## Concurrent refresh — the single-flight problem

When the access token expires, 8 in-flight requests get 401 simultaneously. Each one would, naively, kick off its own refresh — and because the backend rotates refresh tokens, the second refresh sees a revoked token (the first one already rotated it) and the backend interprets that as a **replay attack** and kills the whole family. Every user gets logged out the moment two requests race a refresh. Not acceptable.

### The fix — a promise mutex

```ts
// refresh.ts (shape, not final code)
let inflight: Promise<TokenPair> | null = null;

export function refreshTokens(): Promise<TokenPair> {
  if (inflight) return inflight;
  inflight = doRefresh().finally(() => { inflight = null; });
  return inflight;
}
```

Every interceptor that hits a 401 calls `refreshTokens()`. Only the first call actually fires `POST /account/refresh/`; all others await the same promise. The new refresh token is written to the keychain once, all callers resume their original requests.

**Crucial invariant**: only one `POST /account/refresh/` is ever in flight per app process. Violating this means the backend kills the family and the user is logged out.

Across processes (a Share Extension on iOS, say) this is harder — but the share extension does not make authed network calls in our app, so this is a non-issue today. If/when it does, the keychain item becomes the lock (read with `setUserAuthenticationRequired` so only one process can read at a time, with file-system advisory locking, or just don't do auth from extensions).

## Background app refresh

The OS suspends the app. When the user opens it again, both tokens may be hours or days old.

Resume flow:

1. App returns to foreground (`AppState` event).
2. Read tokens from keychain into memory.
3. If refresh token's `expiresAt > now` → fine, the request interceptor will refresh on demand.
4. If refresh token expired → wipe everything, navigate to login, show a non-alarming "Please sign in again" message.

Do **not** preemptively call `/refresh/` on every foreground event — it is wasted load. Lazy refresh on the first authed call after foreground is enough.

## Offline / no-network

The HTTP interceptor cannot distinguish "the token is bad" from "the network is unreachable" without inspecting the error. Behaviour:

- `NETWORK_ERROR` (DNS, connection timeout, fetch failed before headers): do **not** clear tokens. Surface a toast "No internet connection." Retry is the caller's choice.
- `HTTP 401`: as above.
- `HTTP 5xx` from `/refresh/`: do **not** clear tokens — the server is the problem. Treat the original request's 401 as transient; the next call will retry the refresh. Show "Service is having a moment" if it persists.
- Anything else: pass through.

For requests made *while* offline, the app shows the offline UI; queued mutations (if any — out of scope for v1) are retried with whatever access token is in keychain at retry time.

## Biometric unlock — optional, opt-in

Posted as a follow-up feature, not in the initial migration. When implemented:

- App setting "Require Face ID / Touch ID to use this app."
- When enabled, the keychain item is stored with `accessControl: BIOMETRY_CURRENT_SET` (iOS) and `setUserAuthenticationRequired(true)` (Android Keystore).
- Reading tokens triggers the OS biometric prompt.
- On three failed biometric attempts the app falls back to "please sign in with your password" (i.e. log out).

Not in scope for the initial JWT migration; mention here so the storage layer is designed to support it.

## Logout

User taps "Log out":

1. Disable the logout button (prevents double-tap).
2. Best-effort fire-and-forget `POST /account/logout/` with the current refresh token. Do not await — if the network is down, we still want to log the user out locally.
3. Unregister push token (see below).
4. Clear in-memory state.
5. Clear keychain item.
6. Navigate to the auth stack.

Server-side the refresh token is revoked; access token's `jti` is denylisted; the user's lingering 14 minutes of access token life is dead.

## Push notification token lifecycle

The mobile app registers a push token via `POST /mobile/devices/register` once it has a logged-in session. The token lives independently of the auth tokens; it identifies the device, not the credentials.

On events:

- **Login** (fresh app install or after explicit logout): immediately after login, register the push token. If a token is already registered for the device but for a different user, the server replaces it (server-side concern; the client just calls register).
- **Refresh**: no action. The push token does not change just because the bearer rotated.
- **Logout**: before clearing the keychain, call the push-unregister endpoint (`DELETE /mobile/devices/<token>` or whatever the existing endpoint is). Best-effort; failure does not block logout. The server eventually expires unused tokens anyway.
- **App reinstall / re-login**: the FCM/APNs token changes → re-register on next login.

This is unchanged by the JWT migration; called out so it is not missed in the PR review.

## Error mapping

Surface human messages from server codes. Keep them generic — do not echo the server's "wrong password" because the server itself is generic for security.

| Status | Endpoint | User-facing message |
|---|---|---|
| 400 | login | "Please check your email and password." |
| 401 | login | "Incorrect email or password." (the server intentionally lumps unknown-email and bad-password together; we relay) |
| 401 | refresh | (no message; trigger silent logout + login screen) |
| 401 | any other authed call | (silent; interceptor handles) |
| 403 | login (`EmailNotVerifiedError`) | "Please verify your email — we sent you a link." + button to call resend-verification |
| 423 | login | "Too many sign-in attempts. Please try again in 15 minutes." (or use `Retry-After` if present) |
| 429 | any | "You're going a little fast. Please wait a moment and try again." |
| 5xx | login / refresh | "Something on our end. Please try again in a moment." |
| network | any | "No internet connection." |

The auth client emits these as semantic events; the UI translates them to localised strings.

## Testing

Manual QA:

- **Happy path**: login → use app for 20 minutes → confirm a refresh fires (network tab shows `/refresh/`) → keep using → no logout.
- **Force-expire access**: temporarily set the backend's access TTL to 60 seconds via env, log in, wait, make a request, observe one 401 → one refresh → original request retried with 200. Visible in the app without any user feedback.
- **Force-expire refresh**: set refresh TTL to 120 seconds, log in, wait > 2 minutes, make a request → app navigates to login. No crash, no lingering UI in a broken state.
- **Concurrent refresh**: fire 10 parallel requests immediately after access expiry (e.g. by spamming pull-to-refresh on a list screen). Network tab shows exactly one `/refresh/`; all 10 listed requests succeed.
- **Replay simulation**: capture a refresh token (dev build only), perform a refresh, replay the **old** captured token via curl, then continue using the app → app gets logged out on the next refresh because the family was killed. This verifies the backend's family-kill works end-to-end.
- **Logout**: tap logout, immediately re-open the app → on auth stack, no flash of authed UI.
- **Background**: open app, send to background for 1 hour, return → first action works (lazy refresh fires). Send to background for > refresh TTL, return → routed to login.
- **Airplane mode**: airplane mode on, make a request → "No internet" toast, tokens not cleared, airplane off → next request works.
- **Logout-all from another device**: log in on Device A, log in on Device B, change password from Device B → Device A's next request returns 401, app goes to login.

Automation:

- Unit tests on `refresh.ts` for the mutex — a deterministic test that fires N parallel calls and asserts the underlying refresh function is called exactly once.
- Mocked-axios integration test for the 401-retry path.
- E2E (Detox / Maestro): the "force-expire access" scenario above.

## Acceptance

- Tokens are never written to `AsyncStorage` or any plaintext store. (Grep the diff.)
- The auth header is never logged to the console or sent to Sentry. (Sentry beforeSend strips it.)
- Exactly one `POST /account/refresh/` per app session per access expiry. (Verified via network capture under load.)
- Logout works offline (clears local state, network call is fire-and-forget).
- Foregrounding after refresh expiry → user is on the login screen within one frame, no crash, no flash of authed content.
- Push token registration happens immediately after a successful login; push unregister happens before keychain wipe on logout.
- All hard-coded user-facing strings are localizable (i18n keys, not raw strings).

## Non-goals

- Biometric unlock — flagged as the immediate follow-up; not in the initial PR.
- Multi-account support (switching between two signed-in accounts on the same device) — future.
- Background push triggering silent token refresh — future.
- Sharing auth with a Watch / widget / extension target — none today.
- Reusing the storage module for a future iOS-native or Android-native client — design accommodates it, implementation is RN-only here.
