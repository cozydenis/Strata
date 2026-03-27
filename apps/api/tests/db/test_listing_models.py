"""Tests for Listing, ListingUnitMatch, and ListingHistory models (TDD — RED phase)."""
import datetime

import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session

from strata_api.db.base import Base
from strata_api.db.models.listing import Listing, ListingHistory, ListingUnitMatch


@pytest.fixture(scope="module")
def engine():
    eng = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(eng)
    yield eng
    eng.dispose()


@pytest.fixture
def session(engine):
    with Session(engine) as s:
        yield s
        s.rollback()


# ── Listing ──────────────────────────────────────────────────────────────────


class TestListingModel:
    def test_table_exists(self, engine):
        inspector = inspect(engine)
        assert "listings" in inspector.get_table_names()

    def test_required_columns_present(self, engine):
        inspector = inspect(engine)
        cols = {c["name"] for c in inspector.get_columns("listings")}
        required = {
            "id", "source", "source_id",
            "rent_net", "rent_gross", "rent_charges",
            "rooms", "area_m2",
            "address_raw", "street", "house_number", "plz", "city",
            "lat", "lng",
            "object_type", "offer_type", "status",
            "source_url",
            "first_seen", "last_seen", "is_active",
        }
        assert required <= cols, f"Missing columns: {required - cols}"

    def test_unique_constraint_source_plus_source_id(self, engine):
        inspector = inspect(engine)
        unique_constraints = inspector.get_unique_constraints("listings")
        unique_cols = {
            frozenset(c["column_names"]) for c in unique_constraints
        }
        assert frozenset({"source", "source_id"}) in unique_cols

    def test_insert_and_retrieve(self, session):
        listing = Listing(
            source="flatfox",
            source_id="123",
            rent_net=1800,
            rent_gross=2000,
            rent_charges=200,
            rooms=3.5,
            area_m2=80.0,
            address_raw="Bahnhofstrasse 1, 8001 Zürich",
            street="Bahnhofstrasse",
            house_number="1",
            plz=8001,
            city="Zürich",
            lat=47.376,
            lng=8.541,
            object_type="APARTMENT",
            offer_type="RENT",
            status="active",
            source_url="https://flatfox.ch/en/flat/bahnhofstrasse-8001-zurich/123/",
            first_seen=datetime.datetime(2024, 1, 15, 9, 0),
            last_seen=datetime.datetime(2024, 1, 15, 9, 0),
            is_active=True,
        )
        session.add(listing)
        session.flush()
        assert listing.id is not None

        fetched = session.get(Listing, listing.id)
        assert fetched is not None
        assert fetched.source == "flatfox"
        assert fetched.source_id == "123"
        assert fetched.rooms == 3.5
        assert fetched.is_active is True

    def test_nullable_fields_allowed(self, session):
        listing = Listing(
            source="homegate",
            source_id="HG-999",
            address_raw="Testgasse 5, 8004 Zürich",
            street="Testgasse",
            house_number="5",
            plz=8004,
            city="Zürich",
            offer_type="RENT",
            status="active",
            first_seen=datetime.datetime(2024, 2, 1),
            last_seen=datetime.datetime(2024, 2, 1),
            is_active=True,
        )
        session.add(listing)
        session.flush()
        assert listing.rent_net is None
        assert listing.lat is None
        assert listing.rooms is None


# ── ListingUnitMatch ──────────────────────────────────────────────────────────


class TestListingUnitMatchModel:
    def test_table_exists(self, engine):
        inspector = inspect(engine)
        assert "listing_unit_matches" in inspector.get_table_names()

    def test_required_columns_present(self, engine):
        inspector = inspect(engine)
        cols = {c["name"] for c in inspector.get_columns("listing_unit_matches")}
        required = {"id", "listing_id", "egid", "ewid", "match_confidence", "matched_egid"}
        assert required <= cols, f"Missing columns: {required - cols}"

    def test_confidence_values(self, session):
        listing = Listing(
            source="flatfox",
            source_id="match-test-1",
            address_raw="Musterstrasse 10, 8001 Zürich",
            street="Musterstrasse",
            house_number="10",
            plz=8001,
            city="Zürich",
            offer_type="RENT",
            status="active",
            first_seen=datetime.datetime(2024, 3, 1),
            last_seen=datetime.datetime(2024, 3, 1),
            is_active=True,
        )
        session.add(listing)
        session.flush()

        for confidence in ("exact", "probable", "building_only"):
            match = ListingUnitMatch(
                listing_id=listing.id,
                egid=12345,
                ewid=1,
                match_confidence=confidence,
                matched_egid=12345,
            )
            session.add(match)
        session.flush()

        matches = session.query(ListingUnitMatch).filter_by(listing_id=listing.id).all()
        assert len(matches) == 3
        confidences = {m.match_confidence for m in matches}
        assert confidences == {"exact", "probable", "building_only"}

    def test_ewid_nullable_for_building_only(self, session):
        listing = Listing(
            source="flatfox",
            source_id="match-test-2",
            address_raw="Bergweg 5, 8008 Zürich",
            street="Bergweg",
            house_number="5",
            plz=8008,
            city="Zürich",
            offer_type="RENT",
            status="active",
            first_seen=datetime.datetime(2024, 3, 2),
            last_seen=datetime.datetime(2024, 3, 2),
            is_active=True,
        )
        session.add(listing)
        session.flush()

        match = ListingUnitMatch(
            listing_id=listing.id,
            egid=99999,
            ewid=None,  # building_only: no unit identified
            match_confidence="building_only",
            matched_egid=99999,
        )
        session.add(match)
        session.flush()
        assert match.id is not None
        assert match.ewid is None


# ── ListingHistory ────────────────────────────────────────────────────────────


class TestListingHistoryModel:
    def test_table_exists(self, engine):
        inspector = inspect(engine)
        assert "listing_history" in inspector.get_table_names()

    def test_required_columns_present(self, engine):
        inspector = inspect(engine)
        cols = {c["name"] for c in inspector.get_columns("listing_history")}
        required = {"id", "listing_id", "field_changed", "old_value", "new_value", "changed_at"}
        assert required <= cols, f"Missing columns: {required - cols}"

    def test_insert_price_change(self, session):
        listing = Listing(
            source="flatfox",
            source_id="hist-test-1",
            address_raw="Seestrasse 20, 8002 Zürich",
            street="Seestrasse",
            house_number="20",
            plz=8002,
            city="Zürich",
            rent_net=1900,
            offer_type="RENT",
            status="active",
            first_seen=datetime.datetime(2024, 1, 1),
            last_seen=datetime.datetime(2024, 1, 1),
            is_active=True,
        )
        session.add(listing)
        session.flush()

        history = ListingHistory(
            listing_id=listing.id,
            field_changed="rent_net",
            old_value="1900",
            new_value="2050",
            changed_at=datetime.datetime(2024, 6, 1),
        )
        session.add(history)
        session.flush()

        fetched = session.get(ListingHistory, history.id)
        assert fetched is not None
        assert fetched.field_changed == "rent_net"
        assert fetched.old_value == "1900"
        assert fetched.new_value == "2050"
