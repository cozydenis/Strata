"""Tests for the admin notification trigger endpoint (POST /admin/pipeline/run-notifications)."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from strata_api.notifications.runner import NotificationSummary

_TEST_API_KEY = "test-secret-key"
_AUTH_HEADERS = {"X-API-Key": _TEST_API_KEY}


@pytest.fixture(autouse=True)
def patch_api_key(monkeypatch):
    import strata_api.routers.admin_pipeline as mod

    monkeypatch.setattr(mod.settings, "pipeline_api_key", _TEST_API_KEY)


@pytest.mark.asyncio
async def test_run_notifications_missing_api_key_returns_401():
    from strata_api.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/admin/pipeline/run-notifications")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_run_notifications_wrong_api_key_returns_401():
    from strata_api.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/admin/pipeline/run-notifications", headers={"X-API-Key": "wrong-key"}
        )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_run_notifications_returns_200_with_summary():
    from strata_api.main import app

    summary = NotificationSummary(users=3, sent=1, skipped_no_events=1, skipped_no_email=1, failed=0)

    fake_sender = object()
    fake_resolver = object()

    with (
        patch("strata_api.routers.admin_pipeline.get_engine", return_value=MagicMock()),
        patch("strata_api.routers.admin_pipeline.build_sender", return_value=fake_sender) as build_sender,
        patch(
            "strata_api.routers.admin_pipeline.build_email_resolver", return_value=fake_resolver
        ) as build_resolver,
        patch(
            "strata_api.routers.admin_pipeline.run_notifications", return_value=summary
        ) as run_notifications,
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/admin/pipeline/run-notifications", headers=_AUTH_HEADERS)

    assert response.status_code == 200
    data = response.json()
    assert data["users"] == 3
    assert data["sent"] == 1
    assert data["skipped_no_events"] == 1
    assert data["skipped_no_email"] == 1
    assert data["failed"] == 0

    # sender + resolver are built from settings and injected into the runner
    build_sender.assert_called_once()
    build_resolver.assert_called_once()
    _, kwargs = run_notifications.call_args
    assert kwargs["sender"] is fake_sender
    assert kwargs["resolve_email"] is fake_resolver
