from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, status
from fastapi_error_map import ErrorAwareRouter

from app.core.commands.create_vehicle_document import (
    CreateVehicleDocument,
    CreateVehicleDocumentRequest,
    CreateVehicleDocumentResponse,
)
from app.core.commands.delete_vehicle_document import (
    DeleteVehicleDocument,
    DeleteVehicleDocumentRequest,
    VehicleDocumentNotFoundError,
)
from app.core.common.exceptions import BusinessTypeError
from app.core.queries.list_vehicle_documents import ListVehicleDocuments, ListVehicleDocumentsRequest
from app.core.queries.models.vehicle_document import ListVehicleDocumentsQm
from app.infrastructure.exceptions import ReaderError, StorageError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE


def make_vehicle_documents_router() -> APIRouter:
    router = ErrorAwareRouter(prefix="/vehicle-documents", tags=["Vehicle Documents"])

    @router.post(
        "/",
        error_map={
            StorageError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
            BusinessTypeError: status.HTTP_400_BAD_REQUEST,
        },
        default_on_error=log_info,
        status_code=status.HTTP_201_CREATED,
    )
    @inject
    async def create_vehicle_document(
        request: CreateVehicleDocumentRequest,
        interactor: FromDishka[CreateVehicleDocument],
    ) -> CreateVehicleDocumentResponse:
        return await interactor.execute(request)

    @router.get(
        "/",
        error_map={
            ReaderError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
        },
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def list_vehicle_documents(
        vehicle_id: UUID,
        interactor: FromDishka[ListVehicleDocuments],
    ) -> ListVehicleDocumentsQm:
        return await interactor.execute(
            ListVehicleDocumentsRequest(vehicle_id=vehicle_id)
        )

    @router.delete(
        "/{document_id}",
        error_map={
            StorageError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
            VehicleDocumentNotFoundError: status.HTTP_404_NOT_FOUND,
        },
        default_on_error=log_info,
        status_code=status.HTTP_204_NO_CONTENT,
    )
    @inject
    async def delete_vehicle_document(
        document_id: UUID,
        interactor: FromDishka[DeleteVehicleDocument],
    ) -> None:
        await interactor.execute(
            DeleteVehicleDocumentRequest(document_id=document_id)
        )

    return router
