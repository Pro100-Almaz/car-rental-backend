from typing import Protocol

from app.core.common.entities.fine import Fine
from app.core.common.entities.types_ import FineId


class FineTxStorage(Protocol):
    def add(self, fine: Fine) -> None: ...

    async def get_by_id(
        self,
        fine_id: FineId,
        *,
        for_update: bool = False,
    ) -> Fine | None: ...
