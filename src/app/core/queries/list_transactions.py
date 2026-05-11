import logging
from dataclasses import dataclass
from uuid import UUID

from app.core.queries.ports.transaction_reader import ListTransactionsQm, TransactionReader

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class ListTransactionsRequest:
    organization_id: UUID
    rental_id: UUID | None = None
    client_id: UUID | None = None
    type_: str | None = None
    status: str | None = None


class ListTransactions:
    def __init__(
        self,
        transaction_reader: TransactionReader,
    ) -> None:
        self._transaction_reader = transaction_reader

    async def execute(self, request: ListTransactionsRequest) -> ListTransactionsQm:
        logger.info("List transactions: started.")

        result = await self._transaction_reader.list_transactions(
            organization_id=request.organization_id,
            rental_id=request.rental_id,
            client_id=request.client_id,
            type_=request.type_,
            status=request.status,
        )

        logger.info("List transactions: done.")
        return result
