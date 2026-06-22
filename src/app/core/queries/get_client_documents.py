from uuid import UUID

from app.core.common.authorization.authorize import authorize
from app.core.common.authorization.current_user_service import CurrentUserService, logger
from app.core.common.authorization.rbac import HasPermission, PermissionCheckContext
from app.core.queries.models.client_documents import GetClientDocumentsQm
from app.core.queries.ports.client_document_reader import ClientDocumentReader


class GetClientDocuments:
    def __init__(
        self,
        client_document_reader: ClientDocumentReader,
        current_user_service: CurrentUserService,
    ) -> None:
        self._client_document_reader = client_document_reader
        self._current_user_service = current_user_service

    async def execute(self, client_id: UUID | None) -> GetClientDocumentsQm:
        logger.info("Get my documents: started.")

        if not client_id:
            raise ValueError("Client id is required")

        current_user = await self._current_user_service.get_current_user()

        authorize(
            HasPermission(),
            context=PermissionCheckContext(
                subject=current_user,
                required_permission="client.documents",
            ),
        )
        return await self._client_document_reader.list_client_documents(client_id=client_id)
