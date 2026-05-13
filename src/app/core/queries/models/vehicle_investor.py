from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True, slots=True)
class VehicleInvestorQm:
    id: UUID
    vehicle_id: UUID
    investor_id: UUID
    share_percentage: Decimal
    profit_distribution_type: str
    created_at: datetime
