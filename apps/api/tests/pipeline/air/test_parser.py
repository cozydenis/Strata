"""Tests for the UGZ air-quality parser (parse_air_csv, parse_stations)."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from strata_api.pipeline.air.parser import (
    AirMeasurement,
    Station,
    parse_air_csv,
    parse_stations,
)

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures" / "air"
SAMPLE_CSV = FIXTURES / "ugz_air_sample.csv"
STATIONS_JSON = FIXTURES / "ugz_air_stations.json"

_HEADER = '"Datum","Standort","Parameter","Intervall","Einheit","Wert","Status"'


@pytest.fixture
def sample_csv_text() -> str:
    return SAMPLE_CSV.read_text(encoding="utf-8")


@pytest.fixture
def stations_text() -> str:
    return STATIONS_JSON.read_text(encoding="utf-8")


def _csv(*rows: str) -> str:
    return "\n".join([_HEADER, *rows]) + "\n"


class TestParseAirCsv:
    def test_returns_measurements(self, sample_csv_text):
        result = parse_air_csv(sample_csv_text)
        assert result
        assert all(isinstance(m, AirMeasurement) for m in result)

    def test_all_four_stations_present(self, sample_csv_text):
        stations = {m.station for m in parse_air_csv(sample_csv_text)}
        assert stations == {
            "Zch_Heubeeribüel",
            "Zch_Rosengartenstrasse",
            "Zch_Schimmelstrasse",
            "Zch_Stampfenbachstrasse",
        }

    def test_all_parameters_present(self, sample_csv_text):
        params = {m.parameter for m in parse_air_csv(sample_csv_text)}
        assert {"NO", "NO2", "NOx", "O3", "PM10", "PM2.5"} <= params

    def test_timestamp_is_timezone_aware(self, sample_csv_text):
        m = parse_air_csv(sample_csv_text)[0]
        assert m.timestamp.tzinfo is not None

    def test_bom_stripped_and_first_column_parsed(self):
        text = _csv('"2026-07-01T21:00+0100","Zch_Test","NO2","h1","µg/m3",30.1,"provisorisch"')
        result = parse_air_csv(text)
        assert len(result) == 1
        assert result[0].value == pytest.approx(30.1)
        assert result[0].parameter == "NO2"

    def test_parses_utc_offset_timestamp(self):
        text = _csv('"2026-07-01T21:00+0100","Zch_Test","NO2","h1","µg/m3",30.1,"provisorisch"')
        m = parse_air_csv(text)[0]
        expected = datetime(2026, 7, 1, 20, 0, tzinfo=UTC)
        assert m.timestamp == expected

    def test_skips_empty_value_rows(self):
        text = _csv(
            '"2026-07-01T21:00+0100","Zch_Test","NO2","h1","µg/m3",,"provisorisch"',
            '"2026-07-01T21:00+0100","Zch_Test","O3","h1","µg/m3",44.0,"provisorisch"',
        )
        result = parse_air_csv(text)
        assert len(result) == 1
        assert result[0].parameter == "O3"

    def test_skips_non_numeric_value_rows(self):
        text = _csv('"2026-07-01T21:00+0100","Zch_Test","NO2","h1","µg/m3","n/a","provisorisch"')
        assert parse_air_csv(text) == []

    def test_skips_unknown_status_rows(self):
        text = _csv(
            '"2026-07-01T21:00+0100","Zch_Test","NO2","h1","µg/m3",30.1,"ungültig"',
            '"2026-07-01T21:00+0100","Zch_Test","O3","h1","µg/m3",44.0,"bereinigt"',
        )
        result = parse_air_csv(text)
        assert [m.parameter for m in result] == ["O3"]

    def test_accepts_both_valid_statuses(self):
        text = _csv(
            '"2026-07-01T21:00+0100","Zch_Test","NO2","h1","µg/m3",30.1,"provisorisch"',
            '"2026-07-01T20:00+0100","Zch_Test","NO2","h1","µg/m3",29.0,"bereinigt"',
        )
        assert len(parse_air_csv(text)) == 2

    def test_skips_unparseable_timestamp(self):
        text = _csv('"not-a-date","Zch_Test","NO2","h1","µg/m3",30.1,"provisorisch"')
        assert parse_air_csv(text) == []

    def test_empty_csv_returns_empty_list(self):
        assert parse_air_csv(_HEADER + "\n") == []

    def test_blank_string_returns_empty_list(self):
        assert parse_air_csv("") == []


class TestParseStations:
    def test_returns_station_map(self, stations_text):
        stations = parse_stations(stations_text)
        assert isinstance(stations, dict)
        assert all(isinstance(s, Station) for s in stations.values())

    def test_contains_known_stations(self, stations_text):
        stations = parse_stations(stations_text)
        assert "Zch_Stampfenbachstrasse" in stations
        assert stations["Zch_Stampfenbachstrasse"].short_name == "Stampfenbachstrasse"

    def test_coordinates_are_wgs84_floats(self, stations_text):
        s = parse_stations(stations_text)["Zch_Stampfenbachstrasse"]
        assert 47.0 < s.lat < 48.0
        assert 8.0 < s.lng < 9.0

    def test_accepts_dict_input(self, stations_text):
        import json

        as_dict = json.loads(stations_text)
        assert parse_stations(as_dict) == parse_stations(stations_text)

    def test_skips_entries_without_coordinates(self):
        data = {
            "Standorte": [
                {"ID": "Zch_Good", "Name": "Good", "Koordinaten_WGS84_lat": 47.4, "Koordinaten_WGS84_lng": 8.5},
                {"ID": "Zch_NoCoords", "Name": "Missing coords"},
            ]
        }
        stations = parse_stations(data)
        assert "Zch_Good" in stations
        assert "Zch_NoCoords" not in stations

    def test_empty_metadata(self):
        assert parse_stations({"Standorte": []}) == {}
        assert parse_stations({}) == {}
