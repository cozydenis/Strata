"""Unit tests for Quartierüblichkeit comparables math (OR Art. 270)."""
import datetime
from types import SimpleNamespace

from strata_api.legal.quartierueblichkeit import (
    Verdict,
    analyze_initial_rent,
    select_comparables,
)

NOW = datetime.datetime(2026, 7, 1)


def _listing(**kw) -> SimpleNamespace:
    base = dict(id=0, rooms=3.0, area_m2=80.0, rent_net=2000, plz=8005, last_seen=NOW)
    base.update(kw)
    return SimpleNamespace(**base)


def _comparable(chf_per_m2: float, cid: int) -> SimpleNamespace:
    """Comparable with area 100 m² so rent_net/area == the requested CHF/m²."""
    return _listing(id=cid, area_m2=100.0, rent_net=chf_per_m2 * 100, rooms=3.0, plz=8005)


# --- selection filters --------------------------------------------------------

def test_select_comparables_applies_all_filters():
    target = _listing(id=1, rooms=3.0, area_m2=80.0, plz=8005)
    candidates = [
        _listing(id=2, area_m2=85.0),                                   # OK
        _listing(id=1),                                                 # self -> excluded
        _listing(id=3, rent_net=None),                                  # no rent -> excluded
        _listing(id=4, area_m2=None),                                   # no area -> excluded
        _listing(id=5, plz=8006),                                       # different PLZ -> excluded
        _listing(id=6, rooms=4.0),                                      # rooms +1.0 -> excluded
        _listing(id=7, area_m2=100.0),                                  # 100 > 96 -> excluded
        _listing(id=8, last_seen=datetime.datetime(2024, 1, 1)),        # too old -> excluded
        _listing(id=9, rooms=3.5),                                      # rooms edge 0.5 -> OK
        _listing(id=10, area_m2=96.0),                                  # area edge +20% -> OK
    ]
    selected = select_comparables(target, candidates, now=NOW)
    assert {c.id for c in selected} == {2, 9, 10}


def test_select_comparables_empty_when_target_has_no_area():
    target = _listing(id=1, area_m2=None)
    assert select_comparables(target, [_listing(id=2)], now=NOW) == []


def test_select_comparables_recency_edge_inclusive():
    target = _listing(id=1)
    # exactly 24 calendar months before NOW -> included (>= cutoff)
    on_edge = _listing(id=2, last_seen=datetime.datetime(2024, 7, 1))
    assert {c.id for c in select_comparables(target, [on_edge], now=NOW)} == {2}


# --- percentile / verdict math (pinned) --------------------------------------
# Comparable CHF/m² set: [20, 22, 24, 25, 26, 28, 30, 32], N=8
#   median = (25 + 26) / 2 = 25.5
#   p25 (nearest-rank, ceil(0.25*8)=2) -> 22
#   p75 (nearest-rank, ceil(0.75*8)=6) -> 28
#   p75 * 1.10 = 30.8
_EIGHT = [20, 22, 24, 25, 26, 28, 30, 32]


def _eight_comparables() -> list[SimpleNamespace]:
    return [_comparable(v, cid=100 + i) for i, v in enumerate(_EIGHT)]


def test_pinned_percentiles():
    target = _comparable(25.0, cid=1)
    result = analyze_initial_rent(target, _eight_comparables())
    assert result.comparable_count == 8
    assert result.median_chf_m2 == 25.5
    assert result.p25_chf_m2 == 22.0
    assert result.p75_chf_m2 == 28.0


def test_verdict_within_range_at_p75_boundary():
    target = _comparable(28.0, cid=1)  # == p75 -> within range (<=)
    result = analyze_initial_rent(target, _eight_comparables())
    assert result.verdict is Verdict.WITHIN_RANGE
    assert result.target_chf_m2 == 28.0


def test_verdict_above_market_at_upper_boundary():
    target = _comparable(30.8, cid=1)  # == p75 * 1.10 -> above_market (<=)
    result = analyze_initial_rent(target, _eight_comparables())
    assert result.verdict is Verdict.ABOVE_MARKET


def test_verdict_clearly_above_market_just_over_threshold():
    target = _comparable(31.0, cid=1)  # > p75 * 1.10 (30.8) -> clearly above
    result = analyze_initial_rent(target, _eight_comparables())
    assert result.verdict is Verdict.CLEARLY_ABOVE_MARKET


def test_verdict_within_range_below_median():
    target = _comparable(21.0, cid=1)
    result = analyze_initial_rent(target, _eight_comparables())
    assert result.verdict is Verdict.WITHIN_RANGE


def test_insufficient_data_below_minimum():
    target = _comparable(30.0, cid=1)
    result = analyze_initial_rent(target, _eight_comparables()[:4])  # only 4
    assert result.verdict is Verdict.INSUFFICIENT_DATA
    assert result.comparable_count == 4
    assert result.median_chf_m2 is None
    assert "minimum 5" in result.explanation


def test_insufficient_data_when_target_missing_fields():
    target = _listing(id=1, rent_net=None, area_m2=None)
    result = analyze_initial_rent(target, _eight_comparables())
    assert result.verdict is Verdict.INSUFFICIENT_DATA
    assert result.target_chf_m2 is None


# --- explanation --------------------------------------------------------------

def test_explanation_contains_key_figures_and_disclaimer():
    target = _comparable(30.8, cid=1)
    result = analyze_initial_rent(target, _eight_comparables())
    assert "30.8" in result.explanation          # asking CHF/m²
    assert "25.5" in result.explanation          # median
    assert "28.0" in result.explanation          # p75
    assert "8 comparable" in result.explanation  # count
    assert "not legal advice" in result.explanation
