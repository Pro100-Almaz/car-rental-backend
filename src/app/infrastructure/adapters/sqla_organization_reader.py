from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.queries.models.organization import OrganizationQm
from app.core.queries.ports.organization_reader import ListOrganizationsQm, OrganizationReader
from app.core.queries.query_support.exceptions import SortingError
from app.core.queries.query_support.offset_pagination import OffsetPaginationParams
from app.core.queries.query_support.sorting import SortingOrder, SortingParams
from app.infrastructure.exceptions import ReaderError
from app.infrastructure.persistence_sqla.mappings.organization import organizations_table


class SqlaOrganizationReader(OrganizationReader):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_organizations(
        self,
        *,
        pagination: OffsetPaginationParams,
        sorting: SortingParams,
    ) -> ListOrganizationsQm:
        sorting_column = organizations_table.c.get(sorting.field)
        if sorting_column is None:
            raise SortingError(f"Invalid sorting field: '{sorting.field}'")
        order_by_expression = sorting_column.asc() if sorting.order == SortingOrder.ASC else sorting_column.desc()
        secondary_order_by = (
            organizations_table.c.id.asc() if sorting.order == SortingOrder.ASC else organizations_table.c.id.desc()
        )
        stmt = (
            select(
                organizations_table.c.id,
                organizations_table.c.name,
                organizations_table.c.slug,
                organizations_table.c.settings,
                organizations_table.c.subscription_plan,
                organizations_table.c.created_at,
                organizations_table.c.updated_at,
                func.count().over().label("total"),
            )
            .order_by(order_by_expression, secondary_order_by)
            .limit(pagination.limit)
            .offset(pagination.offset)
        )
        try:
            result = await self._session.execute(stmt)
            rows = result.all()
        except SQLAlchemyError as e:
            raise ReaderError from e
        if not rows:
            total_stmt = select(func.count()).select_from(organizations_table)
            try:
                total = int(await self._session.scalar(total_stmt) or 0)
            except SQLAlchemyError as e:
                raise ReaderError from e
            return ListOrganizationsQm(
                organizations=[],
                total=total,
                limit=pagination.limit,
                offset=pagination.offset,
            )
        organizations = [
            OrganizationQm(
                id=row.id,
                name=row.name,
                slug=row.slug,
                settings=row.settings,
                subscription_plan=row.subscription_plan,
                created_at=row.created_at,
                updated_at=row.updated_at,
            )
            for row in rows
        ]
        return ListOrganizationsQm(
            organizations=organizations,
            total=rows[0].total,
            limit=pagination.limit,
            offset=pagination.offset,
        )
