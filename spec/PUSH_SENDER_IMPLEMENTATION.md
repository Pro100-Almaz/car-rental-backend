# PushSender — Real Implementation

> Replace the silent `StubPushSender` with a working push-notification adapter so reminder, overdue, and pickup notifications actually reach user devices.
> Estimated effort: **~1 day** (provider setup + adapter + tests + ops doc).
> Risk: **Medium** — touches infra (credentials), but the port contract is stable and the swap is a single IoC binding.

---

## Context — what already exists

The project has the full *consumer* side of push notifications wired up. Only the *delivery* layer is stubbed.

| Concern | Location | Status |
|---|---|---|
| Port (interface) | `src/app/core/common/ports/push_sender.py` | Defined. `async send(*, device_token, title, body, data=None) -> bool` |
| Stub adapter | `src/app/infrastructure/adapters/stub_push_sender.py` | Logs and returns `True`. Production today. |
| IoC binding | `src/app/main/ioc/core.py:296` | `provide(StubPushSender, provides=PushSender)` |
| Consumer | `src/app/core/common/services/notification_service.py` | Already calls `PushSender.send(...)` |
| Trigger handlers | `CheckOverdueRentals`, `CheckPickupReminders`, `CheckReturnReminders` (in `src/app/core/commands/`) | Use `NotificationService` — fully implemented |
| Device tokens | Stored in the user/device table per the data model (see `docs/DATA_MODEL.md`) | Collected from mobile clients, currently dead-end data |

Conclusion: implementing a real `PushSender` is **a drop-in replacement**. No callers change.

---

## Scope

In-scope:
- Choose a provider and wire it up.
- New adapter class implementing the existing `PushSender` Protocol.
- Configuration via env vars (credentials, project IDs, environment toggle).
- IoC swap: prod uses the real adapter, tests keep `StubPushSender`.
- Unit tests for the adapter (mocked SDK) + an integration test that asserts `NotificationService` reaches the adapter.
- Ops note in `docs/DEPLOYMENT.md` describing the credential rollout.

Out of scope (own specs later if needed):
- Notification preferences UI / per-user opt-out.
- Retry/dead-letter queue for failed sends.
- Per-platform payload variants (rich media, action buttons).
- Token-lifecycle cleanup (purging stale tokens on `Unregistered` errors — *recommended follow-up*, not blocking).

---

## Provider decision

Recommended: **Firebase Cloud Messaging (FCM) via `firebase-admin`**.

Rationale:
- Single SDK covers Android (native FCM) and iOS (FCM acts as APNs proxy).
- Free tier covers MVP volume comfortably.
- Server-side auth is a service-account JSON file — no per-request token mint.
- `firebase-admin` is async-friendly when wrapped via `asyncio.to_thread` (the SDK itself is sync).

Alternatives considered:
- **APNs + FCM directly** — only if iOS-specific features (critical alerts, App Clips) are needed. Not yet.
- **OneSignal / Expo / Pusher Beams** — extra vendor with no clear win over FCM at this stage.

If the team prefers a different provider, the only file that changes is the adapter — keep the port stable.

---

## Implementation outline

> This is a *plan*, not code. No implementation lands as part of this spec.

### 1. Add config

`src/app/main/configs/...` — extend the settings module with:

```
PUSH_PROVIDER=fcm           # default; "stub" disables sends in dev
FCM_CREDENTIALS_PATH=/run/secrets/fcm.json
FCM_DEFAULT_TIMEOUT_SEC=5
```

Update `env.example` with sensible defaults (`PUSH_PROVIDER=stub` locally).

### 2. Add adapter

`src/app/infrastructure/adapters/fcm_push_sender.py` — a class implementing the existing `PushSender` Protocol:

- Lazily initializes the Firebase app once per process from the credentials file.
- `send(...)` builds a `messaging.Message` and dispatches it via `asyncio.to_thread(messaging.send, msg)`.
- Maps SDK exceptions:
  - `firebase_admin.messaging.UnregisteredError` → log + return `False` (token is dead — feeds future cleanup job).
  - `firebase_admin.messaging.InvalidArgumentError` → log + raise a domain `PushPayloadError`.
  - Network/timeouts → log + return `False`.
- No retries inside the adapter — the caller (NotificationService) decides retry policy.

### 3. Swap IoC binding

`src/app/main/ioc/core.py:296` — replace:

```python
push_sender = provide(StubPushSender, provides=PushSender)
```

with a factory that picks `FCMPushSender` or `StubPushSender` based on `settings.push.provider`. Tests stay on the stub by overriding the binding in the test container.

### 4. Tests

- Unit (`tests/unit/infrastructure/adapters/test_fcm_push_sender.py`):
  - Mocks `firebase_admin.messaging.send`.
  - Asserts payload shape (title, body, data dict serialization).
  - Covers each error-mapping branch.
- Integration (`tests/integration/no_infra/test_notification_service_dispatches.py`):
  - Wires `NotificationService` with a recording fake `PushSender`.
  - Confirms each `Check*Reminders` handler ultimately calls `PushSender.send` once per matched rental.

### 5. Ops

- Add a `secrets/` mount or use the platform's secrets manager. Document in `docs/DEPLOYMENT.md`.
- Rotate the FCM service-account key procedure (a 3-step checklist).
- Add a metric/log line `push.sent` and `push.failed` so the rate is observable from day 1.

---

## Acceptance

- Setting `PUSH_PROVIDER=stub` keeps current behavior (no external traffic).
- Setting `PUSH_PROVIDER=fcm` with valid creds delivers a real notification to a registered test device.
- All existing tests still pass; new unit + integration tests pass.
- `docs/DEPLOYMENT.md` includes the credential-rollout note.

---

## Risks / open questions

- **Credential storage.** Where does the FCM JSON live in each env? (Secret manager vs. file mount.) Resolve before merging.
- **Token cleanup.** When FCM returns `Unregistered`, who deletes the dead token? Recommendation: emit a domain event from the adapter and let a follow-up handler purge it. Out of scope here.
- **Multi-org isolation.** If different organizations need different Firebase projects, the adapter must accept an `organization_id`-keyed credential map. Current design assumes one project for the whole platform — confirm with stakeholders.
