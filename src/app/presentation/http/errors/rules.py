from typing import Final

from fastapi_error_map.rules import Rule, rule
from starlette import status

from app.presentation.http.errors.translators import RateLimitedTranslator, ServiceUnavailableTranslator

HTTP_503_SERVICE_UNAVAILABLE_RULE: Final[Rule] = rule(
    status=status.HTTP_503_SERVICE_UNAVAILABLE,
    translator=ServiceUnavailableTranslator(),
)

HTTP_429_RATE_LIMITED_RULE: Final[Rule] = rule(
    status=status.HTTP_429_TOO_MANY_REQUESTS,
    translator=RateLimitedTranslator(),
)
