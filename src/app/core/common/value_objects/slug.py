import re
from dataclasses import dataclass
from typing import ClassVar

from app.core.common.exceptions import BusinessTypeError
from app.core.common.value_objects.base import ValueObject


@dataclass(frozen=True, slots=True, repr=False)
class Slug(ValueObject):
    MIN_LEN: ClassVar[int] = 2
    MAX_LEN: ClassVar[int] = 63

    PATTERN: ClassVar[re.Pattern[str]] = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

    value: str

    def __post_init__(self) -> None:
        self._validate(self.value)

    @classmethod
    def _validate(cls, value: str) -> None:
        if len(value) < cls.MIN_LEN or len(value) > cls.MAX_LEN:
            raise BusinessTypeError(f"{cls.__name__} must be between {cls.MIN_LEN} and {cls.MAX_LEN} characters.")
        if not cls.PATTERN.fullmatch(value):
            raise BusinessTypeError(
                f"{cls.__name__} can only contain lowercase letters, digits, and hyphens (not leading/trailing)."
            )
