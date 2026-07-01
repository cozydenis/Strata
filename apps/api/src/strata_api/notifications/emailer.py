"""Email senders — how a rendered digest actually leaves the building.

`ConsoleSender` is the zero-config default: it logs the email at INFO so local
and unconfigured deployments still exercise the full pipeline. `SmtpSender`
delivers over stdlib smtplib with STARTTLS. `build_sender` chooses between them
based on whether an SMTP host is configured.
"""
from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage
from typing import Protocol

logger = logging.getLogger(__name__)


class EmailSender(Protocol):
    """Anything that can deliver a plain-text email."""

    def send(self, to: str, subject: str, body: str) -> None: ...


class ConsoleSender:
    """Logs the email at INFO instead of sending it — the default sender."""

    def send(self, to: str, subject: str, body: str) -> None:
        logger.info(
            "Email (console) to=%s subject=%r\n%s",
            to,
            subject,
            body,
        )


class SmtpSender:
    """Sends via SMTP with STARTTLS. Login is skipped when no user is set."""

    def __init__(self, host: str, port: int, user: str, password: str, mail_from: str) -> None:
        self._host = host
        self._port = port
        self._user = user
        self._password = password
        self._mail_from = mail_from

    def send(self, to: str, subject: str, body: str) -> None:
        message = EmailMessage()
        message["From"] = self._mail_from
        message["To"] = to
        message["Subject"] = subject
        message.set_content(body)

        with smtplib.SMTP(self._host, self._port) as smtp:
            smtp.starttls()
            if self._user:
                smtp.login(self._user, self._password)
            smtp.send_message(message)


def build_sender(settings) -> EmailSender:
    """SmtpSender when smtp_host is configured, otherwise ConsoleSender."""
    if getattr(settings, "smtp_host", ""):
        return SmtpSender(
            host=settings.smtp_host,
            port=settings.smtp_port,
            user=settings.smtp_user,
            password=settings.smtp_password,
            mail_from=settings.mail_from,
        )
    return ConsoleSender()
