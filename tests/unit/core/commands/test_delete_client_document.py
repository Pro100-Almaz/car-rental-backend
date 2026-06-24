from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest

from app.core.commands.delete_client_document import DeleteClientDocument, DeleteClientDocumentRequest


@pytest.mark.asyncio
async def test_delete_client_document_success() -> None:
    client_id = uuid4()
    document_id = uuid4()

    # mocking the client_document objext
    client_document = Mock()
    client_document.client_id = client_id
    client_document.url = "/media/client_documents/national_id/old.png"

    current_user_service = Mock()
    current_user_service.get_current_user = AsyncMock(return_value=object())

    client_document_service = Mock()
    client_document_service.delete_uploaded_file = Mock()

    client_document_tx_storage = Mock()
    client_document_tx_storage.get_by_id = AsyncMock(return_value=client_document)
    client_document_tx_storage.delete = AsyncMock()
    client_document_tx_storage.flush = AsyncMock()

    transaction_manager = Mock()
    transaction_manager.commit = AsyncMock()

    interactor = DeleteClientDocument(
        current_user_service=current_user_service,
        client_document_service=client_document_service,
        client_document_tx_storage=client_document_tx_storage,
        transaction_manager=transaction_manager,
    )

    request = DeleteClientDocumentRequest(document_id=document_id, client_id=client_id)

    with patch("app.core.commands.delete_client_document.authorize") as authorize_mock:
        await interactor.execute(request)

    current_user_service.get_current_user.assert_awaited_once()
    authorize_mock.assert_called_once()

    client_document_tx_storage.get_by_id.assert_awaited_once_with(document_id)

    client_document_tx_storage.delete.assert_awaited_once()

    client_document_tx_storage.flush.assert_awaited_once()
    transaction_manager.commit.assert_awaited_once()

    client_document_service.delete_uploaded_file.assert_called_once_with("/media/client_documents/national_id/old.png")
