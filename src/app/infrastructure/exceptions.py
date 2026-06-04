from typing import ClassVar

from app.core.common.exceptions import BaseError


class StorageError(BaseError):
    pass


class ReaderError(BaseError):
    pass


class EmailSendError(BaseError):
    default_message: ClassVar[str] = "Failed to send email. Please try again later."
