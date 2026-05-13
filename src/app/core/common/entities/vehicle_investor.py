from decimal import Decimal

from app.core.common.entities.base import Entity
from app.core.common.entities.types_ import (
    InvestorId,
    ProfitDistributionType,
    VehicleId,
    VehicleInvestorId,
)
from app.core.common.value_objects.utc_datetime import UtcDatetime


class VehicleInvestor(Entity[VehicleInvestorId]):
    def __init__(
        self,
        *,
        id_: VehicleInvestorId,
        vehicle_id: VehicleId,
        investor_id: InvestorId,
        share_percentage: Decimal,
        profit_distribution_type: ProfitDistributionType,
        created_at: UtcDatetime,
    ) -> None:
        super().__init__(id_=id_)
        self.vehicle_id = vehicle_id
        self.investor_id = investor_id
        self.share_percentage = share_percentage
        self.profit_distribution_type = profit_distribution_type
        self._created_at = created_at

    @property
    def created_at(self) -> UtcDatetime:
        return self._created_at
