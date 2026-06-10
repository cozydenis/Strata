"""TDD tests for the OSM amenities module — written BEFORE implementation (RED phase)."""
from __future__ import annotations

import pytest

from strata_api.pipeline.neighborhoods.amenities import (
    AMENITY_CATEGORIES,
    AmenityPoint,
    categorize_tags,
    count_amenities_per_quartier,
    parse_overpass_amenities,
    point_in_geometry,
)
from strata_api.pipeline.neighborhoods.quartier_parser import QuartierRecord

# ── Overpass fixtures ─────────────────────────────────────────────────────────

OVERPASS_RESPONSE = {
    "version": 0.6,
    "elements": [
        # node with direct lat/lon
        {
            "type": "node",
            "id": 1,
            "lat": 47.38,
            "lon": 8.53,
            "tags": {"amenity": "cafe", "name": "Café Z"},
        },
        # way with center coordinates
        {
            "type": "way",
            "id": 2,
            "center": {"lat": 47.39, "lon": 8.54},
            "tags": {"shop": "supermarket", "name": "Migros"},
        },
        # node without a name
        {
            "type": "node",
            "id": 3,
            "lat": 47.37,
            "lon": 8.52,
            "tags": {"amenity": "pharmacy"},
        },
        # element with irrelevant tags — skipped
        {
            "type": "node",
            "id": 4,
            "lat": 47.36,
            "lon": 8.51,
            "tags": {"amenity": "parking"},
        },
        # way without center — skipped (no coordinates)
        {
            "type": "way",
            "id": 5,
            "tags": {"amenity": "restaurant"},
        },
        # node without tags — skipped
        {"type": "node", "id": 6, "lat": 47.35, "lon": 8.50},
    ],
}


class TestParseOverpassAmenities:
    def test_parses_node_with_coords(self):
        points = parse_overpass_amenities(OVERPASS_RESPONSE)
        cafe = next(p for p in points if p.category == "cafes")
        assert cafe.lat == pytest.approx(47.38)
        assert cafe.lon == pytest.approx(8.53)
        assert cafe.name == "Café Z"

    def test_parses_way_with_center(self):
        points = parse_overpass_amenities(OVERPASS_RESPONSE)
        grocery = next(p for p in points if p.category == "groceries")
        assert grocery.lat == pytest.approx(47.39)
        assert grocery.lon == pytest.approx(8.54)

    def test_nameless_amenity_kept(self):
        points = parse_overpass_amenities(OVERPASS_RESPONSE)
        pharmacy = next(p for p in points if p.category == "pharmacies")
        assert pharmacy.name is None

    def test_irrelevant_and_invalid_elements_skipped(self):
        points = parse_overpass_amenities(OVERPASS_RESPONSE)
        assert len(points) == 3  # cafe, supermarket, pharmacy

    def test_empty_response(self):
        assert parse_overpass_amenities({"elements": []}) == []


class TestCategorizeTags:
    def test_groceries(self):
        assert categorize_tags({"shop": "supermarket"}) == "groceries"
        assert categorize_tags({"shop": "convenience"}) == "groceries"

    def test_cafes(self):
        assert categorize_tags({"amenity": "cafe"}) == "cafes"

    def test_restaurants(self):
        assert categorize_tags({"amenity": "restaurant"}) == "restaurants"
        assert categorize_tags({"amenity": "fast_food"}) == "restaurants"

    def test_bars(self):
        assert categorize_tags({"amenity": "bar"}) == "bars"
        assert categorize_tags({"amenity": "pub"}) == "bars"

    def test_pharmacies(self):
        assert categorize_tags({"amenity": "pharmacy"}) == "pharmacies"

    def test_schools(self):
        assert categorize_tags({"amenity": "school"}) == "schools"
        assert categorize_tags({"amenity": "kindergarten"}) == "schools"

    def test_fitness(self):
        assert categorize_tags({"leisure": "fitness_centre"}) == "fitness"
        assert categorize_tags({"leisure": "sports_centre"}) == "fitness"

    def test_unknown_returns_none(self):
        assert categorize_tags({"amenity": "parking"}) is None
        assert categorize_tags({}) is None

    def test_all_categories_registered(self):
        assert set(AMENITY_CATEGORIES) == {
            "groceries", "cafes", "restaurants", "bars", "pharmacies", "schools", "fitness",
        }


# ── Point-in-polygon ──────────────────────────────────────────────────────────

UNIT_SQUARE = {
    "type": "Polygon",
    "coordinates": [[[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0], [0.0, 0.0]]],
}

SQUARE_WITH_HOLE = {
    "type": "Polygon",
    "coordinates": [
        [[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0], [0.0, 0.0]],
        [[0.4, 0.4], [0.6, 0.4], [0.6, 0.6], [0.4, 0.6], [0.4, 0.4]],
    ],
}

MULTI_SQUARES = {
    "type": "MultiPolygon",
    "coordinates": [
        [[[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0], [0.0, 0.0]]],
        [[[2.0, 2.0], [3.0, 2.0], [3.0, 3.0], [2.0, 3.0], [2.0, 2.0]]],
    ],
}


class TestPointInGeometry:
    def test_inside_polygon(self):
        assert point_in_geometry(0.5, 0.5, UNIT_SQUARE) is True

    def test_outside_polygon(self):
        assert point_in_geometry(1.5, 0.5, UNIT_SQUARE) is False

    def test_inside_hole_is_outside(self):
        assert point_in_geometry(0.5, 0.5, SQUARE_WITH_HOLE) is False

    def test_between_hole_and_exterior(self):
        assert point_in_geometry(0.2, 0.2, SQUARE_WITH_HOLE) is True

    def test_multipolygon_second_part(self):
        assert point_in_geometry(2.5, 2.5, MULTI_SQUARES) is True

    def test_multipolygon_gap(self):
        assert point_in_geometry(1.5, 1.5, MULTI_SQUARES) is False

    def test_unsupported_geometry(self):
        assert point_in_geometry(0.5, 0.5, {"type": "Point", "coordinates": [0.5, 0.5]}) is False


# ── Per-quartier counting ─────────────────────────────────────────────────────


def _quartier(qid: int, name: str, geometry: dict) -> QuartierRecord:
    return QuartierRecord(quartier_id=qid, quartier_name=name, kreis=1, area_km2=1.0, geometry=geometry)


SHIFTED_SQUARE = {
    "type": "Polygon",
    "coordinates": [[[2.0, 2.0], [3.0, 2.0], [3.0, 3.0], [2.0, 3.0], [2.0, 2.0]]],
}


class TestCountAmenitiesPerQuartier:
    def test_points_assigned_to_containing_quartier(self):
        quartiere = {
            11: _quartier(11, "A", UNIT_SQUARE),
            12: _quartier(12, "B", SHIFTED_SQUARE),
        }
        points = [
            AmenityPoint(category="cafes", name="c1", lat=0.5, lon=0.5),
            AmenityPoint(category="cafes", name="c2", lat=0.6, lon=0.4),
            AmenityPoint(category="groceries", name="g1", lat=2.5, lon=2.5),
        ]
        counts = count_amenities_per_quartier(points, quartiere)
        assert counts[11]["cafes"] == 2
        assert counts[12]["groceries"] == 1

    def test_every_quartier_has_all_categories(self):
        quartiere = {11: _quartier(11, "A", UNIT_SQUARE)}
        counts = count_amenities_per_quartier([], quartiere)
        assert set(counts[11]) == set(AMENITY_CATEGORIES)
        assert all(v == 0 for v in counts[11].values())

    def test_point_outside_all_quartiere_ignored(self):
        quartiere = {11: _quartier(11, "A", UNIT_SQUARE)}
        points = [AmenityPoint(category="bars", name=None, lat=9.0, lon=9.0)]
        counts = count_amenities_per_quartier(points, quartiere)
        assert counts[11]["bars"] == 0


class TestBuildOverpassQuery:
    def test_query_covers_every_category_value(self):
        """Regression: categories sharing a tag key (amenity) must all survive."""
        from strata_api.pipeline.neighborhoods.amenities import build_overpass_query

        query = build_overpass_query()
        for _key, values in AMENITY_CATEGORIES.values():
            for value in values:
                assert value in query, f"{value} missing from Overpass query"

    def test_query_has_node_and_way_clauses(self):
        from strata_api.pipeline.neighborhoods.amenities import build_overpass_query

        query = build_overpass_query()
        assert 'node["amenity"' in query
        assert 'way["amenity"' in query
        assert "out center;" in query
