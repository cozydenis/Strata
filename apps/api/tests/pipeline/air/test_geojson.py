"""Tests for the air-quality GeoJSON builder."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from strata_api.pipeline.air.aggregator import aggregate_measurements
from strata_api.pipeline.air.geojson import build_air_geojson
from strata_api.pipeline.air.parser import AirMeasurement, Station, parse_air_csv, parse_stations

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures" / "air"
SAMPLE_CSV = FIXTURES / "ugz_air_sample.csv"
STATIONS_JSON = FIXTURES / "ugz_air_stations.json"

_TS = datetime(2026, 7, 1, 21, 0, tzinfo=UTC)


def _measurement(station: str, parameter: str, value: float) -> AirMeasurement:
    return AirMeasurement(station, parameter, _TS, value, "µg/m3", "provisorisch")


def _station(station_id: str) -> Station:
    return Station(station_id, station_id, station_id, 47.4, 8.5, "Somewhere")


class TestBuildAirGeojson:
    def test_returns_feature_collection(self):
        aggregates = aggregate_measurements([_measurement("A", "O3", 40.0)])
        result = build_air_geojson(aggregates, {"A": _station("A")})
        assert result["type"] == "FeatureCollection"

    def test_feature_is_point_with_station_coordinates(self):
        aggregates = aggregate_measurements([_measurement("A", "O3", 40.0)])
        feature = build_air_geojson(aggregates, {"A": _station("A")})["features"][0]
        assert feature["geometry"]["type"] == "Point"
        assert feature["geometry"]["coordinates"] == [8.5, 47.4]

    def test_properties_include_level_and_measured_at(self):
        aggregates = aggregate_measurements([_measurement("A", "O3", 40.0)])
        props = build_air_geojson(aggregates, {"A": _station("A")})["features"][0]["properties"]
        assert props["level"] in {"good", "moderate", "high"}
        assert props["measured_at"] == _TS.isoformat()
        assert props["station_id"] == "A"

    def test_parameters_block_has_latest_mean_unit(self):
        aggregates = aggregate_measurements([_measurement("A", "O3", 40.0)])
        params = build_air_geojson(aggregates, {"A": _station("A")})["features"][0]["properties"]["parameters"]
        assert params["O3"]["latest"] == 40.0
        assert "mean_24h" in params["O3"]
        assert params["O3"]["unit"] == "µg/m3"

    def test_station_missing_from_metadata_is_skipped(self):
        aggregates = aggregate_measurements([_measurement("A", "O3", 40.0), _measurement("Ghost", "O3", 40.0)])
        result = build_air_geojson(aggregates, {"A": _station("A")})
        ids = [f["properties"]["station_id"] for f in result["features"]]
        assert ids == ["A"]

    def test_metadata_only_station_produces_no_feature(self):
        aggregates = aggregate_measurements([_measurement("A", "O3", 40.0)])
        result = build_air_geojson(aggregates, {"A": _station("A"), "Unused": _station("Unused")})
        assert len(result["features"]) == 1

    def test_empty_aggregates(self):
        assert build_air_geojson({}, {"A": _station("A")}) == {"type": "FeatureCollection", "features": []}

    def test_end_to_end_from_fixtures(self):
        measurements = parse_air_csv(SAMPLE_CSV.read_text(encoding="utf-8"))
        stations = parse_stations(STATIONS_JSON.read_text(encoding="utf-8"))
        result = build_air_geojson(aggregate_measurements(measurements), stations)
        # Four stations have data; Rosengartenbrücke is metadata-only -> 4 features
        assert len(result["features"]) == 4
        for feature in result["features"]:
            assert feature["geometry"]["type"] == "Point"
            lng, lat = feature["geometry"]["coordinates"]
            assert 8.0 < lng < 9.0 and 47.0 < lat < 48.0
            assert feature["properties"]["level"] in {"good", "moderate", "high"}
