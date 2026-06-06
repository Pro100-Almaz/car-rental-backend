"""Extracts the Bearer access token from the incoming Request.

Request-scoped. Replaces `CookieManager.read` for the auth flow. No staging side
(refresh-token rotation returns new tokens in the response body, not via a Set-Cookie
roundtrip).
"""

from starlette.requests import Request


class BearerTokenReader:
    def __init__(self, request: Request) -> None:
        self._request = request

    def read(self) -> str | None:
        auth = self._request.headers.get("authorization")
        if not auth:
            return None
        parts = auth.split(None, 1)
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return None
        token = parts[1].strip()
        return token or None
