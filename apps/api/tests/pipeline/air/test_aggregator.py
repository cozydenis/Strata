"""Tests for the air-quality aggregator (latest, 24h mean, LRV level)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from strata_api.pipeline.air.aggregator import (
    LEVEL_GOOD,
    LEVEL_HIGH,
    LEVEL_MODERATE,
    LRV_NO2_24H_UGM3,
    LRV_O3_1H_UGM3,
    LRV_PM10_24H_UGM3,
    aggregate_measurements,
)
from strata_api.pipeline.air.parser import AirMeasurement, parse_air_csv

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures" / "air"
SAMPLE_CSV = FIXTURES / "ugz_air_sample.csv"

_BASE = datetime(2026, 7, 1, 21, 0, tzinfo=UTC)


def _m(station: str, parameter: str, value: float, hours_ago: int = 0, unit: str = "µg/m3") -> AirMeasurement:
    return AirMeasurement(
        station=station,
        parameter=parameter,
        timestamp=_BASE - timedelta(hours=hours_ago),
        value=value,
        unit=unit,
        status="provisorisch",
    )


class TestLatestAndMean:
    def test_latest_is_most_recent(self):
        ms = [_m("A", "O3", 10.0, hours_ago=2), _m("A", "O3", 99.0, hours_ago=0), _m("A", "O3", 50.0, hours_ago=1)]
        summary = aggregate_measurements(ms)["A"].parameters["O3"]
        assert summary.latest_value == pytest.approx(99.0)
        assert summary.latest_at == _BASE

    def test_mean_24h_averages_window(self):
        ms = [_m("A", "PM10", 10.0, hours_ago=0), _m("A", "PM10", 20.0, hours_ago=1), _m("A", "PM10", 30.0, hours_ago=2)]
        summary = aggregate_measurements(ms)["A"].parameters["PM10"]
        assert summary.mean_24h == pytest.approx(20.0)

    def test_mean_24h_excludes_older_than_window(self):
        ms = [_m("A", "PM10", 10.0, hours_ago=0), _m("A", "PM10", 1000.0, hours_ago=48)]
        summary = aggregate_measurements(ms)["A"].parameters["PM10"]
        assert summary.mean_24h == pytest.approx(10.0)

    def test_measured_at_is_max_across_parameters(self):
        ms = [_m("A", "O3", 10.0, hours_ago=3), _m("A", "NO2", 10.0, hours_ago=0)]
        assert aggregate_measurements(ms)["A"].measured_at == _BASE


class TestClassification:
    def test_o3_good_below_half_limit(self):
        value = LRV_O3_1H_UGM3 * 0.4
        summary = aggregate_measurements([_m("A", "O3", value)])["A"].parameters["O3"]
        assert summary.level == LEVEL_GOOD

    def test_o3_moderate_between_half_and_limit(self):
        value = LRV_O3_1H_UGM3 * 0.75
        summary = aggregate_measurements([_m("A", "O3", value)])["A"].parameters["O3"]
        assert summary.level == LEVEL_MODERATE

    def test_o3_high_above_limit(self):
        value = LRV_O3_1H_UGM3 * 1.2
        summary = aggregate_measurements([_m("A", "O3", value)])["A"].parameters["O3"]
        assert summary.level == LEVEL_HIGH

    def test_no2_classified_on_24h_mean(self):
        # two hours both above the limit -> mean above limit -> high
        ms = [_m("A", "NO2", LRV_NO2_24H_UGM3 * 1.1, hours_ago=0), _m("A", "NO2", LRV_NO2_24H_UGM3 * 1.1, hours_ago=1)]
        assert aggregate_measurements(ms)["A"].parameters["NO2"].level == LEVEL_HIGH

    def test_pm10_classified_on_24h_mean(self):
        summary = aggregate_measurements([_m("A", "PM10", LRV_PM10_24H_UGM3 * 0.3)])["A"].parameters["PM10"]
        assert summary.level == LEVEL_GOOD

    def test_no_and_nox_are_unrated(self):
        agg = aggregate_measurements([_m("A", "NO", 500.0), _m("A", "NOx", 500.0)])["A"]
        assert agg.parameters["NO"].level is None
        assert agg.parameters["NOx"].level is None

    def test_station_level_is_worst_of_parameters(self):
        ms = [
            _m("A", "O3", LRV_O3_1H_UGM3 * 0.2),  # good
            _m("A", "NO2", LRV_NO2_24H_UGM3 * 1.5),  # high
        ]
        assert aggregate_measurements(ms)["A"].level == LEVEL_HIGH

    def test_station_level_none_when_no_rated_parameters(self):
        assert aggregate_measurements([_m("A", "NO", 10.0)])["A"].level is None


class TestRealFixture:
    def test_aggregates_four_stations(self):
        measurements = parse_air_csv(SAMPLE_CSV.read_text(encoding="utf-8"))
        aggregates = aggregate_measurements(measurements)
        assert len(aggregates) == 4

    def test_each_station_has_all_parameters(self):
        measurements = parse_air_csv(SAMPLE_CSV.read_text(encoding="utf-8"))
        aggregates = aggregate_measurements(measurements)
        for agg in aggregates.values():
            assert {"NO", "NO2", "NOx", "O3", "PM10", "PM2.5"} <= set(agg.parameters)
            assert agg.level in {LEVEL_GOOD, LEVEL_MODERATE, LEVEL_HIGH}

    def test_empty_measurements(self):
        assert aggregate_measurements([]) == {}
