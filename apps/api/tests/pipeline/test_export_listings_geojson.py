"""Tests for the GeoJSON listings export script."""
import datetime
import json

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from strata_api.db.base import Base
from strata_api.db import models  # noqa: F401
from strata_api.db.models.building import Building
from strata_api.db.models.listing import Listing, ListingUnitMatch


@pytest.fixture
def listings_export_engine():
    eng = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(eng)

    now = datetime.datetime.utcnow()
    with Session(eng) as s:
        # Building with 2 active listings
        s.add(Building(
            egid=40001, gkat=1021, gbauj=1990, gastw=5, ganzwhg=10,
            lat=47.376, lon=8.541, gstat=1004,
            municipality="Zürich", municipality_code=261, canton="ZH",
            data_source="stadt", created_at=now, updated_at=now,
        ))
        # Building with 0 listings
        s.add(Building(
            egid=40002, gkat=1025, gbauj=2010, gastw=3, ganzwhg=6,
            lat=47.391, lon=8.552, gstat=1004,
            municipality="Zürich", municipality_code=261, canton="ZH",
            data_source="stadt", created_at=now, updated_at=now,
        ))
        # Building with null coords — should be excluded
        s.add(Building(
            egid=40003, gkat=1060, gbauj=1970, gastw=2, ganzwhg=4,
            lat=None, lon=None, gstat=1004,
            municipality="Zürich", municipality_code=261, canton="ZH",
            data_source="stadt", created_at=now, updated_at=now,
        ))

        l1 = Listing(
            source="flatfox", source_id="EX-1",
            rent_net=2000, rent_gross=2200, rooms=3.5, area_m2=80.0,
            first_seen=now, last_seen=now, is_active=True,
        )
        l2 = Listing(
            source="flatfox", source_id="EX-2",
            rent_net=1500, rent_gross=1700, rooms=2.0, area_m2=55.0,
            first_seen=now, last_seen=now, is_active=True,
        )
        # Inactive listing — should not count
        l3 = Listing(
            source="flatfox", source_id="EX-3",
            rent_net=3000, rent_gross=3200, rooms=4.0, area_m2=100.0,
            first_seen=now, last_seen=now, is_active=False,
        )
        # Active listing matched to null-coord building
        l4 = Listing(
            source="flatfox", source_id="EX-4",
            rent_net=1000, rooms=1.0, area_m2=30.0,
            first_seen=now, last_seen=now, is_active=True,
        )
        s.add_all([l1, l2, l3, l4])
        s.flush()

        s.add(ListingUnitMatch(listing_id=l1.id, egid=40001, ewid=None, matched_egid=40001, match_confidence="exact"))
        s.add(ListingUnitMatch(listing_id=l2.id, egid=40001, ewid=None, matched_egid=40001, match_confidence="exact"))
        s.add(ListingUnitMatch(listing_id=l3.id, egid=40001, ewid=None, matched_egid=40001, match_confidence="exact"))
        s.add(ListingUnitMatch(listing_id=l4.id, egid=40003, ewid=None, matched_egid=40003, match_confidence="building_only"))
        s.commit()
    yield eng
    Base.metadata.drop_all(eng)


def test_export_returns_feature_collection(listings_export_engine):
    from strata_api.scripts.export_listings_geojson import export_listings_geojson

    result = export_listings_geojson(listings_export_engine)
    assert result["type"] == "FeatureCollection"
    assert "features" in result


def test_export_only_includes_buildings_with_active_listings(listings_export_engine):
    from strata_api.scripts.export_listings_geojson import export_listings_geojson

    result = export_listings_geojson(listings_export_engine)
    egids = {f["properties"]["egid"] for f in result["features"]}
    assert 40001 in egids       # has active listings
    assert 40002 not in egids   # no listings at all


def test_export_excludes_null_coordinate_buildings(listings_export_engine):
    from strata_api.scripts.export_listings_geojson import export_listings_geojson

    result = export_listings_geojson(listings_export_engine)
    egids = {f["properties"]["egid"] for f in result["features"]}
    assert 40003 not in egids   # has listing but null coords


def test_export_feature_has_correct_properties(listings_export_engine):
    from strata_api.scripts.export_listings_geojson import export_listings_geojson

    result = export_listings_geojson(listings_export_engine)
    for feature in result["features"]:
        assert set(feature["properties"].keys()) == {"egid", "listing_count", "cheapest_rent"}


def test_export_listing_count_is_correct(listings_export_engine):
    from strata_api.scripts.export_listings_geojson import export_listings_geojson

    result = export_listings_geojson(listings_export_engine)
    f = next(f for f in result["features"] if f["properties"]["egid"] == 40001)
    assert f["properties"]["listing_count"] == 2  # only active listings count


def test_export_cheapest_rent_picks_minimum(listings_export_engine):
    from strata_api.scripts.export_listings_geojson import export_listings_geojson

    result = export_listings_geojson(listings_export_engine)
    f = next(f for f in result["features"] if f["properties"]["egid"] == 40001)
    # cheapest_rent should prefer rent_gross; min(2200, 1700) = 1700
    assert f["properties"]["cheapest_rent"] == 1700


def test_export_is_valid_json(listings_export_engine):
    from strata_api.scripts.export_listings_geojson import export_listings_geojson

    result = export_listings_geojson(listings_export_engine)
    dumped = json.dumps(result)
    parsed = json.loads(dumped)
    assert parsed["type"] == "FeatureCollection"
