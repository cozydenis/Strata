"""Tests for the admin pipeline trigger endpoints."""
from unittest.mock import MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from strata_api.pipeline.runner import PipelineResult

_TEST_API_KEY = "test-secret-key"
_AUTH_HEADERS = {"X-API-Key": _TEST_API_KEY}


@pytest.fixture(autouse=True)
def patch_api_key(monkeypatch):
    """Set pipeline_api_key for all tests in this module."""
    import strata_api.routers.admin_pipeline as mod
    monkeypatch.setattr(mod.settings, "pipeline_api_key", _TEST_API_KEY)


@pytest.fixture
def mock_stadt_result() -> PipelineResult:
    return PipelineResult(
        run_id=1,
        run_type="stadt",
        status="completed",
        buildings_upserted=100,
        entrances_upserted=80,
        units_upserted=200,
    )


@pytest.fixture
def mock_kanton_result() -> PipelineResult:
    return PipelineResult(
        run_id=2,
        run_type="kanton",
        status="completed",
        buildings_upserted=500,
        entrances_upserted=400,
        units_upserted=1000,
    )


@pytest.fixture
def mock_failed_result() -> PipelineResult:
    return PipelineResult(
        run_id=3,
        run_type="stadt",
        status="failed",
        error_message="network error",
    )


@pytest.mark.asyncio
async def test_trigger_stadt_pipeline_returns_result(mock_stadt_result):
    from strata_api.main import app

    with patch("strata_api.routers.admin_pipeline.run_stadt_pipeline", return_value=mock_stadt_result), \
         patch("strata_api.routers.admin_pipeline.get_engine", return_value=MagicMock()):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/admin/pipeline/run/stadt", headers=_AUTH_HEADERS)

    assert response.status_code == 200
    data = response.json()
    assert data["run_id"] == 1
    assert data["run_type"] == "stadt"
    assert data["status"] == "completed"
    assert data["buildings_upserted"] == 100
    assert data["entrances_upserted"] == 80
    assert data["units_upserted"] == 200
    assert data["error_message"] is None


@pytest.mark.asyncio
async def test_trigger_kanton_pipeline_returns_result(mock_kanton_result):
    from strata_api.main import app

    with patch("strata_api.routers.admin_pipeline.run_kanton_pipeline", return_value=mock_kanton_result), \
         patch("strata_api.routers.admin_pipeline.get_engine", return_value=MagicMock()):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/admin/pipeline/run/kanton", headers=_AUTH_HEADERS)

    assert response.status_code == 200
    data = response.json()
    assert data["run_id"] == 2
    assert data["run_type"] == "kanton"
    assert data["status"] == "completed"
    assert data["buildings_upserted"] == 500


@pytest.mark.asyncio
async def test_trigger_stadt_pipeline_failed_run_returns_200(mock_failed_result):
    """A failed pipeline run is still a successful API call — result contains error info."""
    from strata_api.main import app

    with patch("strata_api.routers.admin_pipeline.run_stadt_pipeline", return_value=mock_failed_result), \
         patch("strata_api.routers.admin_pipeline.get_engine", return_value=MagicMock()):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/admin/pipeline/run/stadt", headers=_AUTH_HEADERS)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "failed"
    assert data["error_message"] == "network error"
    assert data["buildings_upserted"] == 0


@pytest.mark.asyncio
async def test_trigger_unknown_pipeline_returns_404():
    from strata_api.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/admin/pipeline/run/unknown_source", headers=_AUTH_HEADERS)

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_missing_api_key_returns_401():
    from strata_api.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/admin/pipeline/run/stadt")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_wrong_api_key_returns_401():
    from strata_api.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/admin/pipeline/run/stadt", headers={"X-API-Key": "wrong-key"})

    assert response.status_code == 401


# ── /run-listings endpoint ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_run_listings_missing_api_key_returns_401():
    from strata_api.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/admin/pipeline/run-listings")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_run_listings_wrong_api_key_returns_401():
    from strata_api.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/admin/pipeline/run-listings", headers={"X-API-Key": "wrong-key"})

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_run_listings_returns_202_immediately():
    """202 Accepted returned immediately; pipeline runs in background thread."""
    from strata_api.main import app

    async def _fake_pipeline(db):
        return {"flatfox": {"inserted": 5, "updated": 2}}

    with patch("strata_api.pipeline.listing_runner.run_listing_pipeline", new=_fake_pipeline), \
         patch("strata_api.routers.admin_pipeline.get_engine", return_value=MagicMock()):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/admin/pipeline/run-listings", headers=_AUTH_HEADERS)

    assert response.status_code == 202
    assert response.json()["status"] == "accepted"


@pytest.mark.asyncio
async def test_run_listings_pipeline_exception_still_returns_202():
    """Even when pipeline raises, endpoint returns 202 (errors are logged, not surfaced)."""
    from strata_api.main import app

    async def _failing_pipeline(db):
        raise RuntimeError("connection timeout")

    with patch("strata_api.pipeline.listing_runner.run_listing_pipeline", new=_failing_pipeline), \
         patch("strata_api.routers.admin_pipeline.get_engine", return_value=MagicMock()):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/admin/pipeline/run-listings", headers=_AUTH_HEADERS)

    assert response.status_code == 202
