"""Runner test — orchestration end-to-end with downloads monkeypatched to fixtures."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from strata_api.pipeline.air import runner as air_runner

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures" / "air"
SAMPLE_CSV = FIXTURES / "ugz_air_sample.csv"
STATIONS_JSON = FIXTURES / "ugz_air_stations.json"


@pytest.fixture
def patched_downloads(monkeypatch):
    monkeypatch.setattr(air_runner, "download_air_csv", lambda year=None: SAMPLE_CSV.read_text(encoding="utf-8"))
    monkeypatch.setattr(air_runner, "download_stations_json", lambda: STATIONS_JSON.read_text(encoding="utf-8"))


def test_run_writes_geojson_and_returns_stats(patched_downloads, tmp_path):
    stats = air_runner.run_air_pipeline(tmp_path, year=2026)

    output = tmp_path / "air_quality.geojson"
    assert output.exists()

    geojson = json.loads(output.read_text(encoding="utf-8"))
    assert geojson["type"] == "FeatureCollection"
    assert len(geojson["features"]) == 4

    assert stats["stations"] == 4
    assert stats["features"] == 4
    assert stats["measurements"] > 0
    assert sum(stats["levels"].values()) == 4


def test_run_creates_output_dir(patched_downloads, tmp_path):
    nested = tmp_path / "deep" / "data"
    air_runner.run_air_pipeline(nested, year=2026)
    assert (nested / "air_quality.geojson").exists()
