from datetime import UTC, datetime
from typing import cast
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest

from app.core.commands.create_client_document import CreateClientDocument, CreateClientDocumentRequest
from app.core.common.services.client_document_service import UploadedDocumentFile


@pytest.mark.asyncio
async def test_create_client_document_success() -> None:
    upload_file = cast(UploadedDocumentFile, object())
    current_user_service = Mock()
    current_user_service.get_current_user = AsyncMock(return_value=object())

    client_document_service = Mock()
    client_document_service.save_uploaded_file = AsyncMock(return_value="/media/client_documents/national_id/test.png")
    client_document_service.delete_uploaded_file = Mock()

    client_document_tx_storage = Mock()
    client_document_tx_storage.add = Mock()
    client_document_tx_storage.flush = AsyncMock()

    transaction_manager = Mock()
    transaction_manager.commit = AsyncMock()

    utc_timer = Mock()
    utc_timer.now.value = datetime(2026, 1, 1, tzinfo=UTC)

    interactor = CreateClientDocument(
        current_user_service=current_user_service,
        client_document_service=client_document_service,
        client_document_tx_storage=client_document_tx_storage,
        transaction_manager=transaction_manager,
        utc_timer=utc_timer,
    )

    request = CreateClientDocumentRequest(
        client_id=uuid4(), document_type="national_id", description="national id", file=upload_file
    )

    with patch("app.core.commands.create_client_document.authorize") as authorize_mock:
        document_id = await interactor.execute(request)

    assert document_id is not None

    current_user_service.get_current_user.assert_awaited_once()

    authorize_mock.assert_called_once()

    client_document_tx_storage.add.assert_called_once()

    assert client_document_tx_storage.flush.await_count == 2

    client_document_service.save_uploaded_file.assert_awaited_once_with(
        file=request.file,
        client_id=request.client_id,
        document_id=document_id,
        document_type=request.document_type,
        document_description=request.description,
    )

    transaction_manager.commit.assert_awaited_once()

    client_document_service.delete_uploaded_file.assert_not_called()
