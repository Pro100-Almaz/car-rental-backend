from typing import Any
from uuid import UUID

from sqlalchemy import Row, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.queries.models.organization import OrganizationQm
from app.core.queries.ports.client_organization_reader import ClientOrganizationReader, ListClientOrganizationsQm
from app.infrastructure.exceptions import ReaderError
from app.infrastructure.persistence_sqla.mappings.client_organization import client_organizations_table
from app.infrastructure.persistence_sqla.mappings.organization import organizations_table


class SqlaClientOrganizationReader(ClientOrganizationReader):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _row_to_qm(self, row: Row[Any]) -> OrganizationQm:
        return OrganizationQm(
            id=row.id,
            name=row.name,
            slug=row.slug,
            settings=row.settings,
            subscription_plan=row.subscription_plan,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    async def list_by_client_id(
        self,
        *,
        client_id: UUID,
    ) -> ListClientOrganizationsQm:
        stmt = (
            select(
                organizations_table.c.id,
                organizations_table.c.name,
                organizations_table.c.slug,
                organizations_table.c.settings,
                organizations_table.c.subscription_plan,
                organizations_table.c.created_at,
                organizations_table.c.updated_at,
            )
            .join(
                client_organizations_table,
                client_organizations_table.c.organization_id == organizations_table.c.id,
            )
            .where(client_organizations_table.c.client_id == client_id)
            .order_by(client_organizations_table.c.joined_at.desc())
        )
        try:
            result = await self._session.execute(stmt)
            rows = result.all()
        except SQLAlchemyError as e:
            raise ReaderError from e
        orgs = [self._row_to_qm(row) for row in rows]
        return ListClientOrganizationsQm(organizations=orgs, total=len(orgs))

    async def list_organization_ids_for_client(
        self,
        *,
        client_id: UUID,
    ) -> list[UUID]:
        stmt = select(client_organizations_table.c.organization_id).where(
            client_organizations_table.c.client_id == client_id,
        )
        try:
            result = await self._session.execute(stmt)
            return [row[0] for row in result.all()]
        except SQLAlchemyError as e:
            raise ReaderError from e
