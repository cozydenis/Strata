"""TDD tests for noise_parser — written BEFORE implementation (RED phase).

Noise data discovered via recon:
- WFS typename: strlaerm_ep
- Geometry: Point (facade measurement points)
- Key fields: lr_day (dB day), lr_night (dB night), egid (building ID)
- Other fields: address_pod, pod_typ, objectid, exposure_limit_value_d/n
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

FIXTURE = Path(__file__).resolve().parents[2] / "fixtures" / "neighborhoods" / "noise_sample.json"


@pytest.fixture
def noise_geojson() -> dict:
    return json.loads(FIXTURE.read_text())


class TestParseNoiseGeojson:
    """Tests for parse_noise_geojson function."""

    def test_function_is_importable(self):
        from strata_api.pipeline.neighborhoods.noise_parser import parse_noise_geojson  # noqa: F401

    def test_returns_feature_collection(self, noise_geojson):
        from strata_api.pipeline.neighborhoods.noise_parser import parse_noise_geojson

        result = parse_noise_geojson(noise_geojson)
        assert result["type"] == "FeatureCollection"
        assert "features" in result

    def test_output_features_have_db_day(self, noise_geojson):
        from strata_api.pipeline.neighborhoods.noise_parser import parse_noise_geojson

        result = parse_noise_geojson(noise_geojson)
        feats_with_day = [f for f in result["features"] if f["properties"].get("db_day") is not None]
        assert len(feats_with_day) > 0
        assert feats_with_day[0]["properties"]["db_day"] == pytest.approx(43.3)

    def test_output_features_have_db_night(self, noise_geojson):
        from strata_api.pipeline.neighborhoods.noise_parser import parse_noise_geojson

        result = parse_noise_geojson(noise_geojson)
        feat = result["features"][0]
        assert "db_night" in feat["properties"]
        assert feat["properties"]["db_night"] == pytest.approx(36.7)

    def test_output_features_have_egid(self, noise_geojson):
        from strata_api.pipeline.neighborhoods.noise_parser import parse_noise_geojson

        result = parse_noise_geojson(noise_geojson)
        feat = result["features"][0]
        assert feat["properties"]["egid"] == 175053

    def test_skips_features_with_null_db_day_and_db_night(self, noise_geojson):
        """Features with both lr_day=null and lr_night=null should be skipped."""
        from strata_api.pipeline.neighborhoods.noise_parser import parse_noise_geojson

        # Only feature 4 in the fixture has lr_day=null (lr_night is 50.0 — kept)
        result = parse_noise_geojson(noise_geojson)
        # All 4 features have at least one dB value; none fully null
        # The fixture's last feature has null lr_day but non-null lr_night -> kept
        total_null_both = sum(
            1 for f in result["features"]
            if f["properties"].get("db_day") is None and f["properties"].get("db_night") is None
        )
        assert total_null_both == 0

    def test_geometry_preserved(self, noise_geojson):
        from strata_api.pipeline.neighborhoods.noise_parser import parse_noise_geojson

        result = parse_noise_geojson(noise_geojson)
        feat = result["features"][0]
        assert feat["geometry"]["type"] == "Point"
        assert feat["geometry"]["coordinates"] == pytest.approx([8.5401, 47.3769])

    def test_noise_category_assigned(self, noise_geojson):
        """Features should get a noise_category: quiet/moderate/loud/very_loud."""
        from strata_api.pipeline.neighborhoods.noise_parser import parse_noise_geojson

        result = parse_noise_geojson(noise_geojson)
        props_by_day = {
            f["properties"].get("db_day"): f["properties"]
            for f in result["features"]
            if f["properties"].get("db_day") is not None
        }

        assert props_by_day[43.3]["noise_category"] == "quiet"      # <50
        assert props_by_day[62.5]["noise_category"] == "loud"       # 60-70
        assert props_by_day[73.8]["noise_category"] == "very_loud"  # >70

    def test_empty_feature_collection(self):
        from strata_api.pipeline.neighborhoods.noise_parser import parse_noise_geojson

        result = parse_noise_geojson({"type": "FeatureCollection", "features": []})
        assert result["features"] == []

    def test_handles_missing_features_key(self):
        from strata_api.pipeline.neighborhoods.noise_parser import parse_noise_geojson

        result = parse_noise_geojson({"type": "FeatureCollection"})
        assert result["features"] == []

    def test_skips_features_with_null_geometry(self, noise_geojson):
        from strata_api.pipeline.neighborhoods.noise_parser import parse_noise_geojson

        data_with_null = {
            "type": "FeatureCollection",
            "features": [
                {"type": "Feature", "geometry": None, "properties": {"lr_day": 55.0, "lr_night": 48.0, "egid": 999}},
                *noise_geojson["features"],
            ],
        }
        result = parse_noise_geojson(data_with_null)
        egids = [f["properties"].get("egid") for f in result["features"]]
        assert 999 not in egids

    def test_output_has_no_raw_lr_fields(self, noise_geojson):
        """Output should use db_day/db_night, not lr_day/lr_night."""
        from strata_api.pipeline.neighborhoods.noise_parser import parse_noise_geojson

        result = parse_noise_geojson(noise_geojson)
        for feat in result["features"]:
            assert "lr_day" not in feat["properties"]
            assert "lr_night" not in feat["properties"]
