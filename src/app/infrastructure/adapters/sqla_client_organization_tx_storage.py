from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.commands.ports.client_organization_tx_storage import ClientOrganizationTxStorage
from app.core.common.entities.client_organization import ClientOrganization
from app.infrastructure.exceptions import StorageError
from app.infrastructure.persistence_sqla.mappings.client_organization import client_organizations_table


class SqlaClientOrganizationTxStorage(ClientOrganizationTxStorage):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def add(self, client_organization: ClientOrganization) -> None:
        try:
            self._session.add(client_organization)
        except SQLAlchemyError as e:
            raise StorageError from e

    async def get_by_client_and_org(
        self,
        *,
        client_id: UUID,
        organization_id: UUID,
    ) -> ClientOrganization | None:
        stmt = select(ClientOrganization).where(
            client_organizations_table.c.client_id == client_id,
            client_organizations_table.c.organization_id == organization_id,
        )
        try:
            result = await self._session.execute(stmt)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            raise StorageError from e

    async def delete(self, client_organization: ClientOrganization) -> None:
        try:
            await self._session.delete(client_organization)
        except SQLAlchemyError as e:
            raise StorageError from e
