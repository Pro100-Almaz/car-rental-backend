from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.commands.ports.vehicle_document_tx_storage import VehicleDocumentTxStorage
from app.core.common.entities.vehicle_document import VehicleDocument
from app.infrastructure.exceptions import StorageError


class SqlaVehicleDocumentTxStorage(VehicleDocumentTxStorage):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def add(self, vehicle_document: VehicleDocument) -> None:
        self._session.add(vehicle_document)

    async def get_by_id(self, document_id: UUID) -> VehicleDocument | None:
        try:
            return await self._session.get(VehicleDocument, document_id)
        except SQLAlchemyError as e:
            raise StorageError from e

    async def delete(self, vehicle_document: VehicleDocument) -> None:
        try:
            await self._session.delete(vehicle_document)
        except SQLAlchemyError as e:
            raise StorageError from e
