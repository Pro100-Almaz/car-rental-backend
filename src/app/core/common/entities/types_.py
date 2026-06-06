from enum import StrEnum
from typing import NewType
from uuid import UUID

OrganizationId = NewType("OrganizationId", UUID)
BranchId = NewType("BranchId", UUID)
UserId = NewType("UserId", UUID)
VehicleId = NewType("VehicleId", UUID)
ClientId = NewType("ClientId", UUID)
RentalId = NewType("RentalId", UUID)
TransactionId = NewType("TransactionId", UUID)
FineId = NewType("FineId", UUID)
ServiceTaskId = NewType("ServiceTaskId", UUID)
InvestorId = NewType("InvestorId", UUID)
VehicleInvestorId = NewType("VehicleInvestorId", UUID)
InvestorPayoutId = NewType("InvestorPayoutId", UUID)
VehiclePricingId = NewType("VehiclePricingId", UUID)
VehicleDocumentId = NewType("VehicleDocumentId", UUID)
VehicleCategoryId = NewType("VehicleCategoryId", UUID)
AdditionalServiceId = NewType("AdditionalServiceId", UUID)
RentalServiceId = NewType("RentalServiceId", UUID)
ExpenseCategoryId = NewType("ExpenseCategoryId", UUID)
CashJournalEntryId = NewType("CashJournalEntryId", UUID)
NotificationId = NewType("NotificationId", UUID)
DeviceTokenId = NewType("DeviceTokenId", UUID)
ExtensionRequestId = NewType("ExtensionRequestId", UUID)
ClientOrganizationId = NewType("ClientOrganizationId", UUID)
UserPasswordHash = NewType("UserPasswordHash", bytes)
RefreshTokenId = NewType("RefreshTokenId", UUID)
RefreshTokenFamilyId = NewType("RefreshTokenFamilyId", UUID)
AccessTokenJti = NewType("AccessTokenJti", UUID)


class VehicleStatus(StrEnum):
    AVAILABLE = "available"
    RESERVED = "reserved"
    RENTED = "rented"
    RETURNING = "returning"
    IN_SERVICE = "in_service"
    IN_WASH = "in_wash"
    DECOMMISSIONED = "decommissioned"
    SOLD = "sold"


class FuelType(StrEnum):
    PETROL = "petrol"
    DIESEL = "diesel"
    GAS = "gas"
    ELECTRIC = "electric"
    HYBRID = "hybrid"


class Transmission(StrEnum):
    MANUAL = "manual"
    AUTOMATIC = "automatic"


class VerificationStatus(StrEnum):
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"


class TrustLevel(StrEnum):
    NEW = "new"
    VERIFIED = "verified"
    TRUSTED = "trusted"
    VIP = "vip"


class RentalStatus(StrEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    ACTIVE = "active"
    RETURNING = "returning"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    DISPUTED = "disputed"


class BookingType(StrEnum):
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class RateType(StrEnum):
    PER_HOUR = "per_hour"
    PER_DAY = "per_day"
    PER_WEEK = "per_week"
    PER_MONTH = "per_month"


class DepositType(StrEnum):
    CASH = "cash"
    CARD_HOLD = "card_hold"
    KASPI = "kaspi"
    DEBT = "debt"


class DepositStatus(StrEnum):
    PENDING = "pending"
    HELD = "held"
    PARTIALLY_REFUNDED = "partially_refunded"
    REFUNDED = "refunded"
    FORFEITED = "forfeited"


class PrepaymentStatus(StrEnum):
    NONE = "none"
    PARTIAL = "partial"
    FULL = "full"


class TransactionType(StrEnum):
    RENTAL_PAYMENT = "rental_payment"
    DEPOSIT_HOLD = "deposit_hold"
    DEPOSIT_REFUND = "deposit_refund"
    FINE_CHARGE = "fine_charge"
    WALLET_TOPUP = "wallet_topup"
    DEBT_PAYMENT = "debt_payment"
    PLATFORM_FEE = "platform_fee"


class PaymentMethod(StrEnum):
    KASPI = "kaspi"
    CARD = "card"
    CASH = "cash"
    WALLET = "wallet"
    BANK_TRANSFER = "bank_transfer"


class TransactionStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    REJECTED = "rejected"


class ServiceTaskType(StrEnum):
    WASH = "wash"
    MECHANICAL_SERVICE = "mechanical_service"
    REPAIR = "repair"
    RELOCATION = "relocation"
    INSPECTION = "inspection"
    FUEL_TOPUP = "fuel_topup"


class TaskPriority(StrEnum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class TaskStatus(StrEnum):
    CREATED = "created"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    PHOTO_PROOF = "photo_proof"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class FineType(StrEnum):
    TRAFFIC = "traffic"
    PARKING = "parking"
    TOLL = "toll"
    OTHER = "other"


class FineStatus(StrEnum):
    PENDING = "pending"
    CHARGED_TO_CLIENT = "charged_to_client"
    PAID_BY_OPERATOR = "paid_by_operator"
    DISPUTED = "disputed"


class InvestorType(StrEnum):
    OWN = "own"
    PARTNER = "partner"
    SHARED = "shared"


class PayoutStatus(StrEnum):
    CALCULATED = "calculated"
    APPROVED = "approved"
    PAID = "paid"


class ProfitDistributionType(StrEnum):
    PERCENTAGE = "percentage"
    FIXED = "fixed"


class UserRole(StrEnum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    BOOKING_MANAGER = "booking_manager"
    FINANCIAL_MANAGER = "financial_manager"
    INVESTOR = "investor"
    TECHNICIAN = "technician"
    CLIENT = "client"

    @property
    def is_system(self) -> bool:
        return self == UserRole.SUPER_ADMIN


class OperationType(StrEnum):
    INCOME = "income"
    EXPENSE = "expense"


class ExpenseCategoryType(StrEnum):
    DIRECT = "direct"
    OVERHEAD = "overhead"


class RegistrationSource(StrEnum):
    MANUAL = "manual"
    MOBILE = "mobile"


class RentalSource(StrEnum):
    MANUAL = "manual"
    MOBILE = "mobile"


class TransactionSource(StrEnum):
    MANUAL = "manual"
    MOBILE = "mobile"
    AUTO = "auto"


class NotificationType(StrEnum):
    DOCUMENT_APPROVED = "document_approved"
    DOCUMENT_REJECTED = "document_rejected"
    BOOKING_CONFIRMED = "booking_confirmed"
    BOOKING_CANCELLED = "booking_cancelled"
    PICKUP_REMINDER = "pickup_reminder"
    RETURN_REMINDER = "return_reminder"
    OVERDUE_ALERT = "overdue_alert"
    RENTAL_COMPLETED = "rental_completed"
    EXTENSION_APPROVED = "extension_approved"
    EXTENSION_REJECTED = "extension_rejected"
    FINE_ADDED = "fine_added"
    PAYMENT_CONFIRMED = "payment_confirmed"
    PAYMENT_REJECTED = "payment_rejected"
    DEBT_REMINDER = "debt_reminder"


class DevicePlatform(StrEnum):
    IOS = "ios"
    ANDROID = "android"


class ExtensionRequestStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
