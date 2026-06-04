from typing import Any
from uuid import UUID

from sqlalchemy import Row, func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.queries.models.notification import NotificationQm
from app.core.queries.ports.notification_reader import ListNotificationsQm, NotificationReader
from app.infrastructure.exceptions import ReaderError
from app.infrastructure.persistence_sqla.mappings.notification import notifications_table


class SqlaNotificationReader(NotificationReader):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _base_columns(self) -> tuple[Any, ...]:
        return (
            notifications_table.c.id,
            notifications_table.c.user_id,
            notifications_table.c.organization_id,
            notifications_table.c.type,
            notifications_table.c.title,
            notifications_table.c.body,
            notifications_table.c.deep_link,
            notifications_table.c.metadata,
            notifications_table.c.is_read,
            notifications_table.c.read_at,
            notifications_table.c.created_at,
        )

    def _row_to_qm(self, row: Row[Any]) -> NotificationQm:
        return NotificationQm(
            id=row.id,
            user_id=row.user_id,
            organization_id=row.organization_id,
            type=row.type,
            title=row.title,
            body=row.body,
            deep_link=row.deep_link,
            metadata=row.metadata,
            is_read=row.is_read,
            read_at=row.read_at,
            created_at=row.created_at,
        )

    async def list_by_user(
        self,
        *,
        user_id: UUID,
        limit: int = 20,
        offset: int = 0,
    ) -> ListNotificationsQm:
        stmt = (
            select(*self._base_columns())
            .where(notifications_table.c.user_id == user_id)
            .order_by(notifications_table.c.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        count_stmt = (
            select(func.count())
            .select_from(notifications_table)
            .where(notifications_table.c.user_id == user_id)
        )
        unread_stmt = (
            select(func.count())
            .select_from(notifications_table)
            .where(notifications_table.c.user_id == user_id)
            .where(notifications_table.c.is_read.is_(False))
        )
        try:
            result = await self._session.execute(stmt)
            rows = result.all()
            total = (await self._session.execute(count_stmt)).scalar_one()
            unread_count = (await self._session.execute(unread_stmt)).scalar_one()
        except SQLAlchemyError as e:
            raise ReaderError from e

        return ListNotificationsQm(
            notifications=[self._row_to_qm(row) for row in rows],
            total=total,
            unread_count=unread_count,
        )
