from typing import Protocol

from app.core.common.entities.additional_service import AdditionalService
from app.core.common.entities.types_ import AdditionalServiceId


class AdditionalServiceTxStorage(Protocol):
    def add(self, additional_service: AdditionalService) -> None: ...

    async def get_by_id(
        self,
        additional_service_id: AdditionalServiceId,
        *,
        for_update: bool = False,
    ) -> AdditionalService | None: ...
