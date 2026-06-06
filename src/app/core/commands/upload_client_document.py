import logging
from dataclasses import dataclass

from app.core.commands.exceptions import ClientNotFoundError
from app.core.commands.ports.client_tx_storage import ClientTxStorage
from app.core.commands.ports.transaction_manager import TransactionManager
from app.core.commands.ports.utc_timer import UtcTimer
from app.core.common.authorization.authorize import authorize
from app.core.common.authorization.current_user_service import CurrentUserService
from app.core.common.authorization.rbac import HasPermission, PermissionCheckContext
from app.core.common.value_objects.utc_datetime import UtcDatetime

logger = logging.getLogger(__name__)


class InvalidDocumentTypeError(Exception):
    pass


@dataclass(frozen=True, slots=True, kw_only=True)
class UploadClientDocumentRequest:
    document_type: str
    document_url: str


VALID_DOCUMENT_TYPES = {"id_front", "id_back", "license_front", "license_back"}

DOCUMENT_TYPE_FIELD_MAP = {
    "id_front": "id_document_url",
    "id_back": "id_document_url",
    "license_front": "license_front_url",
    "license_back": "license_back_url",
}


class UploadClientDocument:
    def __init__(
        self,
        current_user_service: CurrentUserService,
        utc_timer: UtcTimer,
        client_tx_storage: ClientTxStorage,
        transaction_manager: TransactionManager,
    ) -> None:
        self._current_user_service = current_user_service
        self._utc_timer = utc_timer
        self._client_tx_storage = client_tx_storage
        self._transaction_manager = transaction_manager

    async def execute(self, request: UploadClientDocumentRequest) -> None:
        logger.info("Upload client document: started.")

        current_user = await self._current_user_service.get_current_user()
        authorize(
            HasPermission(),
            context=PermissionCheckContext(
                subject=current_user,
                required_permission="mobile.profile",
            ),
        )

        if request.document_type not in VALID_DOCUMENT_TYPES:
            raise InvalidDocumentTypeError(
                f"Invalid document type: {request.document_type}. Must be one of {VALID_DOCUMENT_TYPES}"
            )

        client = await self._client_tx_storage.get_by_user_id(current_user.id_, for_update=True)
        if client is None:
            raise ClientNotFoundError

        field_name = DOCUMENT_TYPE_FIELD_MAP[request.document_type]
        setattr(client, field_name, request.document_url)
        client.updated_at = UtcDatetime(self._utc_timer.now.value)
        await self._transaction_manager.commit()

        logger.info("Upload client document: done.")
