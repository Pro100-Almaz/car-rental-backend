from decimal import Decimal

from app.core.common.entities.base import Entity
from app.core.common.entities.types_ import AdditionalServiceId, RentalId, RentalServiceId
from app.core.common.value_objects.utc_datetime import UtcDatetime


class RentalService(Entity[RentalServiceId]):
    def __init__(
        self,
        *,
        id_: RentalServiceId,
        rental_id: RentalId,
        service_id: AdditionalServiceId,
        quantity: int,
        price: Decimal,
        created_at: UtcDatetime,
    ) -> None:
        super().__init__(id_=id_)
        self.rental_id = rental_id
        self.service_id = service_id
        self.quantity = quantity
        self.price = price
        self._created_at = created_at

    @property
    def created_at(self) -> UtcDatetime:
        return self._created_at
