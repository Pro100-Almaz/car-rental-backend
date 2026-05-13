from datetime import date, datetime
from decimal import Decimal

from app.core.common.entities.base import Entity
from app.core.common.entities.types_ import (
    InvestorId,
    InvestorPayoutId,
    OrganizationId,
    PayoutStatus,
)
from app.core.common.value_objects.utc_datetime import UtcDatetime


class InvestorPayout(Entity[InvestorPayoutId]):
    def __init__(
        self,
        *,
        id_: InvestorPayoutId,
        organization_id: OrganizationId,
        investor_id: InvestorId,
        period_month: date,
        calculated_profit: Decimal,
        share_amount: Decimal,
        status: PayoutStatus,
        paid_at: datetime | None,
        notes: str | None,
        created_at: UtcDatetime,
    ) -> None:
        super().__init__(id_=id_)
        self.organization_id = organization_id
        self.investor_id = investor_id
        self.period_month = period_month
        self.calculated_profit = calculated_profit
        self.share_amount = share_amount
        self.status = status
        self.paid_at = paid_at
        self.notes = notes
        self._created_at = created_at

    @property
    def created_at(self) -> UtcDatetime:
        return self._created_at
