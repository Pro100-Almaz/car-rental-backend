from typing import Annotated
from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, File, Form, UploadFile, status
from fastapi_error_map import ErrorAwareRouter

from app.core.commands.create_client_document import CreateClientDocument, CreateClientDocumentRequest
from app.core.commands.delete_client_document import DeleteClientDocument, DeleteClientDocumentRequest
from app.core.commands.update_client_document import UpdateClientDocument, UpdateClientDocumentRequest
from app.core.common.entities.types_ import ClientDocumentStatus
from app.core.common.exceptions import ClientNotFoundError
from app.core.queries.get_client_documents import GetClientDocuments
from app.core.queries.models.client_documents import GetClientDocumentsQm
from app.infrastructure.auth_ctx.exceptions import AuthenticationError
from app.infrastructure.exceptions import ReaderError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE


class CreateUpdateClintrDocumentBody:
    document_type: str


def make_client_documents_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.get(
        "/{client_id}/documents",
        error_map={
            AuthenticationError: status.HTTP_401_UNAUTHORIZED,
            ReaderError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
        },
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def get_documents(interactor: FromDishka[GetClientDocuments], client_id: UUID) -> GetClientDocumentsQm:
        result = await interactor.execute(client_id)
        if result is None:
            raise ClientNotFoundError
        return result

    @router.post(
        "/{client_id}/documents",
        error_map={
            AuthenticationError: status.HTTP_401_UNAUTHORIZED,
            ReaderError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
        },
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def create_document(
        interactor: FromDishka[CreateClientDocument],
        client_id: UUID,
        document_type: Annotated[str, Form()],
        file: Annotated[UploadFile, File()],
        description: Annotated[str | None, Form()] = None,
    ) -> dict[str, UUID]:
        document_id = await interactor.execute(
            CreateClientDocumentRequest(
                client_id=client_id, document_type=document_type, file=file, description=description
            )
        )

        return {"id": document_id}

    @router.patch(
        "/client/{client_id}/documents",
        error_map={
            AuthenticationError: status.HTTP_401_UNAUTHORIZED,
            ReaderError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
        },
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def update_document(
        interactor: FromDishka[UpdateClientDocument],
        client_id: UUID,
        document_id: Annotated[UUID, Form()],
        document_type: Annotated[str, Form()],
        status: Annotated[str, Form()],
        file: Annotated[UploadFile, File()],
        name: Annotated[str, Form()],
        description: Annotated[str | None, Form()] = None,
    ) -> None:
        await interactor.execute(
            UpdateClientDocumentRequest(
                document_id=document_id,
                client_id=client_id,
                document_type=document_type,
                status=ClientDocumentStatus(status),
                file=file,
                name=name,
                description=description,
            )
        )

    @router.delete(
        "/client/{client_id}/documents",
        error_map={
            AuthenticationError: status.HTTP_401_UNAUTHORIZED,
            ReaderError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
        },
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def delete_document(
        interactor: FromDishka[DeleteClientDocument], request: DeleteClientDocumentRequest
    ) -> None:
        await interactor.execute(request)

    return router
