from uuid import UUID

from uuid_utils import compat as uuid_utils

from app.core.common.entities.types_ import (
    BranchId,
    ClientId,
    FineId,
    OrganizationId,
    RentalId,
    ServiceTaskId,
    TransactionId,
    UserId,
    VehicleId,
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
