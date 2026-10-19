import logging
import smtplib
from email.message import EmailMessage

from fastapi.concurrency import run_in_threadpool

from app.core.config import settings

logger = logging.getLogger(__name__)


def _send_sync(to: str, subject: str, body: str) -> None:
    msg = EmailMessage()
    msg["From"] = settings.SMTP_FROM
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as smtp:
        if settings.SMTP_USE_TLS:
            smtp.starttls()
        if settings.SMTP_USER:
            smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        smtp.send_message(msg)


class EmailService:
    @staticmethod
    async def send(to: str, subject: str, body: str) -> None:
        if not settings.SMTP_HOST:
            if settings.DEBUG:
                logger.warning("SMTP not configured; email to %s:\n%s\n%s", to, subject, body)
            else:
                logger.error("SMTP not configured; could not send %r to %s", subject, to)
            return

        try:
            await run_in_threadpool(_send_sync, to, subject, body)
        except (smtplib.SMTPException, OSError):
            logger.exception("Failed to send %r to %s", subject, to)
