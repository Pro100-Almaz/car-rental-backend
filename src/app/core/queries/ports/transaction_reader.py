from abc import abstractmethod
from typing import Protocol, TypedDict
from uuid import UUID

from app.core.queries.models.transaction import TransactionQm


class ListTransactionsQm(TypedDict):
    transactions: list[TransactionQm]
    total: int


class TransactionReader(Protocol):
    @abstractmethod
    async def get_by_id(
        self,
        *,
        transaction_id: UUID,
    ) -> TransactionQm | None: ...

    @abstractmethod
    async def list_transactions(
        self,
        *,
        organization_id: UUID,
        rental_id: UUID | None = None,
        client_id: UUID | None = None,
        type_: str | None = None,
        status: str | None = None,
    ) -> ListTransactionsQm: ...
