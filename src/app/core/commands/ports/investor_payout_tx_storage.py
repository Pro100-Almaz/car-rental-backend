from typing import Protocol

from app.core.common.entities.investor_payout import InvestorPayout
from app.core.common.entities.types_ import InvestorPayoutId


class InvestorPayoutTxStorage(Protocol):
    def add(self, payout: InvestorPayout) -> None: ...

    async def get_by_id(
        self,
        payout_id: InvestorPayoutId,
        *,
        for_update: bool = False,
    ) -> InvestorPayout | None: ...
