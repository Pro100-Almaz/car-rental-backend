from typing import Protocol

from app.core.common.entities.transaction import Transaction
from app.core.common.entities.types_ import TransactionId


class PaymentTxStorage(Protocol):
    def add(self, transaction: Transaction) -> None: ...

    async def get_by_id(
        self,
        transaction_id: TransactionId,
        *,
        for_update: bool = False,
    ) -> Transaction | None: ...
