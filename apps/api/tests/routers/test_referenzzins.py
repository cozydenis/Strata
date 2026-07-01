"""Tests for the /legal Referenzzinssatz + Herabsetzungsbegehren endpoints."""
import datetime
from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from strata_api.db import models  # noqa: F401
from strata_api.db.base import Base
from strata_api.db.models.listing import Listing
from strata_api.db.models.reference_rate import ReferenceRate
from strata_api.main import app


@pytest.fixture(scope="module")
def legal_engine():
    eng = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(eng)
    now = datetime.datetime.utcnow()
    with Session(eng) as s:
        s.add(ReferenceRate(valid_from=datetime.date(2023, 12, 1), rate_percent=1.75, source="bwo"))
        s.add(ReferenceRate(valid_from=datetime.date(2025, 3, 3), rate_percent=1.50, source="bwo"))
        s.add(ReferenceRate(valid_from=datetime.date(2025, 9, 1), rate_percent=1.25, source="bwo"))

        # id 1: explicit base rate 1.75, rent 2000 → 2 steps down vs current 1.25
        s.add(Listing(
            id=1, source="flatfox", source_id="L-1",
            rent_net=2000, base_reference_rate=1.75,
            street="Teststrasse", house_number="1", plz=8001, city="Zürich",
            first_seen=datetime.datetime(2024, 6, 1), last_seen=now, is_active=True,
        ))
        # id 2: no base rate, first_seen in the 1.50 era (2025-06)
        s.add(Listing(
            id=2, source="flatfox", source_id="L-2",
            rent_net=1800,
            street="Beispielweg", house_number="2", plz=8004, city="Zürich",
            first_seen=datetime.datetime(2025, 6, 1), last_seen=now, is_active=True,
        ))
        # id 3: no base rate, no rent, first_seen current era (== current rate)
        s.add(Listing(
            id=3, source="flatfox", source_id="L-3",
            street="Leerstrasse", house_number="3", plz=8005, city="Zürich",
            first_seen=datetime.datetime(2026, 6, 1), last_seen=now, is_active=True,
        ))
        s.commit()
    return eng


@pytest.fixture
async def legal_client(legal_engine):
    with patch("strata_api.routers.referenzzins.get_engine", return_value=legal_engine):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            yield ac


async def test_reference_rate_endpoint(legal_client):
    r = await legal_client.get("/legal/reference-rate")
    assert r.status_code == 200
    body = r.json()
    assert body["current"]["rate_percent"] == 1.25
    assert len(body["history"]) == 3


async def test_rent_analysis_known_base(legal_client):
    r = await legal_client.get("/legal/listings/1/rent-analysis")
    assert r.status_code == 200
    body = r.json()
    assert body["basis"] == "known"
    assert body["base_rate"] == 1.75
    assert body["current_rate"] == 1.25
    assert body["change_pct"] == -5.74
    assert body["monthly_chf"] == -114.8
    assert body["direction"] == "reduction"
    assert "reduction" in body["message"].lower()


async def test_rent_analysis_assumed_from_first_seen(legal_client):
    r = await legal_client.get("/legal/listings/2/rent-analysis")
    assert r.status_code == 200
    body = r.json()
    assert body["basis"] == "assumed_from_first_seen"
    assert body["base_rate"] == 1.50
    assert body["change_pct"] == -2.91


async def test_rent_analysis_no_rent_yields_null_chf(legal_client):
    r = await legal_client.get("/legal/listings/3/rent-analysis")
    assert r.status_code == 200
    body = r.json()
    assert body["direction"] == "none"       # 1.25 base == 1.25 current
    assert body["monthly_chf"] is None       # no rent_net → no CHF impact


async def test_rent_analysis_base_rate_override(legal_client):
    r = await legal_client.get("/legal/listings/2/rent-analysis?base_rate=2.0")
    assert r.status_code == 200
    body = r.json()
    assert body["basis"] == "override"
    assert body["base_rate"] == 2.0
    assert body["change_pct"] == -8.49       # 2.00 → 1.25 = 3 steps


async def test_rent_analysis_invalid_base_rate(legal_client):
    r = await legal_client.get("/legal/listings/2/rent-analysis?base_rate=1.3")
    assert r.status_code == 422


async def test_rent_analysis_unknown_listing(legal_client):
    r = await legal_client.get("/legal/listings/999/rent-analysis")
    assert r.status_code == 404


async def test_generate_letter(legal_client):
    payload = {
        "tenant_name": "Anna Muster",
        "tenant_address": "Teststrasse 1, 8001 Zürich",
        "landlord_name": "Verwaltung AG",
        "landlord_address": "Bahnhofstrasse 5, 8001 Zürich",
    }
    r = await legal_client.post("/legal/listings/1/herabsetzungsbegehren", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert "Herabsetzungsbegehren" in body["letter"]
    assert "Anna Muster" in body["letter"]
    assert "5.74" in body["letter"]


async def test_generate_letter_missing_tenant_name(legal_client):
    r = await legal_client.post("/legal/listings/1/herabsetzungsbegehren", json={})
    assert r.status_code == 422


async def test_generate_letter_no_reduction_conflict(legal_client):
    payload = {
        "tenant_name": "Bea Beispiel",
        "tenant_address": "Leerstrasse 3, 8005 Zürich",
        "landlord_name": "Haus AG",
        "landlord_address": "Weg 1, 8005 Zürich",
    }
    r = await legal_client.post("/legal/listings/3/herabsetzungsbegehren", json=payload)
    assert r.status_code == 409


# --- Initial-rent check (OR Art. 270) ----------------------------------------
# Comparable CHF/m² set (area 80 m² -> rent = value * 80): [20,22,24,25,26,28,30,32]
#   median 25.5, p25 22, p75 28, p75*1.10 = 30.8
_IR_CHF = [20, 22, 24, 25, 26, 28, 30, 32]


def _seed_quarter(session, plz: int, base_id: int, now):
    """Seed 8 comparable listings in one PLZ (rooms 3.0, area 80 m²)."""
    for i, chf in enumerate(_IR_CHF):
        session.add(Listing(
            id=base_id + i, source="flatfox", source_id=f"IR-{base_id + i}",
            rent_net=chf * 80, rooms=3.0, area_m2=80.0, plz=plz, city="Zürich",
            first_seen=now, last_seen=now, is_active=True,
        ))


@pytest.fixture(scope="module")
def ir_engine():
    eng = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(eng)
    now = datetime.datetime.utcnow()
    with Session(eng) as s:
        # Each scenario gets its own PLZ so targets never pollute each other's pool.
        _seed_quarter(s, plz=8020, base_id=1000, now=now)  # within-range quarter
        _seed_quarter(s, plz=8021, base_id=1100, now=now)  # above-market quarter
        _seed_quarter(s, plz=8022, base_id=1200, now=now)  # clearly-above quarter

        # Targets (rooms 3.0, area 80) hitting each verdict.
        s.add(Listing(id=2000, source="flatfox", source_id="T-within",
                      rent_net=2000, rooms=3.0, area_m2=80.0, plz=8020, city="Zürich",
                      first_seen=now, last_seen=now, is_active=True))  # 25.0 -> within_range
        s.add(Listing(id=2001, source="flatfox", source_id="T-above",
                      rent_net=2400, rooms=3.0, area_m2=80.0, plz=8021, city="Zürich",
                      first_seen=now, last_seen=now, is_active=True))  # 30.0 -> above_market
        s.add(Listing(id=2002, source="flatfox", source_id="T-clearly",
                      rent_net=2560, rooms=3.0, area_m2=80.0, plz=8022, city="Zürich",
                      first_seen=now, last_seen=now, is_active=True))  # 32.0 -> clearly_above

        # Insufficient-data quarter: only 3 comparables + a target.
        for i, chf in enumerate([24, 26, 28]):
            s.add(Listing(id=1300 + i, source="flatfox", source_id=f"IR-{1300 + i}",
                          rent_net=chf * 80, rooms=3.0, area_m2=80.0, plz=8023, city="Zürich",
                          first_seen=now, last_seen=now, is_active=True))
        s.add(Listing(id=2003, source="flatfox", source_id="T-sparse",
                      rent_net=2400, rooms=3.0, area_m2=80.0, plz=8023, city="Zürich",
                      first_seen=now, last_seen=now, is_active=True))

        # Target missing area/rent -> insufficient_data, never 500.
        s.add(Listing(id=2004, source="flatfox", source_id="T-noarea",
                      rent_net=2400, rooms=3.0, area_m2=None, plz=8020, city="Zürich",
                      first_seen=now, last_seen=now, is_active=True))
        s.commit()
    return eng


@pytest.fixture
async def ir_client(ir_engine):
    with patch("strata_api.routers.referenzzins.get_engine", return_value=ir_engine):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            yield ac


async def test_initial_rent_check_unknown_listing(ir_client):
    r = await ir_client.get("/legal/listings/999999/initial-rent-check")
    assert r.status_code == 404


async def test_initial_rent_check_within_range(ir_client):
    r = await ir_client.get("/legal/listings/2000/initial-rent-check")
    assert r.status_code == 200
    body = r.json()
    assert body["verdict"] == "within_range"
    assert body["target_chf_m2"] == 25.0
    assert body["median_chf_m2"] == 25.5
    assert body["p25"] == 22.0
    assert body["p75"] == 28.0
    assert body["comparable_count"] == 8
    assert body["or270"]["deadline_days"] == 30
    assert "Schlichtungsbehörde" in body["or270"]["schlichtungsbehoerde"]


async def test_initial_rent_check_above_market(ir_client):
    r = await ir_client.get("/legal/listings/2001/initial-rent-check")
    assert r.status_code == 200
    body = r.json()
    assert body["verdict"] == "above_market"
    assert body["target_chf_m2"] == 30.0


async def test_initial_rent_check_clearly_above_market(ir_client):
    r = await ir_client.get("/legal/listings/2002/initial-rent-check")
    assert r.status_code == 200
    body = r.json()
    assert body["verdict"] == "clearly_above_market"
    assert body["target_chf_m2"] == 32.0
    assert "clearly" in body["explanation"].lower()


async def test_initial_rent_check_insufficient_data(ir_client):
    r = await ir_client.get("/legal/listings/2003/initial-rent-check")
    assert r.status_code == 200
    body = r.json()
    assert body["verdict"] == "insufficient_data"
    assert body["comparable_count"] == 3
    assert body["median_chf_m2"] is None


async def test_initial_rent_check_missing_area_is_insufficient_not_500(ir_client):
    r = await ir_client.get("/legal/listings/2004/initial-rent-check")
    assert r.status_code == 200
    body = r.json()
    assert body["verdict"] == "insufficient_data"
    assert body["target_chf_m2"] is None
    assert "no net rent" in body["explanation"].lower() or "area" in body["explanation"].lower()
