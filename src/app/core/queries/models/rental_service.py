from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True, slots=True)
class RentalServiceQm:
    id: UUID
    rental_id: UUID
    service_id: UUID
    quantity: int
    price: Decimal
