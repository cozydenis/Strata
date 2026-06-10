"""TDD tests for the watchlist events feed — written BEFORE implementation (RED phase).

Events are derived from listings matched to watched buildings:
- new_listing:   listing first_seen within the window
- price_change:  listing_history rent changes within the window
- listing_gone:  listing deactivated within the window
"""
from __future__ import annotations

import datetime
from unittest.mock import patch

import jwt
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from strata_api.db import models  # noqa: F401
from strata_api.db.base import Base
from strata_api.db.models.building import Building
from strata_api.db.models.listing import Listing, ListingHistory, ListingUnitMatch
from strata_api.db.models.watch import Watch

_TEST_SECRET = "test-jwt-secret"
_USER = "11111111-1111-1111-1111-111111111111"

NOW = datetime.datetime.utcnow()


def _auth(sub: str = _USER) -> dict:
    token = jwt.encode(
        {"sub": sub, "aud": "authenticated", "exp": datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=1)},
        _TEST_SECRET,
        algorithm="HS256",
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(autouse=True)
def patch_jwt_secret(monkeypatch):
    from strata_api.config import settings

    monkeypatch.setattr(settings, "supabase_jwt_secret", _TEST_SECRET)


def _listing(id_: int, *, first_seen: datetime.datetime, active: bool = True,
             last_seen: datetime.datetime | None = None, rent: int = 2000) -> Listing:
    return Listing(
        id=id_, source="flatfox", source_id=f"src-{id_}",
        rent_gross=rent, rooms=3.5, area_m2=80.0,
        street="Langstrasse", house_number="42", plz=8004, city="Zürich",
        source_url=f"https://flatfox.ch/x/{id_}",
        first_seen=first_seen, last_seen=last_seen or NOW, is_active=active,
        created_at=NOW, updated_at=NOW,
    )


@pytest.fixture
def events_engine():
    eng = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(eng)
    with Session(eng) as s:
        s.add(Building(
            egid=10001, gstat=1004, gkat=1020, gklas=1122,
            gbauj=1990, gabbj=None, garea=200, gastw=5, ganzwhg=10,
            lat=47.38, lon=8.54,
            municipality="Zürich", municipality_code=261, canton="ZH",
            data_source="stadt", created_at=NOW, updated_at=NOW,
        ))
        s.add(Building(
            egid=10002, gstat=1004, gkat=1020, gklas=1122,
            gbauj=2000, gabbj=None, garea=300, gastw=4, ganzwhg=8,
            lat=47.39, lon=8.55,
            municipality="Zürich", municipality_code=261, canton="ZH",
            data_source="stadt", created_at=NOW, updated_at=NOW,
        ))
        # The user watches building 10001 only
        s.add(Watch(user_id=_USER, egid=10001, ewid=None, created_at=NOW))

        from strata_api.db.models.entrance import Entrance
        s.add(Entrance(
            egid=10001, edid=0, strname="Registergasse", deinr="7",
            dplz4=8001, dplzname="Zürich", lat=47.38, lon=8.54,
            data_source="stadt", created_at=NOW, updated_at=NOW,
        ))

        # Listing 1: NEW (first seen 2 days ago) in watched building
        s.add(_listing(1, first_seen=NOW - datetime.timedelta(days=2)))
        s.add(ListingUnitMatch(listing_id=1, egid=10001, ewid=None, match_confidence="building_only", matched_egid=10001))

        # Listing 2: OLD (first seen 200 days ago) but had a price change 5 days ago
        s.add(_listing(2, first_seen=NOW - datetime.timedelta(days=200), rent=2400))
        s.add(ListingUnitMatch(listing_id=2, egid=10001, ewid=None, match_confidence="exact", matched_egid=10001))
        s.add(ListingHistory(
            listing_id=2, field_changed="rent_gross", old_value="2200", new_value="2400",
            changed_at=NOW - datetime.timedelta(days=5),
        ))
        # irrelevant non-price history entry — must NOT produce an event
        s.add(ListingHistory(
            listing_id=2, field_changed="description", old_value="a", new_value="b",
            changed_at=NOW - datetime.timedelta(days=4),
        ))

        # Listing 3: deactivated 1 day ago (gone) in watched building
        s.add(_listing(
            3, first_seen=NOW - datetime.timedelta(days=90), active=False,
            last_seen=NOW - datetime.timedelta(days=1),
        ))
        s.add(ListingUnitMatch(listing_id=3, egid=10001, ewid=None, match_confidence="probable", matched_egid=10001))

        # Listing 4: new listing in UNWATCHED building — must not appear
        s.add(_listing(4, first_seen=NOW - datetime.timedelta(days=1)))
        s.add(ListingUnitMatch(listing_id=4, egid=10002, ewid=None, match_confidence="exact", matched_egid=10002))

        # Listing 6: NEW but with no address of its own (geo-fallback match) —
        # the event must fall back to the building's GWR address
        bare = _listing(6, first_seen=NOW - datetime.timedelta(days=3))
        bare.street = None
        bare.house_number = None
        bare.plz = None
        bare.city = None
        s.add(bare)
        s.add(ListingUnitMatch(listing_id=6, egid=10001, ewid=None, match_confidence="building_only", matched_egid=10001))

        # Listing 5: ancient + still active — outside every window
        s.add(_listing(5, first_seen=NOW - datetime.timedelta(days=400)))
        s.add(ListingUnitMatch(listing_id=5, egid=10001, ewid=None, match_confidence="exact", matched_egid=10001))

        s.commit()
    yield eng
    eng.dispose()


@pytest.fixture
def client(events_engine):
    from strata_api.main import app

    with patch("strata_api.routers.watchlist.get_engine", return_value=events_engine):
        transport = ASGITransport(app=app)
        yield AsyncClient(transport=transport, base_url="http://test")


@pytest.mark.asyncio
async def test_events_require_auth(client):
    async with client as c:
        resp = await c.get("/watchlist/events")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_events_for_watched_building_only(client):
    async with client as c:
        resp = await c.get("/watchlist/events", headers=_auth())
    assert resp.status_code == 200
    data = resp.json()
    types = [e["type"] for e in data["items"]]
    assert sorted(types) == ["listing_gone", "new_listing", "new_listing", "price_change"]
    # listing 4 (unwatched building) and listing 5 (too old) excluded
    listing_ids = {e["listing_id"] for e in data["items"]}
    assert 4 not in listing_ids
    assert 5 not in listing_ids


@pytest.mark.asyncio
async def test_events_sorted_newest_first(client):
    async with client as c:
        resp = await c.get("/watchlist/events", headers=_auth())
    items = resp.json()["items"]
    timestamps = [e["ts"] for e in items]
    assert timestamps == sorted(timestamps, reverse=True)
    assert items[0]["type"] == "listing_gone"  # 1 day ago is the newest event


@pytest.mark.asyncio
async def test_new_listing_event_payload(client):
    async with client as c:
        resp = await c.get("/watchlist/events", headers=_auth())
    event = next(e for e in resp.json()["items"] if e["type"] == "new_listing")
    assert event["listing_id"] == 1
    assert event["egid"] == 10001
    assert event["street"] == "Langstrasse"
    assert event["house_number"] == "42"
    assert event["rent_gross"] == 2000
    assert event["rooms"] == 3.5
    assert event["source_url"]


@pytest.mark.asyncio
async def test_price_change_event_payload(client):
    async with client as c:
        resp = await c.get("/watchlist/events", headers=_auth())
    event = next(e for e in resp.json()["items"] if e["type"] == "price_change")
    assert event["listing_id"] == 2
    assert event["old_value"] == "2200"
    assert event["new_value"] == "2400"


@pytest.mark.asyncio
async def test_days_window_param(client):
    """days=3 keeps the 2-day-old new listing and 1-day-old gone, drops the 5-day-old price change."""
    async with client as c:
        resp = await c.get("/watchlist/events?days=3", headers=_auth())
    types = [e["type"] for e in resp.json()["items"]]
    assert "price_change" not in types
    assert "new_listing" in types


@pytest.mark.asyncio
async def test_no_watches_no_events(client):
    async with client as c:
        resp = await c.get("/watchlist/events", headers=_auth("99999999-9999-9999-9999-999999999999"))
    assert resp.status_code == 200
    assert resp.json() == {"total": 0, "items": []}


@pytest.mark.asyncio
async def test_street_less_listing_falls_back_to_gwr_address(client):
    async with client as c:
        resp = await c.get("/watchlist/events", headers=_auth())
    event = next(e for e in resp.json()["items"] if e["listing_id"] == 6)
    assert event["street"] == "Registergasse"
    assert event["house_number"] == "7"
    assert event["plz"] == 8001
