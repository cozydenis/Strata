"""TDD tests for quartier_parser — written BEFORE implementation (RED phase)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

FIXTURE = Path(__file__).resolve().parents[2] / "fixtures" / "neighborhoods" / "quartier_sample.json"


@pytest.fixture
def geojson_data() -> dict:
    return json.loads(FIXTURE.read_text())


class TestQuartierRecord:
    """Unit tests for the QuartierRecord model."""

    def test_record_is_importable(self):
        from strata_api.pipeline.neighborhoods.quartier_parser import QuartierRecord  # noqa: F401

    def test_record_has_required_fields(self):
        from strata_api.pipeline.neighborhoods.quartier_parser import QuartierRecord

        rec = QuartierRecord(
            quartier_id=11,
            quartier_name="Rathaus",
            kreis=1,
            area_km2=None,
            geometry={"type": "Polygon", "coordinates": [[]]},
        )
        assert rec.quartier_id == 11
        assert rec.quartier_name == "Rathaus"
        assert rec.kreis == 1
        assert rec.area_km2 is None
        assert rec.geometry["type"] == "Polygon"

    def test_record_is_frozen(self):
        """QuartierRecord must be immutable."""
        from strata_api.pipeline.neighborhoods.quartier_parser import QuartierRecord

        rec = QuartierRecord(
            quartier_id=11,
            quartier_name="Rathaus",
            kreis=1,
            area_km2=1.23,
            geometry={"type": "Polygon", "coordinates": [[]]},
        )
        with pytest.raises(Exception):
            rec.quartier_id = 99  # type: ignore[misc]

    def test_record_area_km2_accepts_float(self):
        from strata_api.pipeline.neighborhoods.quartier_parser import QuartierRecord

        rec = QuartierRecord(
            quartier_id=73,
            quartier_name="Hirslanden",
            kreis=7,
            area_km2=2.85,
            geometry={"type": "Polygon", "coordinates": [[]]},
        )
        assert rec.area_km2 == pytest.approx(2.85)


class TestParseQuartierGeojson:
    """Unit tests for parse_quartier_geojson function."""

    def test_function_is_importable(self):
        from strata_api.pipeline.neighborhoods.quartier_parser import parse_quartier_geojson  # noqa: F401

    def test_returns_dict_keyed_by_quartier_id(self, geojson_data):
        from strata_api.pipeline.neighborhoods.quartier_parser import parse_quartier_geojson

        result = parse_quartier_geojson(geojson_data)
        assert isinstance(result, dict)
        assert 11 in result
        assert 12 in result
        assert 73 in result

    def test_parses_correct_field_values(self, geojson_data):
        from strata_api.pipeline.neighborhoods.quartier_parser import parse_quartier_geojson

        result = parse_quartier_geojson(geojson_data)
        rec = result[11]
        assert rec.quartier_id == 11
        assert rec.quartier_name == "Rathaus"
        assert rec.kreis == 1

    def test_parses_quartier_73_hirslanden(self, geojson_data):
        from strata_api.pipeline.neighborhoods.quartier_parser import parse_quartier_geojson

        result = parse_quartier_geojson(geojson_data)
        rec = result[73]
        assert rec.quartier_name == "Hirslanden"
        assert rec.kreis == 7

    def test_preserves_geometry(self, geojson_data):
        from strata_api.pipeline.neighborhoods.quartier_parser import parse_quartier_geojson

        result = parse_quartier_geojson(geojson_data)
        geom = result[11].geometry
        assert geom["type"] == "Polygon"
        assert len(geom["coordinates"]) > 0

    def test_all_three_features_parsed(self, geojson_data):
        from strata_api.pipeline.neighborhoods.quartier_parser import parse_quartier_geojson

        result = parse_quartier_geojson(geojson_data)
        assert len(result) == 3

    def test_empty_feature_collection(self):
        from strata_api.pipeline.neighborhoods.quartier_parser import parse_quartier_geojson

        result = parse_quartier_geojson({"type": "FeatureCollection", "features": []})
        assert result == {}

    def test_area_km2_is_none_when_not_in_properties(self, geojson_data):
        """WFS data does not include area — should default to None."""
        from strata_api.pipeline.neighborhoods.quartier_parser import parse_quartier_geojson

        result = parse_quartier_geojson(geojson_data)
        # Area is not provided in the WFS data
        assert result[11].area_km2 is None

    def test_handles_missing_features_key(self):
        from strata_api.pipeline.neighborhoods.quartier_parser import parse_quartier_geojson

        result = parse_quartier_geojson({"type": "FeatureCollection"})
        assert result == {}

    def test_skips_features_with_no_geometry(self, geojson_data):
        """Features with null geometry should be skipped."""
        from strata_api.pipeline.neighborhoods.quartier_parser import parse_quartier_geojson

        data_with_null_geom = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": None,
                    "properties": {"qnr": 99, "qname": "Ghost", "knr": 9, "kname": "Kreis 9"},
                },
                *geojson_data["features"],
            ],
        }
        result = parse_quartier_geojson(data_with_null_geom)
        assert 99 not in result
        assert len(result) == 3
