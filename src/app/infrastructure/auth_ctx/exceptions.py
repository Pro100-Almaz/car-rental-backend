from typing import ClassVar

from app.core.common.exceptions import BaseError


class AuthenticationError(BaseError):
    default_message: ClassVar[str] = "Not authenticated."


class AlreadyAuthenticatedError(BaseError):
    default_message: ClassVar[str] = "You are already authenticated. Consider logging out."


class ReAuthenticationError(BaseError):
    default_message: ClassVar[str] = "Invalid password."


class AuthenticationChangeError(BaseError):
    default_message: ClassVar[str] = "New password must differ from current password."


class EmailNotVerifiedError(BaseError):
    default_message: ClassVar[str] = "Email is not verified. Please verify your email first."


class InvalidVerificationCodeError(BaseError):
    default_message: ClassVar[str] = "Invalid or expired verification code."


class VerificationCodeRateLimitError(BaseError):
    default_message: ClassVar[str] = "Please wait before requesting a new code."


class EmailAlreadyVerifiedError(BaseError):
    default_message: ClassVar[str] = "Email is already verified."


class InvalidInviteError(BaseError):
    default_message: ClassVar[str] = "Invalid or expired invite."


class InviteAlreadyUsedError(BaseError):
    default_message: ClassVar[str] = "This invite has already been used."
