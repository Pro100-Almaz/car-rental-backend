from typing import Any
from uuid import UUID

from sqlalchemy import Row, or_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.queries.models.client import ClientQm
from app.core.queries.ports.client_reader import ClientReader, ListClientsQm
from app.infrastructure.exceptions import ReaderError
from app.infrastructure.persistence_sqla.mappings.client import clients_table
from app.infrastructure.persistence_sqla.mappings.user import users_table


class SqlaClientReader(ClientReader):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _base_columns(self) -> tuple[Any, ...]:
        return (
            clients_table.c.id,
            clients_table.c.organization_id,
            clients_table.c.user_id,
            clients_table.c.phone,
            clients_table.c.email,
            clients_table.c.first_name,
            clients_table.c.last_name,
            clients_table.c.id_document_url,
            clients_table.c.license_front_url,
            clients_table.c.license_back_url,
            clients_table.c.verification_status,
            clients_table.c.trust_score,
            clients_table.c.trust_level,
            clients_table.c.is_blacklisted,
            clients_table.c.blacklist_reason,
            clients_table.c.wallet_balance,
            clients_table.c.debt_balance,
            clients_table.c.registration_source,
            clients_table.c.rejection_reason,
            clients_table.c.metadata,
            users_table.c.email_verified,
            clients_table.c.created_at,
            clients_table.c.updated_at,
        )

    def _base_query(self) -> Any:
        return select(*self._base_columns()).join(
            users_table,
            clients_table.c.user_id == users_table.c.id,
            isouter=True,
        )

    def _row_to_qm(self, row: Row[Any]) -> ClientQm:
        return ClientQm(
            id=row.id,
            organization_id=row.organization_id,
            user_id=row.user_id,
            phone=row.phone,
            email=row.email,
            first_name=row.first_name,
            last_name=row.last_name,
            id_document_url=row.id_document_url,
            license_front_url=row.license_front_url,
            license_back_url=row.license_back_url,
            verification_status=row.verification_status,
            trust_score=row.trust_score,
            trust_level=row.trust_level,
            is_blacklisted=row.is_blacklisted,
            blacklist_reason=row.blacklist_reason,
            wallet_balance=row.wallet_balance,
            debt_balance=row.debt_balance,
            registration_source=row.registration_source,
            rejection_reason=row.rejection_reason,
            metadata=row.metadata,
            email_verified=row.email_verified if row.email_verified is not None else False,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    async def get_by_id(
        self,
        *,
        client_id: UUID,
    ) -> ClientQm | None:
        stmt = self._base_query().where(
            clients_table.c.id == client_id,
        )
        try:
            result = await self._session.execute(stmt)
            row = result.one_or_none()
        except SQLAlchemyError as e:
            raise ReaderError from e
        if row is None:
            return None
        return self._row_to_qm(row)

    async def get_by_user_id(
        self,
        *,
        user_id: UUID,
    ) -> ClientQm | None:
        stmt = self._base_query().where(
            clients_table.c.user_id == user_id,
        )
        try:
            result = await self._session.execute(stmt)
            row = result.one_or_none()
        except SQLAlchemyError as e:
            raise ReaderError from e
        if row is None:
            return None
        return self._row_to_qm(row)

    async def list_clients(
        self,
        *,
        organization_id: UUID,
        verification_status: str | None = None,
        is_blacklisted: bool | None = None,
        search: str | None = None,
    ) -> ListClientsQm:
        stmt = (
            self._base_query()
            .where(clients_table.c.organization_id == organization_id)
            .order_by(clients_table.c.created_at.desc())
        )
        if verification_status is not None:
            stmt = stmt.where(clients_table.c.verification_status == verification_status)
        if is_blacklisted is not None:
            stmt = stmt.where(clients_table.c.is_blacklisted == is_blacklisted)
        if search is not None:
            pattern = f"%{search}%"
            stmt = stmt.where(
                or_(
                    clients_table.c.first_name.ilike(pattern),
                    clients_table.c.last_name.ilike(pattern),
                    clients_table.c.phone.ilike(pattern),
                    clients_table.c.email.ilike(pattern),
                )
            )
        try:
            result = await self._session.execute(stmt)
            rows = result.all()
        except SQLAlchemyError as e:
            raise ReaderError from e
        clients = [self._row_to_qm(row) for row in rows]
        return ListClientsQm(
            clients=clients,
            total=len(clients),
        )
