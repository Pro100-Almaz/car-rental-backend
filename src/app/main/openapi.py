"""Custom OpenAPI schema: enables Swagger UI's Authorize button for bearer JWT.

All routes default to requiring `bearerAuth`; the few public routes (signup,
login, refresh, password recovery, default-organization lookup) explicitly
declare `security: []` so they remain callable without a token.

Internal job endpoints are not affected — their router is mounted with
`include_in_schema=False` and never appears in the OpenAPI document.
"""

from typing import Any

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

# Path + method pairs that should NOT require bearer auth. Paths are the
# OpenAPI-relative paths (i.e. they include the `/api/v1/...` prefix as set by
# the routers).
_PUBLIC_OPERATIONS: frozenset[tuple[str, str]] = frozenset(
    {
        ("post", "/api/v1/account/signup/"),
        ("post", "/api/v1/account/login/"),
        ("post", "/api/v1/account/refresh/"),
        ("post", "/api/v1/account/verify-email/"),
        ("post", "/api/v1/account/resend-verification/"),
        ("post", "/api/v1/account/forgot-password/"),
        ("post", "/api/v1/account/reset-password/"),
        ("get", "/api/v1/account/default-organization/"),
    }
)


def setup_openapi(app: FastAPI) -> None:
    """Install a custom OpenAPI generator that wires bearer-JWT security."""

    def custom_openapi() -> dict[str, Any]:
        if app.openapi_schema:
            return app.openapi_schema

        schema = get_openapi(
            title=app.title,
            version=app.version,
            summary=app.summary,
            description=app.description,
            routes=app.routes,
        )

        components = schema.setdefault("components", {})
        security_schemes = components.setdefault("securitySchemes", {})
        security_schemes["bearerAuth"] = {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": (
                "Paste your access_token here (the one returned by "
                "`POST /account/login/` or `POST /account/refresh/`). "
                "Do NOT include the word `Bearer`."
            ),
        }

        # Default every operation to require the bearer; override public ones.
        for path, path_item in schema.get("paths", {}).items():
            for method, operation in path_item.items():
                if method not in {"get", "post", "put", "patch", "delete"}:
                    continue
                if (method, path) in _PUBLIC_OPERATIONS:
                    operation["security"] = []
                else:
                    operation["security"] = [{"bearerAuth": []}]

        app.openapi_schema = schema
        return schema

    app.openapi = custom_openapi  # type: ignore[method-assign]
