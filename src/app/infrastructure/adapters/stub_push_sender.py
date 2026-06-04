import logging

logger = logging.getLogger(__name__)


class StubPushSender:
    async def send(
        self,
        *,
        device_token: str,
        title: str,
        body: str,
        data: dict[str, str] | None = None,
    ) -> bool:
        logger.info("STUB push: token=%s title=%s body=%s", device_token, title, body)
        return True
