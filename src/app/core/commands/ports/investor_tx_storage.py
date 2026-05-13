from typing import Protocol

from app.core.common.entities.investor import Investor
from app.core.common.entities.types_ import InvestorId


class InvestorTxStorage(Protocol):
    def add(self, investor: Investor) -> None: ...

    async def get_by_id(
        self,
        investor_id: InvestorId,
        *,
        for_update: bool = False,
    ) -> Investor | None: ...
