import logging
from dataclasses import dataclass
from uuid import UUID

from app.core.commands.ports.client_document_tx_storage import ClientDocumentTxStorage
from app.core.commands.ports.transaction_manager import TransactionManager
from app.core.commands.ports.utc_timer import UtcTimer
from app.core.common.authorization.authorize import authorize
from app.core.common.authorization.current_user_service import CurrentUserService
from app.core.common.authorization.rbac import HasPermission, PermissionCheckContext
from app.core.common.entities.types_ import ClientDocumentStatus
from app.core.common.services.client_document_service import ClientDocumentService, UploadedDocumentFile
from app.core.common.value_objects.utc_datetime import UtcDatetime

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class UpdateClientDocumentRequest:
    document_id: UUID
    client_id: UUID
    document_type: str
    status: ClientDocumentStatus
    file: UploadedDocumentFile
    name: str
    description: str | None = None


class ClientDocumentNotFoundError(Exception):
    pass


class UpdateClientDocument:
    def __init__(
        self,
        current_user_service: CurrentUserService,
        client_document_service: ClientDocumentService,
        client_document_tx_storage: ClientDocumentTxStorage,
        transaction_manager: TransactionManager,
        utc_timer: UtcTimer,
    ) -> None:
        self._client_document_service = client_document_service
        self._current_user_service = current_user_service
        self._client_document_tx_storage = client_document_tx_storage
        self._transaction_manager = transaction_manager
        self._utc_timer = utc_timer

    async def execute(self, request: UpdateClientDocumentRequest) -> None:
        logger.info("Update client document: started.")

        current_user = await self._current_user_service.get_current_user()
        authorize(
            HasPermission(),
            context=PermissionCheckContext(
                subject=current_user,
                required_permission="client.documents",
            ),
        )

        new_url: str | None = None
        old_url: str | None = None

        try:
            client_document = await self._client_document_tx_storage.get_by_id(request.document_id)

            if client_document is None:
                raise ClientDocumentNotFoundError

            if client_document.client_id != request.client_id:
                raise ClientDocumentNotFoundError

            old_url = client_document.url

            if request.file is not None:
                new_url = await self._client_document_service.save_uploaded_file(
                    file=request.file,
                    client_id=request.client_id,
                    document_id=request.document_id,
                    document_type=request.document_type,
                    document_description=request.description,
                )

                client_document.update_file_url(url=new_url, updated_at=UtcDatetime(self._utc_timer.now.value))

            client_document.update_metadata(
                name=request.name,
                status=request.status,
                updated_at=UtcDatetime(self._utc_timer.now.value),
                description=request.description,
            )

            await self._client_document_tx_storage.flush()
            await self._transaction_manager.commit()

        except Exception:
            if new_url:
                self._client_document_service.delete_uploaded_file(new_url)

            raise

        if new_url and old_url:
            self._client_document_service.delete_uploaded_file(old_url)
