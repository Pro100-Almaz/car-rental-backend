from typing import Any
from uuid import UUID

from sqlalchemy import Row, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.queries.models.client import ClientQm
from app.core.queries.ports.client_reader import ClientReader, ListClientsQm
from app.infrastructure.exceptions import ReaderError
from app.infrastructure.persistence_sqla.mappings.client import clients_table


class SqlaClientReader(ClientReader):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _base_columns(self) -> tuple[Any, ...]:
        return (
            clients_table.c.id,
            clients_table.c.organization_id,
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
            clients_table.c.metadata,
            clients_table.c.created_at,
            clients_table.c.updated_at,
        )

    def _row_to_qm(self, row: Row[Any]) -> ClientQm:
        return ClientQm(
            id=row.id,
            organization_id=row.organization_id,
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
            metadata=row.metadata,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    async def get_by_id(
        self,
        *,
        client_id: UUID,
    ) -> ClientQm | None:
        stmt = select(*self._base_columns()).where(
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

    async def list_clients(
        self,
        *,
        organization_id: UUID,
        verification_status: str | None = None,
        is_blacklisted: bool | None = None,
    ) -> ListClientsQm:
        stmt = (
            select(*self._base_columns())
            .where(clients_table.c.organization_id == organization_id)
            .order_by(clients_table.c.created_at.desc())
        )
        if verification_status is not None:
            stmt = stmt.where(clients_table.c.verification_status == verification_status)
        if is_blacklisted is not None:
            stmt = stmt.where(clients_table.c.is_blacklisted == is_blacklisted)
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
