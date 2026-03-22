"""Tests for pipeline/dedup.py — Stadt Zürich wins deduplication."""
import pytest

from strata_api.pipeline.schemas import BuildingRecord, EntranceRecord, UnitRecord


def _building(egid: int, source: str) -> BuildingRecord:
    return BuildingRecord(egid=egid, data_source=source)


def _entrance(egid: int, edid: int, source: str) -> EntranceRecord:
    return EntranceRecord(egid=egid, edid=edid, data_source=source)


def _unit(egid: int, ewid: int, source: str) -> UnitRecord:
    return UnitRecord(egid=egid, ewid=ewid, data_source=source)


# ── extract_stadt_egids ────────────────────────────────────────────────────────

def test_extract_stadt_egids_returns_set():
    from strata_api.pipeline.dedup import extract_stadt_egids

    buildings = [_building(100, "stadt"), _building(200, "stadt")]
    result = extract_stadt_egids(buildings)
    assert isinstance(result, frozenset)


def test_extract_stadt_egids_contains_all_egids():
    from strata_api.pipeline.dedup import extract_stadt_egids

    buildings = [_building(100, "stadt"), _building(200, "stadt"), _building(300, "stadt")]
    result = extract_stadt_egids(buildings)
    assert result == frozenset({100, 200, 300})


def test_extract_stadt_egids_empty_input():
    from strata_api.pipeline.dedup import extract_stadt_egids

    assert extract_stadt_egids([]) == frozenset()


# ── filter_kanton_buildings ────────────────────────────────────────────────────

def test_filter_kanton_buildings_excludes_overlap():
    from strata_api.pipeline.dedup import filter_kanton_buildings

    stadt_egids = frozenset({100, 200})
    kanton = [_building(100, "kanton"), _building(300, "kanton"), _building(200, "kanton")]
    result = filter_kanton_buildings(kanton, stadt_egids)
    egids = [r.egid for r in result]
    assert 100 not in egids
    assert 200 not in egids
    assert 300 in egids


def test_filter_kanton_buildings_empty_overlap():
    from strata_api.pipeline.dedup import filter_kanton_buildings

    kanton = [_building(400, "kanton"), _building(500, "kanton")]
    result = filter_kanton_buildings(kanton, frozenset())
    assert len(result) == 2


def test_filter_kanton_buildings_all_overlap():
    from strata_api.pipeline.dedup import filter_kanton_buildings

    kanton = [_building(1, "kanton"), _building(2, "kanton")]
    result = filter_kanton_buildings(kanton, frozenset({1, 2}))
    assert result == []


# ── filter_kanton_entrances ────────────────────────────────────────────────────

def test_filter_kanton_entrances_excludes_overlap():
    from strata_api.pipeline.dedup import filter_kanton_entrances

    stadt_egids = frozenset({100, 200})
    kanton = [
        _entrance(100, 0, "kanton"),
        _entrance(300, 0, "kanton"),
        _entrance(200, 1, "kanton"),
    ]
    result = filter_kanton_entrances(kanton, stadt_egids)
    egids = [r.egid for r in result]
    assert 100 not in egids
    assert 200 not in egids
    assert 300 in egids


# ── filter_kanton_units ────────────────────────────────────────────────────────

def test_filter_kanton_units_excludes_overlap():
    from strata_api.pipeline.dedup import filter_kanton_units

    stadt_egids = frozenset({100})
    kanton = [_unit(100, 1, "kanton"), _unit(999, 1, "kanton")]
    result = filter_kanton_units(kanton, stadt_egids)
    egids = [r.egid for r in result]
    assert 100 not in egids
    assert 999 in egids
