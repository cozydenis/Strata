"""Resolve a Supabase auth user id to an email via the Admin REST API.

Watches only store the Supabase uid, never the email. The digest runner needs
an address, so we look it up through the Supabase Admin endpoint using the
service-role key. Every failure mode returns None (and logs a warning) so a
single unresolvable user never aborts a notification run.
"""
from __future__ import annotations

import json
import logging
from typing import Protocol
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)

_TIMEOUT_SECONDS = 10


class EmailResolver(Protocol):
    """A callable that maps a Supabase user id to an email, or None."""

    def __call__(self, user_id: str) -> str | None: ...


def resolve_user_email(user_id: str, *, supabase_url: str, service_key: str) -> str | None:
    """GET the admin user record and return its email, or None on any failure."""
    if not supabase_url or not service_key:
        logger.warning("Cannot resolve email for %s: Supabase is not configured.", user_id)
        return None

    url = f"{supabase_url.rstrip('/')}/auth/v1/admin/users/{user_id}"
    request = Request(
        url,
        headers={
            "apikey": service_key,
            "Authorization": f"Bearer {service_key}",
        },
        method="GET",
    )

    try:
        with urlopen(request, timeout=_TIMEOUT_SECONDS) as response:  # noqa: S310 — fixed Supabase URL
            payload = json.loads(response.read())
    except Exception as err:  # noqa: BLE001 — resolution must never raise out
        logger.warning("Failed to resolve email for user %s: %s", user_id, err)
        return None

    email = payload.get("email") if isinstance(payload, dict) else None
    if not email:
        logger.warning("Supabase returned no email for user %s.", user_id)
        return None
    return email


def build_email_resolver(settings) -> EmailResolver:
    """Bind resolve_user_email to the configured Supabase URL + service key."""

    def _resolve(user_id: str) -> str | None:
        return resolve_user_email(
            user_id,
            supabase_url=settings.supabase_url,
            service_key=settings.supabase_service_key,
        )

    return _resolve
