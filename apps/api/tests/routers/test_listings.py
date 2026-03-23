"""Tests for the listings API endpoint."""
import datetime

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from unittest.mock import patch

from strata_api.db.base import Base
from strata_api.db import models  # noqa: F401
from strata_api.db.models.building import Building
from strata_api.db.models.listing import Listing, ListingUnitMatch


@pytest.fixture(scope="module")
def listings_engine():
    eng = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(eng)

    now = datetime.datetime.utcnow()
    with Session(eng) as s:
        s.add(Building(
            egid=20001, gstat=1004, gkat=1020, gklas=1122,
            gbauj=1990, garea=200, gastw=5, ganzwhg=10,
            lat=47.38, lon=8.54,
            municipality="Zürich", municipality_code=261, canton="ZH",
            data_source="stadt", created_at=now, updated_at=now,
        ))
        s.add(Building(
            egid=20002, gstat=1004, gkat=1020, gklas=1110,
            gbauj=2005, garea=300, gastw=3, ganzwhg=6,
            lat=47.39, lon=8.55,
            municipality="Zürich", municipality_code=261, canton="ZH",
            data_source="stadt", created_at=now, updated_at=now,
        ))

        # Two active listings matched to building 20001
        l1 = Listing(
            source="flatfox", source_id="L-1001",
            rent_net=2000, rent_gross=2200, rooms=3.5, area_m2=80.0,
            address_raw="Teststr 1, 8001 Zürich", street="Teststrasse",
            house_number="1", plz=8001, city="Zürich",
            source_url="https://flatfox.ch/test/L-1001/",
            first_seen=now, last_seen=now, is_active=True,
        )
        l2 = Listing(
            source="flatfox", source_id="L-1002",
            rent_net=1800, rent_gross=2000, rooms=2.5, area_m2=60.0,
            address_raw="Teststr 1, 8001 Zürich", street="Teststrasse",
            house_number="1", plz=8001, city="Zürich",
            source_url="https://flatfox.ch/test/L-1002/",
            first_seen=now, last_seen=now, is_active=True,
        )
        # One inactive listing — should be excluded
        l3 = Listing(
            source="flatfox", source_id="L-1003",
            rent_net=1500, rooms=2.0, area_m2=50.0,
            address_raw="Teststr 1, 8001 Zürich", street="Teststrasse",
            house_number="1", plz=8001, city="Zürich",
            first_seen=now, last_seen=now, is_active=False,
        )
        s.add_all([l1, l2, l3])
        s.flush()

        s.add(ListingUnitMatch(
            listing_id=l1.id, egid=20001, ewid=None,
            matched_egid=20001, match_confidence="exact",
        ))
        s.add(ListingUnitMatch(
            listing_id=l2.id, egid=20001, ewid=None,
            matched_egid=20001, match_confidence="exact",
        ))
        s.add(ListingUnitMatch(
            listing_id=l3.id, egid=20001, ewid=None,
            matched_egid=20001, match_confidence="exact",
        ))
        s.commit()
    yield eng
    Base.metadata.drop_all(eng)


@pytest.mark.asyncio
async def test_get_listings_returns_active_only(listings_engine):
    from strata_api.main import app

    with patch("strata_api.routers.listings.get_engine", return_value=listings_engine):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/registry/buildings/20001/listings")

    assert response.status_code == 200
    data = response.json()
    assert data["egid"] == 20001
    assert len(data["listings"]) == 2
    source_ids = {l["source_id"] for l in data["listings"]}
    assert "L-1001" in source_ids
    assert "L-1002" in source_ids
    assert "L-1003" not in source_ids  # inactive


@pytest.mark.asyncio
async def test_get_listings_no_matches(listings_engine):
    from strata_api.main import app

    with patch("strata_api.routers.listings.get_engine", return_value=listings_engine):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/registry/buildings/20002/listings")

    assert response.status_code == 200
    data = response.json()
    assert data["egid"] == 20002
    assert data["listings"] == []


@pytest.mark.asyncio
async def test_get_listings_response_shape(listings_engine):
    from strata_api.main import app

    with patch("strata_api.routers.listings.get_engine", return_value=listings_engine):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/registry/buildings/20001/listings")

    listing = response.json()["listings"][0]
    expected_keys = {
        "id", "source", "source_id", "rent_net", "rent_gross",
        "rooms", "area_m2", "street", "house_number", "plz", "city",
        "source_url", "first_seen", "last_seen",
        "description", "images", "documents",
    }
    assert set(listing.keys()) == expected_keys
    assert isinstance(listing["images"], list)
    assert isinstance(listing["documents"], list)
