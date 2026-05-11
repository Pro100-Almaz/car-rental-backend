from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.commands.ports.payment_tx_storage import PaymentTxStorage
from app.core.common.entities.transaction import Transaction
from app.core.common.entities.types_ import TransactionId
from app.infrastructure.exceptions import StorageError


class SqlaPaymentTxStorage(PaymentTxStorage):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def add(self, transaction: Transaction) -> None:
        try:
            self._session.add(transaction)
        except SQLAlchemyError as e:
            raise StorageError from e

    async def get_by_id(
        self,
        transaction_id: TransactionId,
        *,
        for_update: bool = False,
    ) -> Transaction | None:
        try:
            return await self._session.get(
                Transaction,
                transaction_id,
                with_for_update=for_update,
            )
        except SQLAlchemyError as e:
            raise StorageError from e
