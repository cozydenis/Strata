"""Tests for the rent-trends step (asking-rent CHF/m² per Quartier from the listings corpus)."""
from __future__ import annotations

import datetime

from strata_api.pipeline.neighborhoods.quartier_parser import QuartierRecord
from strata_api.pipeline.neighborhoods.rent_trends import (
    MIN_AREA_M2,
    MIN_MONTHLY_N,
    TREND_MONTHS,
    ListingObservation,
    chf_per_m2,
    compute_rent_stats,
    months_spanned,
)

NOW = datetime.datetime(2026, 7, 1, 12, 0)

# Two adjacent unit-square quartiers: A spans lon 0..1, B spans lon 1..2 (lat 0..1).
_QUARTIER_A = QuartierRecord(
    quartier_id=1, quartier_name="A", kreis=1, area_km2=1.0,
    geometry={"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]},
)
_QUARTIER_B = QuartierRecord(
    quartier_id=2, quartier_name="B", kreis=1, area_km2=1.0,
    geometry={"type": "Polygon", "coordinates": [[[1, 0], [2, 0], [2, 1], [1, 1], [1, 0]]]},
)
QUARTIERE = {1: _QUARTIER_A, 2: _QUARTIER_B}


def _obs(rent=2000, area=80.0, lng=0.5, lat=0.5, first=None, last=None, active=True):
    return ListingObservation(
        rent_net=rent,
        area_m2=area,
        lng=lng,
        lat=lat,
        first_seen=first or NOW - datetime.timedelta(days=10),
        last_seen=last or NOW,
        is_active=active,
    )


# ── chf_per_m2 ──
def test_chf_per_m2_basic():
    assert chf_per_m2(2000, 80.0) == 25.0


def test_chf_per_m2_excludes_bad_inputs():
    assert chf_per_m2(None, 80.0) is None
    assert chf_per_m2(2000, None) is None
    assert chf_per_m2(0, 80.0) is None
    assert chf_per_m2(-5, 80.0) is None
    assert chf_per_m2(2000, MIN_AREA_M2 - 0.5) is None  # implausibly small area


# ── months_spanned ──
def test_months_spanned_single_month():
    months = months_spanned(datetime.datetime(2026, 6, 3), datetime.datetime(2026, 6, 20))
    assert months == ["2026-06"]


def test_months_spanned_across_months():
    months = months_spanned(datetime.datetime(2026, 4, 25), datetime.datetime(2026, 6, 2))
    assert months == ["2026-04", "2026-05", "2026-06"]


def test_months_spanned_across_year_boundary():
    months = months_spanned(datetime.datetime(2025, 12, 15), datetime.datetime(2026, 1, 10))
    assert months == ["2025-12", "2026-01"]


# ── compute_rent_stats: current level ──
def test_current_median_over_active_listings():
    listings = [
        _obs(rent=2000, area=80.0),   # 25.0
        _obs(rent=2700, area=90.0),   # 30.0
        _obs(rent=3500, area=100.0),  # 35.0
        _obs(rent=9999, area=100.0, active=False),  # inactive → excluded from current level
    ]
    stats = compute_rent_stats(listings, QUARTIERE, now=NOW)
    assert stats[1].median_chf_m2 == 30.0
    assert stats[1].listing_count == 3


def test_quartier_without_listings_gets_none():
    stats = compute_rent_stats([_obs(lng=0.5)], QUARTIERE, now=NOW)
    assert stats[2].median_chf_m2 is None
    assert stats[2].listing_count == 0
    assert stats[2].trend == ()


def test_assignment_is_point_in_polygon():
    listings = [_obs(lng=0.5), _obs(lng=1.5, rent=4000, area=100.0)]
    stats = compute_rent_stats(listings, QUARTIERE, now=NOW)
    assert stats[1].listing_count == 1
    assert stats[2].listing_count == 1
    assert stats[2].median_chf_m2 == 40.0


def test_coordless_and_outside_listings_skipped():
    listings = [
        _obs(lng=None, lat=None),      # no coords
        _obs(lng=50.0, lat=50.0),      # outside every quartier
        _obs(),                        # valid
    ]
    stats = compute_rent_stats(listings, QUARTIERE, now=NOW)
    assert stats[1].listing_count == 1


# ── compute_rent_stats: trend ──
def test_trend_buckets_span_months_with_min_n():
    first = datetime.datetime(2026, 5, 10)
    listings = [
        _obs(rent=2000, area=80.0, first=first, last=NOW),   # 25.0 in May, Jun, Jul
        _obs(rent=2400, area=80.0, first=first, last=NOW),   # 30.0
        _obs(rent=2800, area=80.0, first=first, last=NOW),   # 35.0
        # Only present in June → June has n=4, others n=3
        _obs(rent=4000, area=100.0, first=datetime.datetime(2026, 6, 5), last=datetime.datetime(2026, 6, 25)),
    ]
    stats = compute_rent_stats(listings, QUARTIERE, now=NOW)
    trend = {point["month"]: point for point in stats[1].trend}
    assert trend["2026-05"]["median_chf_m2"] == 30.0
    assert trend["2026-05"]["n"] == 3
    assert trend["2026-06"]["n"] == 4
    assert trend["2026-06"]["median_chf_m2"] == 32.5  # median of 25, 30, 35, 40


def test_trend_months_below_min_n_omitted():
    listings = [_obs(), _obs(rent=2400)]  # only 2 listings → below MIN_MONTHLY_N
    assert MIN_MONTHLY_N == 3
    stats = compute_rent_stats(listings, QUARTIERE, now=NOW)
    assert stats[1].trend == ()


def test_trend_clipped_to_window():
    old_first = NOW - datetime.timedelta(days=800)
    listings = [
        _obs(first=old_first, last=NOW),
        _obs(rent=2400, first=old_first, last=NOW),
        _obs(rent=2800, first=old_first, last=NOW),
    ]
    stats = compute_rent_stats(listings, QUARTIERE, now=NOW)
    months = [point["month"] for point in stats[1].trend]
    assert len(months) <= TREND_MONTHS
    assert months == sorted(months)
    assert months[0] >= "2025-08"  # within the 12-month window of NOW


def test_trend_points_are_json_ready_dicts():
    listings = [_obs(), _obs(rent=2400), _obs(rent=2800)]
    stats = compute_rent_stats(listings, QUARTIERE, now=NOW)
    point = stats[1].trend[0]
    assert set(point.keys()) == {"month", "median_chf_m2", "n"}
