import logging
from dataclasses import dataclass
from uuid import UUID

from app.core.queries.models.transaction import TransactionQm
from app.core.queries.ports.transaction_reader import TransactionReader

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class GetTransactionRequest:
    transaction_id: UUID


class GetTransaction:
    def __init__(
        self,
        transaction_reader: TransactionReader,
    ) -> None:
        self._transaction_reader = transaction_reader

    async def execute(self, request: GetTransactionRequest) -> TransactionQm | None:
        logger.info("Get transaction: started.")

        result = await self._transaction_reader.get_by_id(
            transaction_id=request.transaction_id,
        )

        logger.info("Get transaction: done.")
        return result
