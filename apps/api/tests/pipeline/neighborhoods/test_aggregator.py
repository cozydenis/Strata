"""TDD tests for aggregator — written BEFORE implementation (RED phase)."""
from __future__ import annotations

import pytest

from strata_api.pipeline.neighborhoods.demographics_parser import QuartierDemographics
from strata_api.pipeline.neighborhoods.quartier_parser import QuartierRecord

POLYGON_GEOM = {"type": "Polygon", "coordinates": [[[8.53, 47.37], [8.54, 47.37], [8.54, 47.38], [8.53, 47.37]]]}


def _make_quartier(qid: int, name: str, kreis: int, area_km2: float | None = 1.0) -> QuartierRecord:
    return QuartierRecord(
        quartier_id=qid,
        quartier_name=name,
        kreis=kreis,
        area_km2=area_km2,
        geometry=POLYGON_GEOM,
    )


def _make_demo(
    qid: int,
    year: int = 2023,
    total: int = 1000,
    swiss: int = 700,
    foreign: int = 300,
    yoy: int | None = 50,
    age_buckets: dict | None = None,
) -> QuartierDemographics:
    if age_buckets is None:
        age_buckets = {"0-17": 150, "18-29": 250, "30-44": 300, "45-64": 200, "65+": 100}
    return QuartierDemographics(
        quartier_id=qid,
        year=year,
        total_population=total,
        age_buckets=age_buckets,
        swiss_count=swiss,
        foreign_count=foreign,
        yoy_change=yoy,
    )


class TestAggregateQuartierGeojson:
    """Tests for aggregate_quartier_geojson."""

    def test_function_is_importable(self):
        from strata_api.pipeline.neighborhoods.aggregator import (
            aggregate_quartier_geojson,  # noqa: F401
        )

    def test_returns_feature_collection(self):
        from strata_api.pipeline.neighborhoods.aggregator import aggregate_quartier_geojson

        records = {11: _make_quartier(11, "Rathaus", 1)}
        demos = {11: _make_demo(11)}
        result = aggregate_quartier_geojson(records, demos)
        assert result["type"] == "FeatureCollection"
        assert "features" in result

    def test_feature_count_matches_quartier_count(self):
        from strata_api.pipeline.neighborhoods.aggregator import aggregate_quartier_geojson

        records = {
            11: _make_quartier(11, "Rathaus", 1),
            12: _make_quartier(12, "Hochschulen", 1),
            73: _make_quartier(73, "Hirslanden", 7),
        }
        demos = {11: _make_demo(11), 12: _make_demo(12)}
        result = aggregate_quartier_geojson(records, demos)
        assert len(result["features"]) == 3

    def test_feature_has_quartier_id_property(self):
        from strata_api.pipeline.neighborhoods.aggregator import aggregate_quartier_geojson

        records = {11: _make_quartier(11, "Rathaus", 1)}
        demos = {11: _make_demo(11)}
        result = aggregate_quartier_geojson(records, demos)
        feat = result["features"][0]
        assert feat["properties"]["quartier_id"] == 11

    def test_feature_has_quartier_name_property(self):
        from strata_api.pipeline.neighborhoods.aggregator import aggregate_quartier_geojson

        records = {11: _make_quartier(11, "Rathaus", 1)}
        demos = {11: _make_demo(11)}
        result = aggregate_quartier_geojson(records, demos)
        feat = result["features"][0]
        assert feat["properties"]["quartier_name"] == "Rathaus"

    def test_feature_has_kreis_property(self):
        from strata_api.pipeline.neighborhoods.aggregator import aggregate_quartier_geojson

        records = {11: _make_quartier(11, "Rathaus", 1)}
        demos = {11: _make_demo(11)}
        result = aggregate_quartier_geojson(records, demos)
        feat = result["features"][0]
        assert feat["properties"]["kreis"] == 1

    def test_population_density_computed_from_area(self):
        from strata_api.pipeline.neighborhoods.aggregator import aggregate_quartier_geojson

        records = {11: _make_quartier(11, "Rathaus", 1, area_km2=0.5)}
        demos = {11: _make_demo(11, total=1000)}
        result = aggregate_quartier_geojson(records, demos)
        props = result["features"][0]["properties"]
        assert props["population_density"] == pytest.approx(2000.0)

    def test_population_density_is_none_when_no_area(self):
        from strata_api.pipeline.neighborhoods.aggregator import aggregate_quartier_geojson

        records = {11: _make_quartier(11, "Rathaus", 1, area_km2=None)}
        demos = {11: _make_demo(11, total=1000)}
        result = aggregate_quartier_geojson(records, demos)
        props = result["features"][0]["properties"]
        assert props["population_density"] is None

    def test_swiss_pct_computed(self):
        from strata_api.pipeline.neighborhoods.aggregator import aggregate_quartier_geojson

        records = {11: _make_quartier(11, "Rathaus", 1)}
        demos = {11: _make_demo(11, total=1000, swiss=700, foreign=300)}
        result = aggregate_quartier_geojson(records, demos)
        props = result["features"][0]["properties"]
        assert props["swiss_pct"] == pytest.approx(70.0)
        assert props["foreign_pct"] == pytest.approx(30.0)

    def test_yoy_change_passed_through(self):
        from strata_api.pipeline.neighborhoods.aggregator import aggregate_quartier_geojson

        records = {11: _make_quartier(11, "Rathaus", 1)}
        demos = {11: _make_demo(11, total=1000, yoy=50)}
        result = aggregate_quartier_geojson(records, demos)
        props = result["features"][0]["properties"]
        assert props["yoy_change"] == 50

    def test_growth_rate_computed(self):
        """growth_rate = yoy_change / (total - yoy_change) * 100."""
        from strata_api.pipeline.neighborhoods.aggregator import aggregate_quartier_geojson

        records = {11: _make_quartier(11, "Rathaus", 1)}
        demos = {11: _make_demo(11, total=1050, yoy=50)}
        result = aggregate_quartier_geojson(records, demos)
        props = result["features"][0]["properties"]
        expected = 50 / (1050 - 50) * 100
        assert props["growth_rate"] == pytest.approx(expected)

    def test_trend_growing(self):
        from strata_api.pipeline.neighborhoods.aggregator import aggregate_quartier_geojson

        records = {11: _make_quartier(11, "Rathaus", 1)}
        demos = {11: _make_demo(11, total=1050, yoy=50)}
        result = aggregate_quartier_geojson(records, demos)
        assert result["features"][0]["properties"]["trend"] == "growing"

    def test_trend_declining(self):
        from strata_api.pipeline.neighborhoods.aggregator import aggregate_quartier_geojson

        records = {11: _make_quartier(11, "Rathaus", 1)}
        demos = {11: _make_demo(11, total=950, yoy=-50)}
        result = aggregate_quartier_geojson(records, demos)
        assert result["features"][0]["properties"]["trend"] == "declining"

    def test_trend_stable(self):
        """yoy_change of 0 or None -> stable."""
        from strata_api.pipeline.neighborhoods.aggregator import aggregate_quartier_geojson

        records = {11: _make_quartier(11, "Rathaus", 1)}
        demos = {11: _make_demo(11, total=1000, yoy=0)}
        result = aggregate_quartier_geojson(records, demos)
        assert result["features"][0]["properties"]["trend"] == "stable"

    def test_trend_stable_when_yoy_is_none(self):
        from strata_api.pipeline.neighborhoods.aggregator import aggregate_quartier_geojson

        records = {11: _make_quartier(11, "Rathaus", 1)}
        demos = {11: _make_demo(11, total=1000, yoy=None)}
        result = aggregate_quartier_geojson(records, demos)
        assert result["features"][0]["properties"]["trend"] == "stable"

    def test_age_pct_properties_present(self):
        from strata_api.pipeline.neighborhoods.aggregator import aggregate_quartier_geojson

        records = {11: _make_quartier(11, "Rathaus", 1)}
        demos = {11: _make_demo(11, total=1000, age_buckets={
            "0-17": 100, "18-29": 200, "30-44": 300, "45-64": 250, "65+": 150,
        })}
        result = aggregate_quartier_geojson(records, demos)
        props = result["features"][0]["properties"]
        assert props["age_0_17_pct"] == pytest.approx(10.0)
        assert props["age_18_29_pct"] == pytest.approx(20.0)
        assert props["age_30_44_pct"] == pytest.approx(30.0)
        assert props["age_45_64_pct"] == pytest.approx(25.0)
        assert props["age_65plus_pct"] == pytest.approx(15.0)

    def test_quartier_without_demographics_gets_null_values(self):
        """Quartier 73 has no demographic data — all demographic fields should be None."""
        from strata_api.pipeline.neighborhoods.aggregator import aggregate_quartier_geojson

        records = {
            11: _make_quartier(11, "Rathaus", 1),
            73: _make_quartier(73, "Hirslanden", 7),
        }
        demos = {11: _make_demo(11)}  # No demo for 73
        result = aggregate_quartier_geojson(records, demos)

        feats_by_id = {f["properties"]["quartier_id"]: f for f in result["features"]}
        props_73 = feats_by_id[73]["properties"]
        assert props_73["total_population"] is None
        assert props_73["population_density"] is None
        assert props_73["swiss_pct"] is None
        assert props_73["trend"] is None

    def test_feature_geometry_preserved(self):
        from strata_api.pipeline.neighborhoods.aggregator import aggregate_quartier_geojson

        records = {11: _make_quartier(11, "Rathaus", 1)}
        demos = {11: _make_demo(11)}
        result = aggregate_quartier_geojson(records, demos)
        geom = result["features"][0]["geometry"]
        assert geom["type"] == "Polygon"

    def test_empty_inputs(self):
        from strata_api.pipeline.neighborhoods.aggregator import aggregate_quartier_geojson

        result = aggregate_quartier_geojson({}, {})
        assert result["type"] == "FeatureCollection"
        assert result["features"] == []

    def test_growth_rate_none_when_yoy_is_none(self):
        from strata_api.pipeline.neighborhoods.aggregator import aggregate_quartier_geojson

        records = {11: _make_quartier(11, "Rathaus", 1)}
        demos = {11: _make_demo(11, total=1000, yoy=None)}
        result = aggregate_quartier_geojson(records, demos)
        props = result["features"][0]["properties"]
        assert props["growth_rate"] is None
