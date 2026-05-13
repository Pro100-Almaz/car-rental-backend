from datetime import date, datetime
from decimal import Decimal

from app.core.common.entities.base import Entity
from app.core.common.entities.types_ import (
    CashJournalEntryId,
    ExpenseCategoryId,
    OperationType,
    OrganizationId,
    PaymentMethod,
    RentalId,
    UserId,
    VehicleId,
)
from app.core.common.value_objects.utc_datetime import UtcDatetime


class CashJournalEntry(Entity[CashJournalEntryId]):
    def __init__(
        self,
        *,
        id_: CashJournalEntryId,
        organization_id: OrganizationId,
        date: date,
        operation_type: OperationType,
        vehicle_id: VehicleId | None,
        rental_id: RentalId | None,
        expense_category_id: ExpenseCategoryId | None,
        payment_method: PaymentMethod,
        amount: Decimal,
        description: str | None,
        receipt_url: str | None,
        confirmed_by: UserId | None,
        confirmed_at: datetime | None,
        created_by: UserId,
        created_at: UtcDatetime,
    ) -> None:
        super().__init__(id_=id_)
        self.organization_id = organization_id
        self.date = date
        self.operation_type = operation_type
        self.vehicle_id = vehicle_id
        self.rental_id = rental_id
        self.expense_category_id = expense_category_id
        self.payment_method = payment_method
        self.amount = amount
        self.description = description
        self.receipt_url = receipt_url
        self.confirmed_by = confirmed_by
        self.confirmed_at = confirmed_at
        self.created_by = created_by
        self._created_at = created_at

    @property
    def created_at(self) -> UtcDatetime:
        return self._created_at
