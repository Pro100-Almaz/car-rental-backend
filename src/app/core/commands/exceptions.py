from typing import ClassVar

from app.core.common.exceptions import BaseError


class EmailAlreadyExistsError(BaseError):
    default_message: ClassVar[str] = "Email already exists."


class UserNotFoundError(BaseError):
    default_message: ClassVar[str] = "User not found."


class OrganizationNotFoundError(BaseError):
    default_message: ClassVar[str] = "Organization not found."


class OrganizationSlugAlreadyExistsError(BaseError):
    default_message: ClassVar[str] = "Organization slug already exists."


class BranchNotFoundError(BaseError):
    default_message: ClassVar[str] = "Branch not found."


class VehicleNotFoundError(BaseError):
    default_message: ClassVar[str] = "Vehicle not found."


class InvalidVehicleStatusTransitionError(BaseError):
    default_message: ClassVar[str] = "Invalid vehicle status transition."


class ClientNotFoundError(BaseError):
    default_message: ClassVar[str] = "Client not found."


class RentalNotFoundError(BaseError):
    default_message: ClassVar[str] = "Rental not found."


class InvalidRentalStatusTransitionError(BaseError):
    default_message: ClassVar[str] = "Invalid rental status transition."


class TransactionNotFoundError(BaseError):
    default_message: ClassVar[str] = "Transaction not found."


class InvalidTransactionStatusTransitionError(BaseError):
    default_message: ClassVar[str] = "Invalid transaction status transition."


class FineNotFoundError(BaseError):
    default_message: ClassVar[str] = "Fine not found."


class ServiceTaskNotFoundError(BaseError):
    default_message: ClassVar[str] = "Service task not found."


class InvalidTaskStatusTransitionError(BaseError):
    default_message: ClassVar[str] = "Invalid task status transition."


class InvestorNotFoundError(BaseError):
    default_message: ClassVar[str] = "Investor not found."


class VehicleInvestorNotFoundError(BaseError):
    default_message: ClassVar[str] = "Vehicle-investor binding not found."


class InvestorPayoutNotFoundError(BaseError):
    default_message: ClassVar[str] = "Investor payout not found."


class InvalidPayoutStatusTransitionError(BaseError):
    default_message: ClassVar[str] = "Invalid payout status transition."
