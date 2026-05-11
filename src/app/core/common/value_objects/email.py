import re
from dataclasses import dataclass
from typing import ClassVar

from app.core.common.exceptions import BusinessTypeError
from app.core.common.value_objects.base import ValueObject


@dataclass(frozen=True, slots=True, repr=False)
class Email(ValueObject):
    MAX_LEN: ClassVar[int] = 254

    PATTERN: ClassVar[re.Pattern[str]] = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

    value: str

    def __post_init__(self) -> None:
        self._validate(self.value)

    @classmethod
    def _validate(cls, value: str) -> None:
        if len(value) > cls.MAX_LEN:
            raise BusinessTypeError(f"{cls.__name__} must be at most {cls.MAX_LEN} characters.")
        if not cls.PATTERN.fullmatch(value):
            raise BusinessTypeError(f"{cls.__name__} is not a valid email address.")
