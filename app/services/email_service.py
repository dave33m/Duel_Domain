"""Transactional email: fastapi-mail over Resend's SMTP relay, rendered from Jinja templates.

Emails are queued as background tasks so API responses don't wait on the mail server,
and so a request's timing doesn't reveal whether an email was actually sent.
"""
import asyncio
import logging
from functools import lru_cache
from pathlib import Path

from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType

from app.core.config import settings
from app.models.user import User

logger = logging.getLogger(__name__)

TEMPLATE_DIR = Path(__file__).resolve().parents[1] / "templates" / "email"

# Strong references to in-flight sends; asyncio only keeps weak ones.
_pending: set[asyncio.Task] = set()


def build_mail_client(suppress_send: bool = False) -> FastMail:
    return FastMail(
        ConnectionConfig(
            MAIL_USERNAME="resend",
            MAIL_PASSWORD=settings.RESEND_API_KEY or "unset",
            MAIL_SERVER=settings.MAIL_SERVER,
            MAIL_PORT=settings.MAIL_PORT,
            # Resend: 465/2465 are implicit TLS; 25/587/2587 upgrade with STARTTLS.
            MAIL_STARTTLS=settings.MAIL_PORT not in (465, 2465),
            MAIL_SSL_TLS=settings.MAIL_PORT in (465, 2465),
            MAIL_FROM=settings.MAIL_FROM,
            MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
            TEMPLATE_FOLDER=TEMPLATE_DIR,
            SUPPRESS_SEND=int(suppress_send),
            TIMEOUT=15,
        )
    )


@lru_cache
def _client() -> FastMail:
    return build_mail_client()


def _context(**values) -> dict:
    return {
        "frontend_url": settings.FRONTEND_URL,
        "support_email": settings.MAIL_REPLY_TO or settings.MAIL_FROM,
        **values,
    }


class EmailService:
    @staticmethod
    async def send(recipients: list[str], subject: str, template: str, context: dict, client: FastMail | None = None) -> None:
        if client is None and not settings.RESEND_API_KEY:
            logger.warning("RESEND_API_KEY not set; not sending %r to %s", subject, recipients)
            return

        message = MessageSchema(
            recipients=recipients,
            subject=subject,
            template_body=_context(**context),
            subtype=MessageType.html,
            reply_to=[settings.MAIL_REPLY_TO] if settings.MAIL_REPLY_TO else [],
        )
        try:
            await (client or _client()).send_message(message, template_name=template)
        except Exception:
            logger.exception("Failed to send %r to %s", subject, recipients)

    @staticmethod
    def queue(recipients: list[str], subject: str, template: str, context: dict) -> None:
        task = asyncio.create_task(EmailService.send(recipients, subject, template, context))
        _pending.add(task)
        task.add_done_callback(_pending.discard)

    # One method per email the app sends.

    @staticmethod
    def verification_code(user: User, code: str, minutes: int) -> None:
        EmailService.queue([user.email], "Verify your Duel Domain email", "verify_email.html",
                           {"username": user.username, "code": code, "minutes": minutes})

    @staticmethod
    def welcome(user: User) -> None:
        EmailService.queue([user.email], "Welcome to Duel Domain", "welcome.html", {"username": user.username})

    @staticmethod
    def password_reset_code(user: User, code: str, minutes: int) -> None:
        EmailService.queue([user.email], "Your Duel Domain password reset code", "password_reset.html",
                           {"username": user.username, "code": code, "minutes": minutes})

    @staticmethod
    def password_change_code(user: User, code: str, minutes: int) -> None:
        EmailService.queue([user.email], "Confirm your Duel Domain password change", "password_change_code.html",
                           {"username": user.username, "code": code, "minutes": minutes})

    @staticmethod
    def password_changed(user: User) -> None:
        EmailService.queue([user.email], "Your Duel Domain password was changed", "password_changed.html",
                           {"username": user.username})

    @staticmethod
    def new_signup_alert(user: User) -> None:
        recipients = settings.admin_notify_emails_list
        if recipients:
            EmailService.queue(recipients, f"New Duel Domain signup: {user.username}", "admin_new_signup.html",
                               {"username": user.username, "email": user.email, "user_id": str(user.id)})
