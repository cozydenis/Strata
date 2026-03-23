"""Tests for the listing loader — upsert, change detection, deactivation (TDD — RED)."""
import datetime

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from strata_api.db.base import Base
from strata_api.db.models import Building, Entrance, Unit  # registers all models
from strata_api.db.models.listing import Listing, ListingHistory, ListingUnitMatch
from strata_api.pipeline.connectors.flatfox import FlatfoxListing
from strata_api.pipeline.listing_loader import deactivate_missing, upsert_listings


@pytest.fixture(scope="module")
def engine():
    eng = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(eng)
    yield eng
    eng.dispose()


@pytest.fixture
def db(engine):
    with Session(engine) as session:
        yield session
        session.rollback()


def _listing(
    source_id: str = "1001",
    source: str = "flatfox",
    rent_net: int = 2000,
    rent_gross: int = 2200,
    rent_charges: int = 200,
    rooms: float = 3.5,
    area_m2: float = 80.0,
    street: str = "Seestrasse",
    house_number: str = "10",
    plz: int = 8002,
    city: str = "Zürich",
    status: str = "active",
    offer_type: str = "RENT",
    address_raw: str = "Seestrasse 10, 8002 Zürich",
    source_url: str = "https://flatfox.ch/en/flat/seestrasse-8002/1001/",
    description: str | None = None,
) -> FlatfoxListing:
    return FlatfoxListing(
        source=source,
        source_id=source_id,
        rent_net=rent_net,
        rent_gross=rent_gross,
        rent_charges=rent_charges,
        rooms=rooms,
        area_m2=area_m2,
        address_raw=address_raw,
        street=street,
        house_number=house_number,
        plz=plz,
        city=city,
        status=status,
        offer_type=offer_type,
        source_url=source_url,
        description=description,
    )


# ── Insert new listing ────────────────────────────────────────────────────────


class TestUpsertNewListing:
    def test_new_listing_inserted(self, db):
        stats = upsert_listings(db, [_listing(source_id="2001")])
        assert stats["inserted"] == 1

        row = db.execute(
            select(Listing).where(Listing.source_id == "2001")
        ).scalar_one()
        assert row.rent_net == 2000
        assert row.plz == 8002
        assert row.is_active is True

    def test_new_listing_sets_first_seen_and_last_seen(self, db):
        before = datetime.datetime.utcnow()
        upsert_listings(db, [_listing(source_id="2002")])
        after = datetime.datetime.utcnow()

        row = db.execute(
            select(Listing).where(Listing.source_id == "2002")
        ).scalar_one()
        assert before <= row.first_seen <= after
        assert before <= row.last_seen <= after

    def test_new_listing_first_seen_equals_last_seen(self, db):
        upsert_listings(db, [_listing(source_id="2003")])
        row = db.execute(
            select(Listing).where(Listing.source_id == "2003")
        ).scalar_one()
        assert row.first_seen == row.last_seen

    def test_new_listing_stores_description(self, db):
        upsert_listings(db, [_listing(source_id="2010", description="Nice flat")])
        row = db.execute(
            select(Listing).where(Listing.source_id == "2010")
        ).scalar_one()
        assert row.description == "Nice flat"

    def test_no_history_entry_for_new_listing(self, db):
        upsert_listings(db, [_listing(source_id="2004")])
        row = db.execute(
            select(Listing).where(Listing.source_id == "2004")
        ).scalar_one()
        history = db.execute(
            select(ListingHistory).where(ListingHistory.listing_id == row.id)
        ).scalars().all()
        assert history == []


# ── Upsert unchanged listing ──────────────────────────────────────────────────


class TestUpsertUnchangedListing:
    def test_unchanged_listing_counted_as_unchanged(self, db):
        upsert_listings(db, [_listing(source_id="3001")])
        stats = upsert_listings(db, [_listing(source_id="3001")])
        assert stats["unchanged"] == 1
        assert stats.get("inserted", 0) == 0

    def test_unchanged_listing_updates_last_seen(self, db):
        upsert_listings(db, [_listing(source_id="3002")])
        first_row = db.execute(
            select(Listing).where(Listing.source_id == "3002")
        ).scalar_one()
        first_last_seen = first_row.last_seen

        # Second upsert with identical data
        upsert_listings(db, [_listing(source_id="3002")])
        row = db.execute(
            select(Listing).where(Listing.source_id == "3002")
        ).scalar_one()
        assert row.last_seen >= first_last_seen

    def test_unchanged_listing_does_not_change_first_seen(self, db):
        upsert_listings(db, [_listing(source_id="3003")])
        first_row = db.execute(
            select(Listing).where(Listing.source_id == "3003")
        ).scalar_one()
        original_first_seen = first_row.first_seen

        upsert_listings(db, [_listing(source_id="3003")])
        row = db.execute(
            select(Listing).where(Listing.source_id == "3003")
        ).scalar_one()
        assert row.first_seen == original_first_seen


# ── Upsert changed listing ────────────────────────────────────────────────────


class TestUpsertChangedListing:
    def test_price_change_updates_rent_net(self, db):
        upsert_listings(db, [_listing(source_id="4001", rent_net=2000)])
        upsert_listings(db, [_listing(source_id="4001", rent_net=2100)])

        row = db.execute(
            select(Listing).where(Listing.source_id == "4001")
        ).scalar_one()
        assert row.rent_net == 2100

    def test_price_change_counted_as_updated(self, db):
        upsert_listings(db, [_listing(source_id="4002", rent_net=1800)])
        stats = upsert_listings(db, [_listing(source_id="4002", rent_net=1900)])
        assert stats["updated"] == 1

    def test_price_change_logged_to_history(self, db):
        upsert_listings(db, [_listing(source_id="4003", rent_net=2500)])
        upsert_listings(db, [_listing(source_id="4003", rent_net=2600)])

        row = db.execute(
            select(Listing).where(Listing.source_id == "4003")
        ).scalar_one()
        history = db.execute(
            select(ListingHistory).where(
                ListingHistory.listing_id == row.id,
                ListingHistory.field_changed == "rent_net",
            )
        ).scalars().all()

        assert len(history) == 1
        assert history[0].old_value == "2500"
        assert history[0].new_value == "2600"

    def test_status_change_logged_to_history(self, db):
        upsert_listings(db, [_listing(source_id="4004", status="active")])
        upsert_listings(db, [_listing(source_id="4004", status="inactive")])

        row = db.execute(
            select(Listing).where(Listing.source_id == "4004")
        ).scalar_one()
        history = db.execute(
            select(ListingHistory).where(
                ListingHistory.listing_id == row.id,
                ListingHistory.field_changed == "status",
            )
        ).scalars().all()

        assert len(history) == 1
        assert history[0].old_value == "active"
        assert history[0].new_value == "inactive"

    def test_multiple_field_changes_all_logged(self, db):
        upsert_listings(db, [_listing(source_id="4005", rent_net=2000, rent_gross=2200)])
        upsert_listings(db, [_listing(source_id="4005", rent_net=2100, rent_gross=2350)])

        row = db.execute(
            select(Listing).where(Listing.source_id == "4005")
        ).scalar_one()
        history = db.execute(
            select(ListingHistory).where(ListingHistory.listing_id == row.id)
        ).scalars().all()

        changed_fields = {h.field_changed for h in history}
        assert "rent_net" in changed_fields
        assert "rent_gross" in changed_fields


# ── Deactivate missing ────────────────────────────────────────────────────────


class TestDeactivateMissing:
    def test_deactivates_listings_not_in_seen_ids(self, db):
        upsert_listings(db, [_listing(source_id="5001"), _listing(source_id="5002")])

        count = deactivate_missing(db, source="flatfox", seen_source_ids={"5001"})
        assert count == 1

        row = db.execute(
            select(Listing).where(Listing.source_id == "5002")
        ).scalar_one()
        assert row.is_active is False

    def test_active_listings_in_seen_ids_stay_active(self, db):
        upsert_listings(db, [_listing(source_id="5003")])
        deactivate_missing(db, source="flatfox", seen_source_ids={"5003"})

        row = db.execute(
            select(Listing).where(Listing.source_id == "5003")
        ).scalar_one()
        assert row.is_active is True

    def test_deactivated_listings_keep_their_data(self, db):
        upsert_listings(db, [_listing(source_id="5004", rent_net=1700)])
        deactivate_missing(db, source="flatfox", seen_source_ids=set())

        row = db.execute(
            select(Listing).where(Listing.source_id == "5004")
        ).scalar_one()
        assert row.rent_net == 1700  # Data preserved

    def test_deactivate_only_affects_given_source(self, db):
        upsert_listings(db, [
            _listing(source_id="5005", source="flatfox"),
            _listing(source_id="5005", source="homegate"),  # same source_id, different source
        ])
        deactivate_missing(db, source="flatfox", seen_source_ids=set())

        flatfox_row = db.execute(
            select(Listing).where(Listing.source == "flatfox", Listing.source_id == "5005")
        ).scalar_one()
        homegate_row = db.execute(
            select(Listing).where(Listing.source == "homegate", Listing.source_id == "5005")
        ).scalar_one()

        assert flatfox_row.is_active is False
        assert homegate_row.is_active is True  # unaffected

    def test_returns_count_of_deactivated(self, db):
        upsert_listings(db, [
            _listing(source_id="5006"),
            _listing(source_id="5007"),
            _listing(source_id="5008"),
        ])
        count = deactivate_missing(db, source="flatfox", seen_source_ids={"5006"})
        assert count == 2  # 5007 and 5008 deactivated
