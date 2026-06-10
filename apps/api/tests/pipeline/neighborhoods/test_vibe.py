"""TDD tests for vibe profiles — written BEFORE implementation (RED phase).

Vibes are explainable tags derived from each Quartier's metrics relative to the
citywide distribution (quartiles). Every tag carries human-readable evidence.
"""
from __future__ import annotations

from strata_api.pipeline.neighborhoods.vibe import MAX_TAGS, compute_vibes


def _feature(
    qid: int,
    *,
    young: float = 20.0,
    old: float = 15.0,
    foreign: float = 30.0,
    density: float = 5000.0,
    growth: float = 0.5,
    area: float = 2.0,
    cafes: int = 5,
    bars: int = 5,
    restaurants: int = 10,
    schools: int = 5,
    per_km2: float = 20.0,
    with_demo: bool = True,
    with_amenities: bool = True,
) -> dict:
    props = {
        "quartier_id": qid,
        "quartier_name": f"Q{qid}",
        "kreis": 1,
        "area_km2": area,
        "total_population": 10000 if with_demo else None,
        "population_density": density if with_demo else None,
        "foreign_pct": foreign if with_demo else None,
        "growth_rate": growth if with_demo else None,
        "age_18_29_pct": young if with_demo else None,
        "age_65plus_pct": old if with_demo else None,
        "amenities": (
            {
                "groceries": 5, "cafes": cafes, "restaurants": restaurants, "bars": bars,
                "pharmacies": 2, "schools": schools, "fitness": 3,
                "total": 5 + cafes + restaurants + bars + 2 + schools + 3,
                "per_km2": per_km2,
            }
            if with_amenities
            else None
        ),
    }
    return {"type": "Feature", "geometry": None, "properties": props}


def _baseline_city(n: int = 8) -> list[dict]:
    """A city of unremarkable quartiere — nothing should hit a top quartile."""
    return [_feature(100 + i) for i in range(n)]


class TestComputeVibes:
    def test_young_international_nightlife_quartier(self):
        features = [*_baseline_city(), _feature(1, young=35.0, foreign=50.0, bars=40, restaurants=80, area=1.0)]
        vibes = compute_vibes(features)
        tags = [t["tag"] for t in vibes[1]["tags"]]
        assert "young crowd" in tags
        assert "international" in tags
        assert "nightlife hub" in tags

    def test_older_swiss_quiet_quartier(self):
        features = [*_baseline_city(), _feature(2, old=30.0, foreign=12.0, per_km2=4.0, cafes=0, bars=0)]
        vibes = compute_vibes(features)
        tags = [t["tag"] for t in vibes[2]["tags"]]
        assert "settled & older" in tags
        assert "predominantly Swiss" in tags
        assert "quiet residential" in tags

    def test_every_tag_has_evidence(self):
        features = [*_baseline_city(), _feature(1, young=35.0, foreign=50.0, bars=40)]
        vibes = compute_vibes(features)
        for tag in vibes[1]["tags"]:
            assert isinstance(tag["evidence"], str)
            assert len(tag["evidence"]) > 10

    def test_tags_capped(self):
        # A quartier extreme on every dimension cannot exceed MAX_TAGS
        features = [
            *_baseline_city(),
            _feature(
                1, young=40.0, foreign=60.0, density=15000.0, growth=3.0,
                bars=50, cafes=50, restaurants=100, schools=30, per_km2=300.0, area=1.0,
            ),
        ]
        vibes = compute_vibes(features)
        assert len(vibes[1]["tags"]) <= MAX_TAGS

    def test_summary_present_and_capitalized(self):
        features = [*_baseline_city(), _feature(1, young=35.0, foreign=50.0)]
        vibes = compute_vibes(features)
        summary = vibes[1]["summary"]
        assert summary
        assert summary[0].isupper()
        assert summary.endswith('.')

    def test_unremarkable_quartier_gets_balanced_tag(self):
        """Middle-of-the-road quartiere still get a non-empty vibe."""
        vibes = compute_vibes(_baseline_city())
        assert vibes[100] is not None
        assert len(vibes[100]["tags"]) >= 1

    def test_no_demographics_no_vibe(self):
        features = [*_baseline_city(), _feature(3, with_demo=False)]
        vibes = compute_vibes(features)
        assert vibes[3] is None

    def test_missing_amenities_still_gets_demographic_tags(self):
        features = [*_baseline_city(), _feature(4, young=35.0, foreign=50.0, with_amenities=False)]
        vibes = compute_vibes(features)
        tags = [t["tag"] for t in vibes[4]["tags"]]
        assert "young crowd" in tags
        assert all("nightlife" not in t for t in tags)

    def test_dense_and_lowrise_tags(self):
        features = [
            *_baseline_city(),
            _feature(5, density=16000.0),
            _feature(6, density=900.0),
        ]
        vibes = compute_vibes(features)
        assert "dense urban fabric" in [t["tag"] for t in vibes[5]["tags"]]
        assert "low-rise & spacious" in [t["tag"] for t in vibes[6]["tags"]]

    def test_growth_tag(self):
        features = [*_baseline_city(), _feature(7, growth=3.5)]
        vibes = compute_vibes(features)
        assert "rapidly growing" in [t["tag"] for t in vibes[7]["tags"]]
