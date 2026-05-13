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
AdditionalServiceId = NewType("AdditionalServiceId", UUID)
RentalServiceId = NewType("RentalServiceId", UUID)
ExpenseCategoryId = NewType("ExpenseCategoryId", UUID)
CashJournalEntryId = NewType("CashJournalEntryId", UUID)
UserPasswordHash = NewType("UserPasswordHash", bytes)


class VehicleCategory(StrEnum):
    ECONOMY = "economy"
    COMFORT = "comfort"
    BUSINESS = "business"
    SUV = "suv"
    MINIVAN = "minivan"


class VehicleStatus(StrEnum):
    AVAILABLE = "available"
    RESERVED = "reserved"
    RENTED = "rented"
    RETURNING = "returning"
    IN_SERVICE = "in_service"
    IN_WASH = "in_wash"
    DECOMMISSIONED = "decommissioned"


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
    OWNER = "owner"
    BRANCH_MANAGER = "branch_manager"
    DISPATCHER = "dispatcher"
    FINANCE = "finance"
    FIELD_STAFF = "field_staff"
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
