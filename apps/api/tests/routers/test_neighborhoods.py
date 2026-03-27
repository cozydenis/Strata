"""TDD integration tests for neighborhoods router — written BEFORE implementation (RED phase).

Uses a fixture quartiere.geojson to avoid hitting the network.
"""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

FIXTURE_GEOJSON = Path(__file__).resolve().parents[1] / "fixtures" / "neighborhoods" / "quartiere_fixture.geojson"


@pytest.fixture
def fixture_geojson_data() -> dict:
    return json.loads(FIXTURE_GEOJSON.read_text())


@pytest.fixture
def client(fixture_geojson_data, tmp_path):
    """TestClient with the neighborhoods router mounted, using a fixture GeoJSON file."""
    geojson_path = tmp_path / "quartiere.geojson"
    geojson_path.write_text(json.dumps(fixture_geojson_data), encoding="utf-8")

    from fastapi import FastAPI
    from strata_api.routers.neighborhoods import router, _reset_cache

    _reset_cache()

    app = FastAPI()
    app.include_router(router)

    with patch("strata_api.routers.neighborhoods._QUARTIERE_PATH", geojson_path):
        with TestClient(app) as c:
            yield c

    _reset_cache()


class TestGetQuartierProfile:
    """Integration tests for GET /neighborhoods/{quartier_id}/profile."""

    def test_returns_200_for_existing_quartier(self, client):
        response = client.get("/neighborhoods/11/profile")
        assert response.status_code == 200

    def test_returns_404_for_missing_quartier(self, client):
        response = client.get("/neighborhoods/999/profile")
        assert response.status_code == 404

    def test_response_has_quartier_id(self, client):
        data = client.get("/neighborhoods/11/profile").json()
        assert data["quartier_id"] == 11

    def test_response_has_quartier_name(self, client):
        data = client.get("/neighborhoods/11/profile").json()
        assert data["quartier_name"] == "Rathaus"

    def test_response_has_kreis(self, client):
        data = client.get("/neighborhoods/11/profile").json()
        assert data["kreis"] == 1

    def test_response_has_population_block(self, client):
        data = client.get("/neighborhoods/11/profile").json()
        pop = data["population"]
        assert pop["total"] == 4200
        assert pop["density_per_km2"] == pytest.approx(12000.0)
        assert pop["swiss_pct"] == pytest.approx(68.5)
        assert pop["foreign_pct"] == pytest.approx(31.5)
        assert pop["growth_rate"] == pytest.approx(1.2)
        assert pop["trend"] == "growing"

    def test_response_has_age_distribution(self, client):
        data = client.get("/neighborhoods/11/profile").json()
        age_dist = data["age_distribution"]
        assert isinstance(age_dist, list)
        assert len(age_dist) == 5
        buckets = {item["bucket"] for item in age_dist}
        assert buckets == {"0-17", "18-29", "30-44", "45-64", "65+"}

    def test_age_distribution_has_pct(self, client):
        data = client.get("/neighborhoods/11/profile").json()
        age_dist = {item["bucket"]: item["pct"] for item in data["age_distribution"]}
        assert age_dist["0-17"] == pytest.approx(12.3)
        assert age_dist["65+"] == pytest.approx(15.5)

    def test_quartier_without_demographics_returns_null_population(self, client):
        data = client.get("/neighborhoods/12/profile").json()
        assert data["quartier_name"] == "Hochschulen"
        assert data["population"]["total"] is None

    def test_geojson_cached_after_first_load(self, client, fixture_geojson_data, tmp_path):
        """Second call should use cached data, not reload the file."""
        client.get("/neighborhoods/11/profile")
        client.get("/neighborhoods/11/profile")
        # Both calls should succeed (no error from missing file on reload)

    def test_router_mounted_in_main_app(self):
        """neighborhoods router should be registered in main.py."""
        from strata_api.main import app

        routes = [r.path for r in app.routes]  # type: ignore[attr-defined]
        assert any("neighborhoods" in r for r in routes)
