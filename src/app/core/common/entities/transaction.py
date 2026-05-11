from decimal import Decimal
from typing import Any

from app.core.common.entities.base import Entity
from app.core.common.entities.types_ import (
    ClientId,
    OrganizationId,
    PaymentMethod,
    RentalId,
    TransactionId,
    TransactionStatus,
    TransactionType,
)
from app.core.common.value_objects.utc_datetime import UtcDatetime


class Transaction(Entity[TransactionId]):
    def __init__(
        self,
        *,
        id_: TransactionId,
        organization_id: OrganizationId,
        rental_id: RentalId | None,
        client_id: ClientId,
        type_: TransactionType,
        amount: Decimal,
        currency: str,
        payment_method: PaymentMethod,
        status: TransactionStatus,
        external_id: str | None,
        metadata: dict[str, Any] | None,
        created_at: UtcDatetime,
        updated_at: UtcDatetime,
    ) -> None:
        super().__init__(id_=id_)
        self.organization_id = organization_id
        self.rental_id = rental_id
        self.client_id = client_id
        self.type_ = type_
        self.amount = amount
        self.currency = currency
        self.payment_method = payment_method
        self.status = status
        self.external_id = external_id
        self.metadata = metadata
        self._created_at = created_at
        self.updated_at = updated_at

    @property
    def created_at(self) -> UtcDatetime:
        return self._created_at
