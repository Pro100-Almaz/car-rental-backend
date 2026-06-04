from typing import Protocol

from app.core.common.entities.extension_request import ExtensionRequest
from app.core.common.entities.types_ import ExtensionRequestId, RentalId


class ExtensionRequestTxStorage(Protocol):
    def add(self, extension_request: ExtensionRequest) -> None: ...

    async def get_by_id(
        self,
        extension_request_id: ExtensionRequestId,
        *,
        for_update: bool = False,
    ) -> ExtensionRequest | None: ...

    async def get_pending_for_rental(
        self,
        rental_id: RentalId,
    ) -> ExtensionRequest | None: ...
