import asyncio
import logging
import smtplib
from email.message import EmailMessage
from functools import partial

from app.core.common.ports.email_sender import EmailSender

logger = logging.getLogger(__name__)


class SmtpEmailSender(EmailSender):
    def __init__(
        self,
        *,
        host: str,
        port: int,
        username: str,
        password: str,
        from_email: str,
        use_tls: bool = True,
    ) -> None:
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._from_email = from_email
        self._use_tls = use_tls

    async def send(self, *, to: str, subject: str, body: str) -> None:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = self._from_email
        msg["To"] = to
        msg.set_content(body)

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, partial(self._send_sync, msg))
        logger.info("Email sent to %s: %s", to, subject)

    def _send_sync(self, msg: EmailMessage) -> None:
        if self._use_tls:
            with smtplib.SMTP_SSL(self._host, self._port) as server:
                server.login(self._username, self._password)
                server.send_message(msg)
        else:
            with smtplib.SMTP(self._host, self._port) as server:
                server.starttls()
                server.login(self._username, self._password)
                server.send_message(msg)
