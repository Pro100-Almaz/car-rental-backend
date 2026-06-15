from app.core.common.authorization.authorize import authorize
from app.core.common.authorization.current_user_service import CurrentUserService, logger
from app.core.common.authorization.rbac import HasPermission, PermissionCheckContext
from app.core.queries.models.client_documents import GetClientDocumentsQm
from app.core.queries.ports.client_document_reader import ClientDocumentReader
from app.core.queries.ports.mobile_rental_reader import MobileRentalReader


class GetMyDocuments:
    def __init__(
        self,
        current_user_service: CurrentUserService,
        client_document_reader: ClientDocumentReader,
        mobile_rental_reader: MobileRentalReader,
    ) -> None:
        self._current_user_service = current_user_service
        self._client_reader = client_document_reader
        self._mobile_rental_reader = mobile_rental_reader

    async def execute(self) -> GetClientDocumentsQm:
        logger.info("Get my documents: started.")

        current_user = await self._current_user_service.get_current_user()

        authorize(
            HasPermission(),
            context=PermissionCheckContext(
                subject=current_user,
                required_permission="mobile.documents",
            ),
        )

        return await self._client_reader.list_client_documents(client_id=current_user.id_)
