"""Tests for the address matching engine (TDD — RED phase).

Matching strategy:
  1. Exact:   normalize(street) + house_number + plz → egid in gwr_entrances → confidence "exact"
  2. Probable: fuzzy street name match within same PLZ → confidence "probable"
  3. Building-only: geo nearest-entrance fallback → confidence "building_only"
  4. Unit narrowing: within matched egid, filter by wazim (±0.5 rooms) and warea (±10%)
"""
import math
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from strata_api.db.base import Base
from strata_api.db.models import Building, Entrance, Unit  # noqa: F401 (registers all models)
from strata_api.pipeline.address_matcher import (
    MatchResult,
    normalize_street,
    match_listing,
)

# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def engine():
    eng = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(eng)
    return eng


@pytest.fixture
def db(engine):
    with Session(engine) as session:
        yield session
        session.rollback()


def _entrance(egid: int, strname: str, deinr: str, dplz4: int, lat: float = 47.37, lon: float = 8.54) -> Entrance:
    return Entrance(
        egid=egid,
        edid=1,
        strname=strname,
        deinr=deinr,
        dplz4=dplz4,
        dplzname="Zürich",
        doffadr=1,
        lat=lat,
        lon=lon,
        data_source="stadt",
    )


def _unit(egid: int, ewid: int, wazim: int | None = None, warea: int | None = None) -> Unit:
    return Unit(
        egid=egid,
        ewid=ewid,
        wazim=wazim,
        warea=warea,
        dplz4=8001,
        data_source="stadt",
    )


# ── normalize_street ──────────────────────────────────────────────────────────


class TestNormalizeStreet:
    def test_lowercase(self):
        assert normalize_street("Bahnhofstrasse") == "bahnhofstrasse"

    def test_strips_whitespace(self):
        assert normalize_street("  Seestrasse  ") == "seestrasse"

    def test_expands_str_abbreviation(self):
        assert normalize_street("Muster-Str.") == "musterstrasse"

    def test_expands_pl_abbreviation(self):
        """'Pl.' abbreviation expands to 'platz'."""
        assert normalize_street("Bahnhof-Pl.") == "bahnhofplatz"

    def test_umlaut_ae_equivalence(self):
        """'ä' and 'ae' both normalize to 'ae' so fuzzy can match them."""
        assert normalize_street("Rämistrasse") == normalize_street("Raemistrasse")

    def test_umlaut_oe_equivalence(self):
        assert normalize_street("Möhrengasse") == normalize_street("Moehrengasse")

    def test_umlaut_ue_equivalence(self):
        assert normalize_street("Mühlgasse") == normalize_street("Muehlgasse")

    def test_none_returns_empty_string(self):
        assert normalize_street(None) == ""


# ── match_listing — exact match ───────────────────────────────────────────────


class TestMatchListingExact:
    def test_exact_match_returns_egid(self, db):
        db.add(_entrance(egid=101, strname="Langstrasse", deinr="100", dplz4=8004))
        db.flush()

        results = match_listing(
            db, street="Langstrasse", house_number="100", plz=8004
        )
        assert len(results) >= 1
        assert any(r.egid == 101 and r.confidence == "exact" for r in results)

    def test_exact_match_is_case_insensitive(self, db):
        db.add(_entrance(egid=102, strname="Seestrasse", deinr="5", dplz4=8002))
        db.flush()

        results = match_listing(
            db, street="seestrasse", house_number="5", plz=8002
        )
        assert any(r.egid == 102 and r.confidence == "exact" for r in results)

    def test_no_match_returns_empty(self, db):
        results = match_listing(
            db, street="Fantasiestrasse", house_number="999", plz=9999
        )
        assert results == []

    def test_wrong_plz_no_exact_match(self, db):
        db.add(_entrance(egid=103, strname="Bergweg", deinr="3", dplz4=8050))
        db.flush()

        results = match_listing(
            db, street="Bergweg", house_number="3", plz=8099  # wrong PLZ
        )
        assert not any(r.egid == 103 and r.confidence == "exact" for r in results)


# ── match_listing — probable (fuzzy) ──────────────────────────────────────────


class TestMatchListingProbable:
    def test_abbreviated_strasse_matches(self, db):
        """'Str.' expands to 'Strasse' → should fuzzy-match 'Birsstrasse'."""
        db.add(_entrance(egid=201, strname="Birsstrasse", deinr="12", dplz4=8003))
        db.flush()

        results = match_listing(
            db, street="Birs-Str.", house_number="12", plz=8003
        )
        assert any(r.egid == 201 for r in results)

    def test_umlaut_variant_matches(self, db):
        """'Mühlgasse' in listing vs 'Muehlgasse' in GWR (or vice versa)."""
        db.add(_entrance(egid=202, strname="Muehlgasse", deinr="7", dplz4=8001))
        db.flush()

        results = match_listing(
            db, street="Mühlgasse", house_number="7", plz=8001
        )
        assert any(r.egid == 202 for r in results)


# ── match_listing — building_only (geo fallback) ──────────────────────────────


class TestMatchListingGeoFallback:
    def test_geo_fallback_when_address_unresolvable(self, db):
        """No address match but coordinates point to nearby entrance."""
        # Entrance at ~0 metres from listing coords
        db.add(_entrance(egid=301, strname="Quellenstrasse", deinr="17", dplz4=8005,
                         lat=47.3800, lon=8.5300))
        db.flush()

        results = match_listing(
            db,
            street="Gibberischwort",  # unresolvable address
            house_number="999",
            plz=8005,
            lat=47.3800,
            lng=8.5300,
        )
        assert any(r.egid == 301 and r.confidence == "building_only" for r in results)

    def test_geo_fallback_not_triggered_when_no_coords(self, db):
        results = match_listing(
            db,
            street="Nichtexistent",
            house_number="0",
            plz=8000,
            lat=None,
            lng=None,
        )
        assert results == []

    def test_geo_fallback_when_plz_not_in_gwr(self, db):
        """Address is valid but PLZ has zero entrances → geo fallback should fire."""
        # Entrance exists in PLZ 8005, but listing has PLZ 8570 (not in GWR)
        db.add(_entrance(egid=302, strname="Nearby", deinr="1", dplz4=8005,
                         lat=47.3810, lon=8.5310))
        db.flush()

        results = match_listing(
            db,
            street="Marktstrasse",  # valid street name
            house_number="28",      # valid house number
            plz=8570,               # not in our GWR dataset
            lat=47.3810,            # same coords as the entrance
            lng=8.5310,
        )
        assert any(r.egid == 302 and r.confidence == "building_only" for r in results)


# ── match_listing — unit narrowing ────────────────────────────────────────────


class TestMatchListingUnitNarrowing:
    def test_unit_narrowing_by_rooms_and_area(self, db):
        """Within matched building, units with matching rooms+area get ewid set."""
        db.add(_entrance(egid=401, strname="Preyergasse", deinr="10", dplz4=8001))
        db.add(_unit(egid=401, ewid=1, wazim=3, warea=75))   # 3 rooms, 75 m²
        db.add(_unit(egid=401, ewid=2, wazim=5, warea=110))  # 5 rooms, 110 m²
        db.flush()

        results = match_listing(
            db, street="Preyergasse", house_number="10", plz=8001,
            rooms=3.0, area_m2=75.0,
        )
        egid_401 = [r for r in results if r.egid == 401]
        assert len(egid_401) >= 1
        # ewid=1 should be in the results (3 rooms ±0.5, 75 m² ±10%)
        assert any(r.ewid == 1 for r in egid_401)
        # ewid=2 should NOT be in results (5 rooms is out of ±0.5 from 3)
        assert not any(r.ewid == 2 for r in egid_401)

    def test_unit_narrowing_rooms_tolerance(self, db):
        """Swiss half-room counting: 3.5-room listing matches 3- and 4-room GWR units."""
        db.add(_entrance(egid=402, strname="Feldeggstrasse", deinr="4", dplz4=8008))
        db.add(_unit(egid=402, ewid=1, wazim=3, warea=80))
        db.add(_unit(egid=402, ewid=2, wazim=4, warea=80))
        db.add(_unit(egid=402, ewid=3, wazim=6, warea=80))  # outside tolerance
        db.flush()

        results = match_listing(
            db, street="Feldeggstrasse", house_number="4", plz=8008,
            rooms=3.5, area_m2=80.0,
        )
        ewids = {r.ewid for r in results if r.egid == 402}
        assert 1 in ewids
        assert 2 in ewids
        assert 3 not in ewids

    def test_building_only_when_no_units_match(self, db):
        """If rooms/area don't narrow to any unit, return building_only match."""
        db.add(_entrance(egid=403, strname="Rosengartenstrasse", deinr="1", dplz4=8037))
        db.add(_unit(egid=403, ewid=1, wazim=6, warea=200))  # way off
        db.flush()

        results = match_listing(
            db, street="Rosengartenstrasse", house_number="1", plz=8037,
            rooms=2.0, area_m2=50.0,
        )
        match_403 = [r for r in results if r.egid == 403]
        assert len(match_403) >= 1
        # Should fall back to building_only since no units match
        assert any(r.confidence == "building_only" and r.ewid is None for r in match_403)

    def test_building_only_returned_when_no_rooms_given(self, db):
        """When rooms/area not provided, return building_only match."""
        db.add(_entrance(egid=404, strname="Limmatstrasse", deinr="2", dplz4=8005))
        db.add(_unit(egid=404, ewid=1, wazim=3, warea=70))
        db.flush()

        results = match_listing(
            db, street="Limmatstrasse", house_number="2", plz=8005
            # No rooms or area_m2
        )
        match_404 = [r for r in results if r.egid == 404]
        assert len(match_404) >= 1
        assert any(r.confidence in ("exact", "building_only") for r in match_404)


# ── MatchResult schema ────────────────────────────────────────────────────────


class TestMatchResult:
    def test_exact_confidence_value(self):
        r = MatchResult(egid=1, ewid=1, confidence="exact")
        assert r.confidence == "exact"

    def test_probable_confidence_value(self):
        r = MatchResult(egid=1, ewid=None, confidence="probable")
        assert r.confidence == "probable"

    def test_building_only_has_no_ewid(self):
        r = MatchResult(egid=1, ewid=None, confidence="building_only")
        assert r.ewid is None
