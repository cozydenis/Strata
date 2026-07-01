"""TDD tests for Supabase user-id → email resolution — written BEFORE impl (RED).

urllib is mocked; no network. Any failure (404, network error, malformed JSON,
missing email) yields None and a logged warning — never an exception.
"""
from __future__ import annotations

import io
import json
import logging
import urllib.error
from types import SimpleNamespace
from unittest.mock import patch

from strata_api.notifications.user_emails import (
    build_email_resolver,
    resolve_user_email,
)

_URL = "https://proj.supabase.co"
_KEY = "service-key"
_UID = "11111111-1111-1111-1111-111111111111"


class _FakeResponse:
    def __init__(self, payload: bytes):
        self._payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self) -> bytes:
        return self._payload


def test_resolve_happy_path_parses_email():
    payload = json.dumps({"id": _UID, "email": "watcher@example.com"}).encode()
    with patch("strata_api.notifications.user_emails.urlopen", return_value=_FakeResponse(payload)) as opener:
        email = resolve_user_email(_UID, supabase_url=_URL, service_key=_KEY)
    assert email == "watcher@example.com"
    # request carries the admin URL and both auth headers
    request = opener.call_args.args[0]
    assert request.full_url == f"{_URL}/auth/v1/admin/users/{_UID}"
    assert request.headers["Apikey"] == _KEY
    assert request.headers["Authorization"] == f"Bearer {_KEY}"


def test_resolve_404_returns_none_and_warns(caplog):
    err = urllib.error.HTTPError(url="x", code=404, msg="Not Found", hdrs=None, fp=io.BytesIO(b""))
    with (
        patch("strata_api.notifications.user_emails.urlopen", side_effect=err),
        caplog.at_level(logging.WARNING),
    ):
        email = resolve_user_email(_UID, supabase_url=_URL, service_key=_KEY)
    assert email is None
    assert caplog.records  # a warning was logged


def test_resolve_network_error_returns_none():
    err = urllib.error.URLError("connection refused")
    with patch("strata_api.notifications.user_emails.urlopen", side_effect=err):
        assert resolve_user_email(_UID, supabase_url=_URL, service_key=_KEY) is None


def test_resolve_malformed_json_returns_none():
    with patch("strata_api.notifications.user_emails.urlopen", return_value=_FakeResponse(b"not json")):
        assert resolve_user_email(_UID, supabase_url=_URL, service_key=_KEY) is None


def test_resolve_missing_email_field_returns_none():
    payload = json.dumps({"id": _UID}).encode()
    with patch("strata_api.notifications.user_emails.urlopen", return_value=_FakeResponse(payload)):
        assert resolve_user_email(_UID, supabase_url=_URL, service_key=_KEY) is None


def test_resolve_without_config_returns_none():
    assert resolve_user_email(_UID, supabase_url="", service_key="") is None


def test_build_email_resolver_binds_settings():
    settings = SimpleNamespace(supabase_url=_URL, supabase_service_key=_KEY)
    resolver = build_email_resolver(settings)
    payload = json.dumps({"email": "bound@example.com"}).encode()
    with patch("strata_api.notifications.user_emails.urlopen", return_value=_FakeResponse(payload)):
        assert resolver(_UID) == "bound@example.com"
