"""TDD tests for email senders — written BEFORE implementation (RED).

ConsoleSender logs; SmtpSender talks to a mocked smtplib.SMTP (no network);
build_sender picks SMTP when smtp_host is configured, else Console.
"""
from __future__ import annotations

import logging
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from strata_api.notifications.emailer import (
    ConsoleSender,
    SmtpSender,
    build_sender,
)


def _settings(**overrides) -> SimpleNamespace:
    base = {
        "smtp_host": "",
        "smtp_port": 587,
        "smtp_user": "",
        "smtp_password": "",
        "mail_from": "Strata <no-reply@strata.test>",
    }
    base.update(overrides)
    return SimpleNamespace(**base)


def test_console_sender_logs_email(caplog):
    sender = ConsoleSender()
    with caplog.at_level(logging.INFO):
        sender.send("watcher@example.com", "Subject here", "Body here")
    joined = caplog.text
    assert "watcher@example.com" in joined
    assert "Subject here" in joined


def test_build_sender_returns_console_without_smtp_host():
    sender = build_sender(_settings(smtp_host=""))
    assert isinstance(sender, ConsoleSender)


def test_build_sender_returns_smtp_when_host_set():
    sender = build_sender(_settings(smtp_host="smtp.example.com", smtp_user="u", smtp_password="p"))
    assert isinstance(sender, SmtpSender)


def test_smtp_sender_uses_starttls_login_and_send_message():
    sender = SmtpSender(
        host="smtp.example.com",
        port=587,
        user="user@example.com",
        password="secret",
        mail_from="Strata <no-reply@strata.test>",
    )

    smtp_instance = MagicMock()
    smtp_cm = MagicMock()
    smtp_cm.__enter__.return_value = smtp_instance
    smtp_cm.__exit__.return_value = False

    with patch("strata_api.notifications.emailer.smtplib.SMTP", return_value=smtp_cm) as smtp_cls:
        sender.send("watcher@example.com", "Hello", "World")

    smtp_cls.assert_called_once_with("smtp.example.com", 587)
    smtp_instance.starttls.assert_called_once()
    smtp_instance.login.assert_called_once_with("user@example.com", "secret")
    smtp_instance.send_message.assert_called_once()
    sent = smtp_instance.send_message.call_args.args[0]
    assert sent["To"] == "watcher@example.com"
    assert sent["Subject"] == "Hello"
    assert sent["From"] == "Strata <no-reply@strata.test>"
    assert sent.get_content().strip() == "World"


def test_smtp_sender_skips_login_without_credentials():
    sender = SmtpSender(
        host="smtp.example.com", port=25, user="", password="", mail_from="a@b.test"
    )
    smtp_instance = MagicMock()
    smtp_cm = MagicMock()
    smtp_cm.__enter__.return_value = smtp_instance
    smtp_cm.__exit__.return_value = False

    with patch("strata_api.notifications.emailer.smtplib.SMTP", return_value=smtp_cm):
        sender.send("to@example.com", "s", "b")

    smtp_instance.login.assert_not_called()
    smtp_instance.send_message.assert_called_once()
