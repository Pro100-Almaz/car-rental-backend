from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, status
from fastapi_error_map import ErrorAwareRouter

from app.core.common.exceptions import ClientNotFoundError
from app.core.queries.get_my_documents import GetMyDocuments
from app.core.queries.models.client_documents import GetClientDocumentsQm
from app.infrastructure.auth_ctx.exceptions import AuthenticationError
from app.infrastructure.exceptions import ReaderError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE


def make_client_me_document_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.get(
        "/clients/me/documents",
        error_map={
            AuthenticationError: status.HTTP_401_UNAUTHORIZED,
            ReaderError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
        },
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def get_documents(interactor: FromDishka[GetMyDocuments]) -> GetClientDocumentsQm:
        result = await interactor.execute()
        if result is None:
            raise ClientNotFoundError
        return result

    return router
