import logging
from dataclasses import dataclass
from uuid import UUID

from app.core.commands.ports.client_document_tx_storage import ClientDocumentTxStorage
from app.core.commands.ports.transaction_manager import TransactionManager
from app.core.common.authorization.authorize import authorize
from app.core.common.authorization.current_user_service import CurrentUserService
from app.core.common.authorization.rbac import HasPermission, PermissionCheckContext
from app.core.common.services.client_document_service import ClientDocumentService

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class DeleteClientDocumentRequest:
    document_id: UUID
    client_id: UUID


class ClientDocumentNotFoundError(Exception):
    pass


class DeleteClientDocument:
    def __init__(
        self,
        current_user_service: CurrentUserService,
        client_document_service: ClientDocumentService,
        client_document_tx_storage: ClientDocumentTxStorage,
        transaction_manager: TransactionManager,
    ) -> None:
        self._client_document_service = client_document_service
        self._current_user_service = current_user_service
        self._client_document_tx_storage = client_document_tx_storage
        self._transaction_manager = transaction_manager

    async def execute(self, request: DeleteClientDocumentRequest) -> None:
        logger.info("Delete client document: started.")

        current_user = await self._current_user_service.get_current_user()
        authorize(
            HasPermission(),
            context=PermissionCheckContext(
                subject=current_user,
                required_permission="client.documents",
            ),
        )

        old_url: str | None = None

        client_document = await self._client_document_tx_storage.get_by_id(request.document_id)

        if client_document is None:
            raise ClientDocumentNotFoundError

        if client_document.client_id != request.client_id:
            raise ClientDocumentNotFoundError

        old_url = client_document.url

        await self._client_document_tx_storage.delete(client_document)
        await self._client_document_tx_storage.flush()
        await self._transaction_manager.commit()

        if old_url:
            self._client_document_service.delete_uploaded_file(old_url)
