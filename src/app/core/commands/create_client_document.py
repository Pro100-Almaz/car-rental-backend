import logging
import uuid
from dataclasses import dataclass
from uuid import UUID

from app.core.commands.ports.client_document_tx_storage import ClientDocumentTxStorage
from app.core.commands.ports.transaction_manager import TransactionManager
from app.core.commands.ports.utc_timer import UtcTimer
from app.core.common.authorization.authorize import authorize
from app.core.common.authorization.current_user_service import CurrentUserService
from app.core.common.authorization.rbac import HasPermission, PermissionCheckContext
from app.core.common.entities.client_documents import ClientDocument
from app.core.common.entities.types_ import ClientDocumentId, ClientDocumentStatus, ClientDocumentType, ClientId
from app.core.common.services.client_document_service import ClientDocumentService, UploadedDocumentFile
from app.core.common.value_objects.utc_datetime import UtcDatetime

logger = logging.getLogger(__name__)


class InvalidDocumentTypeError(Exception):
    pass


@dataclass(frozen=True, slots=True, kw_only=True)
class CreateClientDocumentRequest:
    client_id: UUID
    document_type: str
    description: str | None = None
    file: UploadedDocumentFile


DOCUMENT_DESCRIPTIONS = {"id_front", "license_front", "license_back"}


class CreateClientDocument:
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

    async def execute(self, request: CreateClientDocumentRequest) -> UUID:
        logger.info("Create client document: started.")

        current_user = await self._current_user_service.get_current_user()
        authorize(
            HasPermission(),
            context=PermissionCheckContext(
                subject=current_user,
                required_permission="client.documents",
            ),
        )

        document_id = uuid.uuid4()
        now = UtcDatetime(self._utc_timer.now.value)
        saved_url: str | None = None

        try:
            document_name = f"{request.document_type}_{request.client_id}"
            client_document = ClientDocument(
                id_=ClientDocumentId(document_id),
                client_id=ClientId(request.client_id),
                document_type=ClientDocumentType(request.document_type),
                status=ClientDocumentStatus.Pending,
                name=document_name,
                description=request.description,
                url="",
                created_at=now,
                updated_at=now,
            )

            self._client_document_tx_storage.add(client_document)

            await self._client_document_tx_storage.flush()

            saved_url = await self._client_document_service.save_uploaded_file(
                file=request.file,
                client_id=request.client_id,
                document_id=document_id,
                document_type=request.document_type,
                document_description=request.description,
            )

            client_document.update_file_url(url=saved_url, updated_at=UtcDatetime(self._utc_timer.now.value))

            await self._client_document_tx_storage.flush()
            await self._transaction_manager.commit()
        except Exception:
            if saved_url:
                self._client_document_service.delete_uploaded_file(saved_url)
            raise
        return document_id
