from datetime import UTC, datetime
from typing import cast
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest

from app.core.commands.update_client_document import UpdateClientDocument, UpdateClientDocumentRequest
from app.core.common.entities.types_ import ClientDocumentStatus
from app.core.common.services.client_document_service import UploadedDocumentFile
from app.core.common.value_objects.utc_datetime import UtcDatetime


@pytest.mark.asyncio
async def test_update_client_document_success() -> None:
    client_id = uuid4()
    document_id = uuid4()
    upload_file = cast(UploadedDocumentFile, object())

    # mocking the client_document objext
    client_document = Mock()
    client_document.client_id = client_id
    client_document.url = "/media/client_documents/national_id/old.png"
    client_document.update_file_url = Mock()
    client_document.update_metadata = Mock()

    current_user_service = Mock()
    current_user_service.get_current_user = AsyncMock(return_value=object())

    client_document_service = Mock()
    client_document_service.save_uploaded_file = AsyncMock(return_value="/media/client_documents/national_id/new.png")
    client_document_service.delete_uploaded_file = Mock()

    client_document_tx_storage = Mock()
    client_document_tx_storage.get_by_id = AsyncMock(return_value=client_document)
    client_document_tx_storage.flush = AsyncMock()

    transaction_manager = Mock()
    transaction_manager.commit = AsyncMock()

    utc_timer = Mock()
    utc_timer.now.value = datetime(2026, 1, 1, tzinfo=UTC)

    interactor = UpdateClientDocument(
        current_user_service=current_user_service,
        client_document_service=client_document_service,
        client_document_tx_storage=client_document_tx_storage,
        transaction_manager=transaction_manager,
        utc_timer=utc_timer,
    )

    request = UpdateClientDocumentRequest(
        document_id=document_id,
        client_id=client_id,
        document_type="national_id",
        status=ClientDocumentStatus.Valid,
        file=upload_file,
        name="test_update",
        description="national id",
    )

    with patch("app.core.commands.update_client_document.authorize") as authorize_mock:
        await interactor.execute(request)

    current_user_service.get_current_user.assert_awaited_once()
    authorize_mock.assert_called_once()

    client_document_tx_storage.get_by_id.assert_awaited_once_with(document_id)

    client_document_service.save_uploaded_file.assert_awaited_once_with(
        file=request.file,
        client_id=request.client_id,
        document_id=request.document_id,
        document_type=request.document_type,
        document_description=request.description,
    )

    client_document.update_file_url.assert_called_once()

    client_document.update_metadata.assert_called_once_with(
        name=request.name,
        status=request.status,
        updated_at=UtcDatetime(datetime(2026, 1, 1, tzinfo=UTC)),
        description=request.description,
    )

    client_document_tx_storage.flush.assert_awaited_once()
    transaction_manager.commit.assert_awaited_once()

    client_document_service.delete_uploaded_file.assert_called_once_with("/media/client_documents/national_id/old.png")
