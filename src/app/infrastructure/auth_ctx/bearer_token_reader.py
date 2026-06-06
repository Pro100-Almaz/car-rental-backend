"""Extracts the Bearer access token from the incoming Request.

Request-scoped. Replaces `CookieManager.read` for the auth flow. No staging side
(refresh-token rotation returns new tokens in the response body, not via a Set-Cookie
roundtrip).
"""

from starlette.requests import Request

_SCHEME_AND_TOKEN_PARTS = 2


class BearerTokenReader:
    def __init__(self, request: Request) -> None:
        self._request = request

    def read(self) -> str | None:
        auth = self._request.headers.get("authorization")
        if not auth:
            return None
        parts = auth.split(None, 1)
        if len(parts) != _SCHEME_AND_TOKEN_PARTS or parts[0].lower() != "bearer":
            return None
        token = parts[1].strip()
        return token or None
