# Default-Organization Discovery Endpoint

> Public endpoint so the signup UI can pre-populate (or hide) the `organization_id` field when an instance has a single default tenant configured.
>
> Estimated effort: **~10 min**.
> Risk: **Very low** — read-only, no schema, no new DI binding.

## Why

The signup handler already supports an env-driven `DEFAULT_ORGANIZATION_ID` fallback (`infrastructure/auth_ctx/handlers/sign_up.py:165-168`). The frontend currently has no way to know whether that value is set — so it can't decide whether to show an org picker or skip the field. Exposing the value via a small unauthenticated GET fixes that.

## Endpoint

```
GET /api/v1/account/default-organization/
```

- **Auth:** none (signup must work for unauthenticated users).
- **Response:** `200 OK`
  ```json
  { "organization_id": "019e549b-5ab4-71d1-9290-17de7937b9e3" }
  ```
  or, if unset:
  ```json
  { "organization_id": null }
  ```

200 (not 404) for the "unset" case so the frontend handles one shape, branching on `organization_id != null`.

## Changes

1. **New file** `src/app/presentation/http/account/get_default_organization.py`:
   - Pydantic response model `DefaultOrganizationResponse` with `organization_id: UUID | None`.
   - `ErrorAwareRouter` with the standard error_map for an auth-optional GET.
   - Handler resolves `DefaultOrganizationId` via `FromDishka` and returns it.

2. **Edit** `src/app/presentation/http/account/router.py`:
   - Import + include the new router.

No changes to commands, DI, or config — `DefaultOrganizationId` provider already exists (`main/ioc/infrastructure.py:200`).

## Acceptance

- `curl http://localhost:8000/api/v1/account/default-organization/` returns `200` with `{"organization_id": null}` when `APP_DEFAULT_ORGANIZATION_ID` is unset.
- Setting `APP_DEFAULT_ORGANIZATION_ID=<some-uuid>` (via `.secrets` for local dev) and restarting the stack — the same curl returns that UUID.
- OpenAPI schema at `/openapi.json` lists the new path under the `Account` tag.

## Non-goals

- Returning the org's display name / slug. Add later if the frontend needs more than the ID.
- Multiple-default-org support (one per region etc.). Out of scope.
- Caching / ETag. Endpoint is cheap.
