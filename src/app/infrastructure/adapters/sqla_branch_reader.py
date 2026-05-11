from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.queries.models.branch import BranchQm
from app.core.queries.ports.branch_reader import BranchReader, ListBranchesQm
from app.infrastructure.exceptions import ReaderError
from app.infrastructure.persistence_sqla.mappings.branch import branches_table


class SqlaBranchReader(BranchReader):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_branches(
        self,
        *,
        organization_id: UUID,
    ) -> ListBranchesQm:
        stmt = (
            select(
                branches_table.c.id,
                branches_table.c.organization_id,
                branches_table.c.name,
                branches_table.c.address,
                branches_table.c.latitude,
                branches_table.c.longitude,
                branches_table.c.timezone,
                branches_table.c.created_at,
            )
            .where(branches_table.c.organization_id == organization_id)
            .order_by(branches_table.c.name.asc())
        )
        try:
            result = await self._session.execute(stmt)
            rows = result.all()
        except SQLAlchemyError as e:
            raise ReaderError from e
        branches = [
            BranchQm(
                id=row.id,
                organization_id=row.organization_id,
                name=row.name,
                address=row.address,
                latitude=row.latitude,
                longitude=row.longitude,
                timezone=row.timezone,
                created_at=row.created_at,
            )
            for row in rows
        ]
        return ListBranchesQm(
            branches=branches,
            total=len(branches),
        )
