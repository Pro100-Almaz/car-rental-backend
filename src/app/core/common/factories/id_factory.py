from uuid import UUID

from uuid_utils import compat as uuid_utils

from app.core.common.entities.types_ import (
    AdditionalServiceId,
    BranchId,
    CashJournalEntryId,
    ClientId,
    ExpenseCategoryId,
    FineId,
    InvestorId,
    InvestorPayoutId,
    OrganizationId,
    RentalId,
    RentalServiceId,
    ServiceTaskId,
    TransactionId,
    UserId,
    VehicleId,
    VehicleInvestorId,
    VehiclePricingId,
)


def create_organization_id(value: UUID | None = None) -> OrganizationId:
    return OrganizationId(value if value is not None else uuid_utils.uuid7())


def create_branch_id(value: UUID | None = None) -> BranchId:
    return BranchId(value if value is not None else uuid_utils.uuid7())


def create_user_id(value: UUID | None = None) -> UserId:
    return UserId(value if value is not None else uuid_utils.uuid7())


def create_vehicle_id(value: UUID | None = None) -> VehicleId:
    return VehicleId(value if value is not None else uuid_utils.uuid7())


def create_client_id(value: UUID | None = None) -> ClientId:
    return ClientId(value if value is not None else uuid_utils.uuid7())


def create_rental_id(value: UUID | None = None) -> RentalId:
    return RentalId(value if value is not None else uuid_utils.uuid7())


def create_transaction_id(value: UUID | None = None) -> TransactionId:
    return TransactionId(value if value is not None else uuid_utils.uuid7())


def create_fine_id(value: UUID | None = None) -> FineId:
    return FineId(value if value is not None else uuid_utils.uuid7())


def create_service_task_id(value: UUID | None = None) -> ServiceTaskId:
    return ServiceTaskId(value if value is not None else uuid_utils.uuid7())


def create_investor_id(value: UUID | None = None) -> InvestorId:
    return InvestorId(value if value is not None else uuid_utils.uuid7())


def create_vehicle_investor_id(value: UUID | None = None) -> VehicleInvestorId:
    return VehicleInvestorId(value if value is not None else uuid_utils.uuid7())


def create_investor_payout_id(value: UUID | None = None) -> InvestorPayoutId:
    return InvestorPayoutId(value if value is not None else uuid_utils.uuid7())


def create_vehicle_pricing_id(value: UUID | None = None) -> VehiclePricingId:
    return VehiclePricingId(value if value is not None else uuid_utils.uuid7())


def create_additional_service_id(value: UUID | None = None) -> AdditionalServiceId:
    return AdditionalServiceId(value if value is not None else uuid_utils.uuid7())


def create_rental_service_id(value: UUID | None = None) -> RentalServiceId:
    return RentalServiceId(value if value is not None else uuid_utils.uuid7())


def create_expense_category_id(value: UUID | None = None) -> ExpenseCategoryId:
    return ExpenseCategoryId(value if value is not None else uuid_utils.uuid7())


def create_cash_journal_entry_id(value: UUID | None = None) -> CashJournalEntryId:
    return CashJournalEntryId(value if value is not None else uuid_utils.uuid7())
