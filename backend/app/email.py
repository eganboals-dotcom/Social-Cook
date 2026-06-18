"""Outbound email — pluggable behind a small interface.

The default `ConsoleEmailSender` just logs the message (so password reset works
end-to-end in dev without an email provider). Swap in an SMTP/SendGrid/SES sender
for production by changing `get_email_sender`.
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod

logger = logging.getLogger("social_cook.email")


class EmailSender(ABC):
    @abstractmethod
    def send(self, *, to: str, subject: str, body: str) -> None: ...


class ConsoleEmailSender(EmailSender):
    """Dev sender — logs instead of delivering. NOT for production."""

    def send(self, *, to: str, subject: str, body: str) -> None:
        logger.info("EMAIL to=%s subject=%s\n%s", to, subject, body)


def get_email_sender() -> EmailSender:
    # Production: return an SMTP/SendGrid/SES-backed sender keyed off settings.
    return ConsoleEmailSender()
