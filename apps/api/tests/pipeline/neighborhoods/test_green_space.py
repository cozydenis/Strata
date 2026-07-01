"""TDD tests for the OSM green-space module — written BEFORE implementation (RED phase)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from strata_api.pipeline.neighborhoods.green_space import (
    GREEN_CATEGORIES,
    GreenArea,
    build_green_geojson,
    build_green_overpass_query,
    categorize_green_tags,
    compute_green_metrics,
    green_area_m2,
    parse_overpass_green,
)
from strata_api.pipeline.neighborhoods.quartier_parser import QuartierRecord

FIXTURE = Path(__file__).resolve().parents[2] / "fixtures" / "neighborhoods" / "green_overpass_sample.json"


def _load_fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


# ── Categorization ────────────────────────────────────────────────────────────


class TestCategorizeGreenTags:
    def test_park(self):
        assert categorize_green_tags({"leisure": "park"}) == "park"

    def test_garden(self):
        assert categorize_green_tags({"leisure": "garden"}) == "garden"

    def test_grass(self):
        assert categorize_green_tags({"landuse": "grass"}) == "grass"

    def test_meadow(self):
        assert categorize_green_tags({"landuse": "meadow"}) == "meadow"

    def test_forest(self):
        assert categorize_green_tags({"landuse": "forest"}) == "forest"

    def test_wood(self):
        assert categorize_green_tags({"natural": "wood"}) == "wood"

    def test_irrelevant_returns_none(self):
        assert categorize_green_tags({"landuse": "residential"}) is None
        assert categorize_green_tags({}) is None

    def test_all_categories_registered(self):
        assert set(GREEN_CATEGORIES) == {"park", "garden", "grass", "meadow", "forest", "wood"}


# ── Overpass query ─────────────────────────────────────────────────────────────


class TestBuildGreenOverpassQuery:
    def test_covers_every_category_value(self):
        query = build_green_overpass_query()
        for _key, values in GREEN_CATEGORIES.values():
            for value in values:
                assert value in query, f"{value} missing from Overpass query"

    def test_fetches_ways_and_relations_with_geometry(self):
        query = build_green_overpass_query()
        assert 'way["leisure"' in query
        assert 'relation["leisure"' in query
        # `out geom` is required so ways/relations carry vertex geometry
        assert "out geom;" in query

    def test_does_not_query_nodes(self):
        # Green space is areal — points are meaningless here
        query = build_green_overpass_query()
        assert 'node["leisure"' not in query


# ── Parsing ────────────────────────────────────────────────────────────────────


class TestParseOverpassGreen:
    def test_parses_way_categories(self):
        areas = parse_overpass_green(_load_fixture())
        cats = {a.category for a in areas}
        assert "park" in cats
        assert "forest" in cats
        assert "grass" in cats

    def test_named_park_preserved(self):
        areas = parse_overpass_green(_load_fixture())
        park = next(a for a in areas if a.name == "Test Park")
        assert park.category == "park"

    def test_relation_outer_ring_parsed(self):
        areas = parse_overpass_green(_load_fixture())
        rel = next(a for a in areas if a.name == "Bürkliterrasse")
        assert rel.category == "park"
        assert len(rel.coordinates) >= 3

    def test_degenerate_geometry_skipped(self):
        # The meadow way in the fixture has only 2 points -> skipped
        areas = parse_overpass_green(_load_fixture())
        assert not any(a.category == "meadow" for a in areas)

    def test_irrelevant_element_skipped(self):
        areas = parse_overpass_green(_load_fixture())
        # landuse=residential is not a green category
        assert all(a.category in GREEN_CATEGORIES for a in areas)

    def test_expected_area_count(self):
        # park way + forest way + grass way + park relation(outer) = 4 valid areas
        areas = parse_overpass_green(_load_fixture())
        assert len(areas) == 4

    def test_coordinates_are_lon_lat_pairs(self):
        areas = parse_overpass_green(_load_fixture())
        lon, lat = areas[0].coordinates[0]
        assert 8.0 < lon < 9.0
        assert 47.0 < lat < 48.0

    def test_empty_response(self):
        assert parse_overpass_green({"elements": []}) == []


# ── Area math ──────────────────────────────────────────────────────────────────

# ~0.001° x 0.001° square near lat 47.0 -> ~8450 m²
SMALL_SQUARE = [[8.5, 47.0], [8.501, 47.0], [8.501, 47.001], [8.5, 47.001], [8.5, 47.0]]


class TestGreenAreaM2:
    def test_known_square_area(self):
        area = green_area_m2(SMALL_SQUARE)
        assert area == pytest.approx(8450, rel=0.01)

    def test_degenerate_ring_is_zero(self):
        assert green_area_m2([[8.5, 47.0], [8.501, 47.0]]) == 0.0

    def test_area_is_orientation_independent(self):
        reversed_ring = list(reversed(SMALL_SQUARE))
        assert green_area_m2(reversed_ring) == pytest.approx(green_area_m2(SMALL_SQUARE))


# ── Per-quartier metrics (centroid assignment) ─────────────────────────────────

UNIT_SQUARE_GEOM = {
    "type": "Polygon",
    "coordinates": [[[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0], [0.0, 0.0]]],
}
SHIFTED_SQUARE_GEOM = {
    "type": "Polygon",
    "coordinates": [[[2.0, 2.0], [3.0, 2.0], [3.0, 3.0], [2.0, 3.0], [2.0, 2.0]]],
}


def _quartier(qid: int, geometry: dict, area_km2: float | None = 1.0) -> QuartierRecord:
    return QuartierRecord(quartier_id=qid, quartier_name=f"Q{qid}", kreis=1, area_km2=area_km2, geometry=geometry)


def _green(coords: list[list[float]], category: str = "park", name: str | None = None) -> GreenArea:
    return GreenArea.from_ring(name=name, category=category, coordinates=coords)


class TestComputeGreenMetrics:
    def test_park_assigned_to_centroid_quartier(self):
        quartiere = {11: _quartier(11, UNIT_SQUARE_GEOM), 12: _quartier(12, SHIFTED_SQUARE_GEOM)}
        # Park centroid ~ (0.5, 0.5) -> inside quartier 11 only
        park = _green([[0.4, 0.4], [0.6, 0.4], [0.6, 0.6], [0.4, 0.6], [0.4, 0.4]])
        metrics = compute_green_metrics([park], quartiere, {11: 1000, 12: 1000})
        assert metrics[11]["green_area_m2"] > 0
        assert metrics[12]["green_area_m2"] == 0

    def test_every_quartier_present_with_zero_default(self):
        quartiere = {11: _quartier(11, UNIT_SQUARE_GEOM)}
        metrics = compute_green_metrics([], quartiere, {11: 500})
        assert metrics[11]["green_area_m2"] == 0
        assert metrics[11]["green_share_pct"] == 0
        assert metrics[11]["green_m2_per_capita"] == 0

    def test_green_share_pct_computed(self):
        # quartier area 1 km² = 1_000_000 m²; a park of ~8450 m² -> ~0.845 %
        quartiere = {11: _quartier(11, {
            "type": "Polygon",
            "coordinates": [[[8.4, 46.9], [8.6, 46.9], [8.6, 47.1], [8.4, 47.1], [8.4, 46.9]]],
        }, area_km2=1.0)}
        park = _green(SMALL_SQUARE)
        metrics = compute_green_metrics([park], quartiere, {11: 1000})
        assert metrics[11]["green_area_m2"] == pytest.approx(8450, rel=0.01)
        assert metrics[11]["green_share_pct"] == pytest.approx(0.845, rel=0.02)

    def test_green_m2_per_capita_computed(self):
        quartiere = {11: _quartier(11, {
            "type": "Polygon",
            "coordinates": [[[8.4, 46.9], [8.6, 46.9], [8.6, 47.1], [8.4, 47.1], [8.4, 46.9]]],
        }, area_km2=1.0)}
        park = _green(SMALL_SQUARE)
        metrics = compute_green_metrics([park], quartiere, {11: 1000})
        assert metrics[11]["green_m2_per_capita"] == pytest.approx(8.45, rel=0.01)

    def test_zero_population_guard(self):
        quartiere = {11: _quartier(11, UNIT_SQUARE_GEOM)}
        park = _green([[0.4, 0.4], [0.6, 0.4], [0.6, 0.6], [0.4, 0.6], [0.4, 0.4]])
        metrics = compute_green_metrics([park], quartiere, {11: 0})
        assert metrics[11]["green_m2_per_capita"] is None

    def test_none_population_guard(self):
        quartiere = {11: _quartier(11, UNIT_SQUARE_GEOM)}
        park = _green([[0.4, 0.4], [0.6, 0.4], [0.6, 0.6], [0.4, 0.6], [0.4, 0.4]])
        metrics = compute_green_metrics([park], quartiere, {11: None})
        assert metrics[11]["green_m2_per_capita"] is None

    def test_share_none_when_area_missing(self):
        quartiere = {11: _quartier(11, UNIT_SQUARE_GEOM, area_km2=None)}
        park = _green([[0.4, 0.4], [0.6, 0.4], [0.6, 0.6], [0.4, 0.6], [0.4, 0.4]])
        metrics = compute_green_metrics([park], quartiere, {11: 1000})
        assert metrics[11]["green_share_pct"] is None

    def test_park_outside_all_quartiere_dropped(self):
        quartiere = {11: _quartier(11, UNIT_SQUARE_GEOM)}
        park = _green([[9.0, 9.0], [9.1, 9.0], [9.1, 9.1], [9.0, 9.1], [9.0, 9.0]])
        metrics = compute_green_metrics([park], quartiere, {11: 1000})
        assert metrics[11]["green_area_m2"] == 0


# ── GeoJSON builder ────────────────────────────────────────────────────────────


class TestBuildGreenGeojson:
    def test_feature_collection(self):
        areas = parse_overpass_green(_load_fixture())
        fc = build_green_geojson(areas)
        assert fc["type"] == "FeatureCollection"
        assert len(fc["features"]) == len(areas)

    def test_feature_is_polygon_with_properties(self):
        park = _green(SMALL_SQUARE, category="park", name="P")
        fc = build_green_geojson([park])
        feat = fc["features"][0]
        assert feat["type"] == "Feature"
        assert feat["geometry"]["type"] == "Polygon"
        assert feat["geometry"]["coordinates"] == [SMALL_SQUARE]
        assert feat["properties"]["name"] == "P"
        assert feat["properties"]["category"] == "park"
        assert feat["properties"]["area_m2"] == pytest.approx(8450, rel=0.01)

    def test_empty_areas(self):
        fc = build_green_geojson([])
        assert fc["features"] == []
