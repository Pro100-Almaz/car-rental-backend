from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.commands.ports.organization_tx_storage import OrganizationTxStorage
from app.core.common.entities.organization import Organization
from app.core.common.entities.types_ import OrganizationId
from app.infrastructure.exceptions import StorageError


class SqlaOrganizationTxStorage(OrganizationTxStorage):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def add(self, organization: Organization) -> None:
        try:
            self._session.add(organization)
        except SQLAlchemyError as e:
            raise StorageError from e

    async def get_by_id(
        self,
        organization_id: OrganizationId,
        *,
        for_update: bool = False,
    ) -> Organization | None:
        try:
            return await self._session.get(
                Organization,
                organization_id,
                with_for_update=for_update,
            )
        except SQLAlchemyError as e:
            raise StorageError from e
