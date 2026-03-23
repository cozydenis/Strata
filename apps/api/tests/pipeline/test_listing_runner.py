"""Tests for the listing pipeline runner."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from strata_api.db.base import Base
from strata_api.db.models.listing import Listing, ListingImage
from strata_api.pipeline.connectors.flatfox import FlatfoxListing
from strata_api.pipeline.listing_runner import run_listing_pipeline


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


def _make_flatfox_listing(
    source_id: str,
    plz: int = 8001,
    slug: str = "",
) -> FlatfoxListing:
    return FlatfoxListing(
        source="flatfox",
        source_id=source_id,
        slug=slug,
        rent_net=2000,
        rent_gross=2200,
        rooms=3.5,
        area_m2=80.0,
        address_raw="Teststrasse 1, 8001 Zürich",
        street="Teststrasse",
        house_number="1",
        plz=plz,
        city="Zürich",
        status="active",
        offer_type="RENT",
        source_url=f"https://flatfox.ch/en/flat/test/{source_id}/",
    )


# ── run_listing_pipeline ──────────────────────────────────────────────────────


class TestRunListingPipeline:
    @pytest.mark.asyncio
    async def test_pipeline_inserts_listings_from_flatfox(self, db):
        """Pipeline should fetch from Flatfox, insert listings, return stats."""
        listings = [_make_flatfox_listing("F-10001"), _make_flatfox_listing("F-10002")]

        with patch(
            "strata_api.pipeline.listing_runner.FlatfoxConnector"
        ) as MockConnector:
            mock_instance = MagicMock()
            mock_instance.fetch_all_zurich = AsyncMock(return_value=listings)
            MockConnector.return_value = mock_instance

            stats = await run_listing_pipeline(db)

        assert stats["flatfox"]["inserted"] == 2

    @pytest.mark.asyncio
    async def test_pipeline_deactivates_missing_flatfox_listings(self, db):
        """Listings from Flatfox not in the latest run should be deactivated."""
        # Pre-insert a listing that won't appear in the mock response
        from strata_api.pipeline.listing_loader import upsert_listings
        upsert_listings(db, [_make_flatfox_listing("F-OLD-99")])

        new_listings = [_make_flatfox_listing("F-20001")]

        with patch(
            "strata_api.pipeline.listing_runner.FlatfoxConnector"
        ) as MockConnector:
            mock_instance = MagicMock()
            mock_instance.fetch_all_zurich = AsyncMock(return_value=new_listings)
            MockConnector.return_value = mock_instance

            await run_listing_pipeline(db)

        old_row = db.execute(
            select(Listing).where(Listing.source_id == "F-OLD-99")
        ).scalar_one()
        assert old_row.is_active is False

    @pytest.mark.asyncio
    async def test_pipeline_returns_stats_with_all_sources(self, db):
        """Stats dict should include entries for each source."""
        with patch(
            "strata_api.pipeline.listing_runner.FlatfoxConnector"
        ) as MockFlatfox:
            mock_ff = MagicMock()
            mock_ff.fetch_all_zurich = AsyncMock(return_value=[])
            MockFlatfox.return_value = mock_ff

            stats = await run_listing_pipeline(db)

        assert "flatfox" in stats

    @pytest.mark.asyncio
    async def test_pipeline_handles_empty_connector_response(self, db):
        """Empty connector response should produce zero insertions."""
        with patch(
            "strata_api.pipeline.listing_runner.FlatfoxConnector"
        ) as MockConnector:
            mock_instance = MagicMock()
            mock_instance.fetch_all_zurich = AsyncMock(return_value=[])
            MockConnector.return_value = mock_instance

            stats = await run_listing_pipeline(db)

        assert stats["flatfox"]["inserted"] == 0


class TestSecondPipelineRun:
    """Tests for second-run behaviour: updates, deactivation, history tracking."""

    @pytest.mark.asyncio
    async def test_second_run_detects_price_change(self, db):
        """If rent_net changes between runs, listing_history should log it."""
        listing_v1 = _make_flatfox_listing("F-PRICE-1", plz=8001)
        listing_v2 = _make_flatfox_listing("F-PRICE-1", plz=8001)
        # Simulate price increase
        listing_v2 = listing_v2.model_copy(update={"rent_net": 2500})

        with patch(
            "strata_api.pipeline.listing_runner.FlatfoxConnector"
        ) as MockConnector:
            mock = MagicMock()
            mock.fetch_all_zurich = AsyncMock(return_value=[listing_v1])
            MockConnector.return_value = mock
            await run_listing_pipeline(db)

        with patch(
            "strata_api.pipeline.listing_runner.FlatfoxConnector"
        ) as MockConnector:
            mock = MagicMock()
            mock.fetch_all_zurich = AsyncMock(return_value=[listing_v2])
            MockConnector.return_value = mock
            stats = await run_listing_pipeline(db)

        assert stats["flatfox"]["updated"] == 1

        from strata_api.db.models.listing import Listing, ListingHistory
        row = db.execute(
            select(Listing).where(Listing.source_id == "F-PRICE-1")
        ).scalar_one()
        assert row.rent_net == 2500

        history = db.execute(
            select(ListingHistory).where(
                ListingHistory.listing_id == row.id,
                ListingHistory.field_changed == "rent_net",
            )
        ).scalars().all()
        assert len(history) == 1
        assert history[0].old_value == "2000"
        assert history[0].new_value == "2500"

    @pytest.mark.asyncio
    async def test_second_run_deactivates_gone_listings(self, db):
        """Listings present in run 1 but absent in run 2 get is_active=False."""
        listing_a = _make_flatfox_listing("F-GONE-A", plz=8001)
        listing_b = _make_flatfox_listing("F-GONE-B", plz=8001)

        with patch(
            "strata_api.pipeline.listing_runner.FlatfoxConnector"
        ) as MockConnector:
            mock = MagicMock()
            mock.fetch_all_zurich = AsyncMock(return_value=[listing_a, listing_b])
            MockConnector.return_value = mock
            await run_listing_pipeline(db)

        # Second run: only listing_a is still present
        with patch(
            "strata_api.pipeline.listing_runner.FlatfoxConnector"
        ) as MockConnector:
            mock = MagicMock()
            mock.fetch_all_zurich = AsyncMock(return_value=[listing_a])
            MockConnector.return_value = mock
            stats = await run_listing_pipeline(db)

        assert stats["flatfox"]["deactivated"] == 1

        from strata_api.db.models.listing import Listing
        row_b = db.execute(
            select(Listing).where(Listing.source_id == "F-GONE-B")
        ).scalar_one()
        assert row_b.is_active is False

        row_a = db.execute(
            select(Listing).where(Listing.source_id == "F-GONE-A")
        ).scalar_one()
        assert row_a.is_active is True

    @pytest.mark.asyncio
    async def test_second_run_unchanged_listing(self, db):
        """Identical listings across two runs → unchanged count, no history."""
        listing = _make_flatfox_listing("F-SAME-1", plz=8001)

        with patch(
            "strata_api.pipeline.listing_runner.FlatfoxConnector"
        ) as MockConnector:
            mock = MagicMock()
            mock.fetch_all_zurich = AsyncMock(return_value=[listing])
            MockConnector.return_value = mock
            await run_listing_pipeline(db)

        with patch(
            "strata_api.pipeline.listing_runner.FlatfoxConnector"
        ) as MockConnector:
            mock = MagicMock()
            mock.fetch_all_zurich = AsyncMock(return_value=[listing])
            MockConnector.return_value = mock
            stats = await run_listing_pipeline(db)

        assert stats["flatfox"]["unchanged"] == 1
        assert stats["flatfox"]["inserted"] == 0

        from strata_api.db.models.listing import Listing, ListingHistory
        row = db.execute(
            select(Listing).where(Listing.source_id == "F-SAME-1")
        ).scalar_one()
        history = db.execute(
            select(ListingHistory).where(ListingHistory.listing_id == row.id)
        ).scalars().all()
        assert history == []


class TestMediaDownloadInRunner:
    """Tests for the photo + floor plan download step in run_listing_pipeline."""

    @pytest.mark.asyncio
    async def test_stats_include_media_keys(self, db, tmp_path):
        """Stats dict should include photos_saved and floorplans_saved keys."""
        listings = [_make_flatfox_listing("100001", slug="test-8001")]

        with patch("strata_api.pipeline.listing_runner.FlatfoxConnector") as MockConnector, \
             patch("strata_api.pipeline.listing_runner.scrape_listing_media") as mock_scrape, \
             patch("strata_api.pipeline.listing_runner.save_listing_media") as mock_save:

            mock_instance = MagicMock()
            mock_instance.fetch_all_zurich = AsyncMock(return_value=listings)
            MockConnector.return_value = mock_instance
            mock_scrape.return_value = {"photos": [], "floorplans": []}
            mock_save.return_value = {"photos_saved": 0, "floorplans_saved": 0}

            stats = await run_listing_pipeline(db, media_dir=tmp_path)

        assert "photos_saved" in stats["flatfox"]
        assert "floorplans_saved" in stats["flatfox"]

    @pytest.mark.asyncio
    async def test_media_scraped_for_new_listings_with_slug(self, db, tmp_path):
        """scrape_listing_media is called for new listings that have a slug."""
        listings = [_make_flatfox_listing("200002", slug="test-slug-8001")]

        with patch("strata_api.pipeline.listing_runner.FlatfoxConnector") as MockConnector, \
             patch("strata_api.pipeline.listing_runner.scrape_listing_media") as mock_scrape, \
             patch("strata_api.pipeline.listing_runner.save_listing_media") as mock_save:

            mock_instance = MagicMock()
            mock_instance.fetch_all_zurich = AsyncMock(return_value=listings)
            MockConnector.return_value = mock_instance
            mock_scrape.return_value = {"photos": [], "floorplans": []}
            mock_save.return_value = {"photos_saved": 0, "floorplans_saved": 0}

            await run_listing_pipeline(db, media_dir=tmp_path)

        mock_scrape.assert_called_once_with("test-slug-8001", 200002)

    @pytest.mark.asyncio
    async def test_media_not_scraped_for_listings_without_slug(self, db, tmp_path):
        """Listings with no slug should be skipped for media scraping."""
        listings = [_make_flatfox_listing("F-NOSLUG-1", slug="")]

        with patch("strata_api.pipeline.listing_runner.FlatfoxConnector") as MockConnector, \
             patch("strata_api.pipeline.listing_runner.scrape_listing_media") as mock_scrape:

            mock_instance = MagicMock()
            mock_instance.fetch_all_zurich = AsyncMock(return_value=listings)
            MockConnector.return_value = mock_instance

            await run_listing_pipeline(db, media_dir=tmp_path)

        mock_scrape.assert_not_called()

    @pytest.mark.asyncio
    async def test_media_not_re_scraped_on_second_run(self, db, tmp_path):
        """Listings that already have images should not trigger another scrape."""
        import datetime
        # Pre-insert listing with an existing image
        existing = Listing(
            source="flatfox",
            source_id="F-HAS-IMG-1",
            first_seen=datetime.datetime.utcnow(),
            last_seen=datetime.datetime.utcnow(),
            is_active=True,
        )
        db.add(existing)
        db.flush()
        db.add(ListingImage(
            listing_id=existing.id,
            url="https://flatfox.ch/existing.jpg",
            image_type="photo",
            ordering=0,
        ))
        db.flush()

        listings = [_make_flatfox_listing("F-HAS-IMG-1", slug="test-slug")]

        with patch("strata_api.pipeline.listing_runner.FlatfoxConnector") as MockConnector, \
             patch("strata_api.pipeline.listing_runner.scrape_listing_media") as mock_scrape:

            mock_instance = MagicMock()
            mock_instance.fetch_all_zurich = AsyncMock(return_value=listings)
            MockConnector.return_value = mock_instance

            await run_listing_pipeline(db, media_dir=tmp_path)

        mock_scrape.assert_not_called()

    @pytest.mark.asyncio
    async def test_photos_saved_count_in_stats(self, db, tmp_path):
        """photos_saved stat reflects actual images scraped."""
        listings = [_make_flatfox_listing("300001", slug="test-8001")]

        with patch("strata_api.pipeline.listing_runner.FlatfoxConnector") as MockConnector, \
             patch("strata_api.pipeline.listing_runner.scrape_listing_media") as mock_scrape, \
             patch("strata_api.pipeline.listing_runner.save_listing_media") as mock_save:

            mock_instance = MagicMock()
            mock_instance.fetch_all_zurich = AsyncMock(return_value=listings)
            MockConnector.return_value = mock_instance
            mock_scrape.return_value = {"photos": ["u1", "u2"], "floorplans": ["fp1"]}
            mock_save.return_value = {"photos_saved": 2, "floorplans_saved": 1}

            stats = await run_listing_pipeline(db, media_dir=tmp_path)

        assert stats["flatfox"]["photos_saved"] == 2
        assert stats["flatfox"]["floorplans_saved"] == 1
