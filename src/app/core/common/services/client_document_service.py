import os
from pathlib import Path
from typing import Protocol
from uuid import UUID, uuid4

from anyio import open_file

UPLOAD_ROOT = Path(os.getenv("UPLOAD_ROOT", "/code/uploads"))
MEDIA_URL_PREFIX = "/media"

UPLOAD_DIRS = {
    "national_id": "client_documents/national_id",
    "license_front": "client_documents/license_front",
    "license_back": "client_documents/license_back",
}

ALLOWED_TYPES = {
    "image/jpg": ".jpg",
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}

MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024


class UploadedDocumentFile(Protocol):
    filename: str | None
    content_type: str | None

    async def read(self, size: int = -1) -> bytes: ...


class InvalidClientDocumentTypeError(ValueError):
    pass


class ClientDocumentFileStorageError(Exception):
    pass


class ClientDocumentService:
    async def save_uploaded_file(
        self,
        *,
        file: UploadedDocumentFile,
        client_id: UUID,
        document_id: UUID,
        document_type: str,
        document_description: str | None = None,
    ) -> str:

        if document_type not in UPLOAD_DIRS:
            raise InvalidClientDocumentTypeError("Unsupported document type.")
        if file.content_type not in ALLOWED_TYPES:
            raise ClientDocumentFileStorageError("Unsupported file type.")

        extension = ALLOWED_TYPES[file.content_type]

        relative_dir = Path(UPLOAD_DIRS[document_type])
        target_dir = UPLOAD_ROOT / relative_dir
        target_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{client_id}_{document_id}_{uuid4().hex}{extension}"
        target_path = target_dir / filename

        total_size = 0

        try:
            async with await open_file(target_path, "wb") as f:
                while chunk := await file.read(1024 * 1024):
                    total_size += len(chunk)

                    if total_size > MAX_FILE_SIZE_BYTES:
                        raise InvalidClientDocumentTypeError("File size exceeds the limit.")

                    await f.write(chunk)

        except InvalidClientDocumentTypeError:
            target_path.unlink(missing_ok=True)
            raise

        except Exception as e:
            target_path.unlink(missing_ok=True)
            raise ClientDocumentFileStorageError("Failed to save file.") from e

        relative_file_path = relative_dir / filename

        return f"{MEDIA_URL_PREFIX}/{relative_file_path.as_posix()}"

    def delete_uploaded_file(self, url: str | None) -> None:
        if url is None:
            return

        relative_path = url.removeprefix(f"{MEDIA_URL_PREFIX}/") if url.startswith(f"{MEDIA_URL_PREFIX}/") else url

        file_path = (UPLOAD_ROOT / relative_path).resolve()
        upload_root = UPLOAD_ROOT.resolve()

        if upload_root not in file_path.parents:
            return

        file_path.unlink(missing_ok=True)
