from fastapi_error_map import ErrorTranslator, SimpleErrorResponseModel


class ServiceUnavailableTranslator(ErrorTranslator[SimpleErrorResponseModel]):
    @property
    def error_response_model_cls(self) -> type[SimpleErrorResponseModel]:
        return SimpleErrorResponseModel

    def from_error(self, err: Exception) -> SimpleErrorResponseModel:
        return SimpleErrorResponseModel(error="Service temporarily unavailable. Please try again later.")


class RateLimitedTranslator(ErrorTranslator[SimpleErrorResponseModel]):
    """Returns a 429 Too Many Requests response."""

    @property
    def error_response_model_cls(self) -> type[SimpleErrorResponseModel]:
        return SimpleErrorResponseModel

    def from_error(self, err: Exception) -> SimpleErrorResponseModel:
        return SimpleErrorResponseModel(error="Too many requests. Please slow down.")


class LockedTranslator(ErrorTranslator[SimpleErrorResponseModel]):
    """Returns a 423 Locked response with Retry-After: 900."""

    @property
    def error_response_model_cls(self) -> type[SimpleErrorResponseModel]:
        return SimpleErrorResponseModel

    def from_error(self, err: Exception) -> SimpleErrorResponseModel:
        return SimpleErrorResponseModel(
            error="Account temporarily locked due to too many failed login attempts. "
            "Please try again in 15 minutes."
        )
