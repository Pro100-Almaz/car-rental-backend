import logging
from typing import Any
from uuid import UUID

from app.core.commands.ports.client_tx_storage import ClientTxStorage
from app.core.commands.ports.device_token_tx_storage import DeviceTokenTxStorage
from app.core.commands.ports.flusher import Flusher
from app.core.commands.ports.notification_tx_storage import NotificationTxStorage
from app.core.commands.ports.transaction_manager import TransactionManager
from app.core.commands.ports.user_tx_storage import UserTxStorage
from app.core.commands.ports.utc_timer import UtcTimer
from app.core.common.entities.notification import Notification
from app.core.common.entities.types_ import (
    ClientId,
    NotificationType,
    OrganizationId,
    UserId,
)
from app.core.common.factories.id_factory import create_notification_id
from app.core.common.ports.push_sender import PushSender
from app.core.common.value_objects.utc_datetime import UtcDatetime

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(
        self,
        utc_timer: UtcTimer,
        notification_tx_storage: NotificationTxStorage,
        device_token_tx_storage: DeviceTokenTxStorage,
        user_tx_storage: UserTxStorage,
        client_tx_storage: ClientTxStorage,
        push_sender: PushSender,
        flusher: Flusher,
        transaction_manager: TransactionManager,
    ) -> None:
        self._utc_timer = utc_timer
        self._notification_tx_storage = notification_tx_storage
        self._device_token_tx_storage = device_token_tx_storage
        self._user_tx_storage = user_tx_storage
        self._client_tx_storage = client_tx_storage
        self._push_sender = push_sender
        self._flusher = flusher
        self._transaction_manager = transaction_manager

    async def send_to_client(
        self,
        *,
        client_id: UUID,
        organization_id: UUID,
        type_: NotificationType,
        title: str,
        body: str,
        deep_link: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Dispatch a notification to the user account linked to a client, or skip silently.

        `notifications.user_id` FKs to `users.id`, but rental code holds `clients.id`. Clients may
        or may not have a paired user account (`clients.user_id` is nullable). When absent, we
        skip — no in-app notification possible, no FK violation either.
        """
        client = await self._client_tx_storage.get_by_id(ClientId(client_id))
        if client is None:
            logger.info("Notification skipped: client %s not found.", client_id)
            return
        if client.user_id is None:
            logger.info(
                "Notification skipped: client %s has no paired user account.",
                client_id,
            )
            return
        await self.send(
            user_id=client.user_id,
            organization_id=organization_id,
            type_=type_,
            title=title,
            body=body,
            deep_link=deep_link,
            metadata=metadata,
        )

    async def send(
        self,
        *,
        user_id: UUID,
        organization_id: UUID,
        type_: NotificationType,
        title: str,
        body: str,
        deep_link: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        user = await self._user_tx_storage.get_by_id(UserId(user_id))
        if user is not None and user.notification_preferences:
            prefs = user.notification_preferences
            if prefs.get(type_.value) is False:
                logger.info("Notification type %s muted for user %s, skipping.", type_, user_id)
                return

        now = UtcDatetime(self._utc_timer.now.value)
        notification = Notification(
            id_=create_notification_id(),
            user_id=UserId(user_id),
            organization_id=OrganizationId(organization_id),
            type_=type_,
            title=title,
            body=body,
            deep_link=deep_link,
            metadata=metadata or {},
            is_read=False,
            read_at=None,
            created_at=now,
        )
        self._notification_tx_storage.add(notification)
        await self._flusher.flush()
        await self._transaction_manager.commit()

        try:
            tokens = await self._device_token_tx_storage.get_all_for_user(UserId(user_id))
            push_data = {"type": type_.value}
            if deep_link:
                push_data["deep_link"] = deep_link
            for token in tokens:
                await self._push_sender.send(
                    device_token=token.token,
                    title=title,
                    body=body,
                    data=push_data,
                )
        except Exception:
            logger.exception("Failed to dispatch push notification for user %s", user_id)
