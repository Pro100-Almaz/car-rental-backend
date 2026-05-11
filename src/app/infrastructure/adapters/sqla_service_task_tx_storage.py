from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.commands.ports.service_task_tx_storage import ServiceTaskTxStorage
from app.core.common.entities.service_task import ServiceTask
from app.core.common.entities.types_ import ServiceTaskId
from app.infrastructure.exceptions import StorageError


class SqlaServiceTaskTxStorage(ServiceTaskTxStorage):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def add(self, service_task: ServiceTask) -> None:
        try:
            self._session.add(service_task)
        except SQLAlchemyError as e:
            raise StorageError from e

    async def get_by_id(
        self,
        service_task_id: ServiceTaskId,
        *,
        for_update: bool = False,
    ) -> ServiceTask | None:
        try:
            return await self._session.get(
                ServiceTask,
                service_task_id,
                with_for_update=for_update,
            )
        except SQLAlchemyError as e:
            raise StorageError from e
