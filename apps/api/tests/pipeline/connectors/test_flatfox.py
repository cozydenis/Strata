"""Tests for Flatfox API connector (TDD — RED phase)."""
import json
from pathlib import Path

import pytest

from strata_api.pipeline.connectors.flatfox import (
    FlatfoxConnector,
    FlatfoxListing,
    parse_flatfox_listing,
)

SAMPLES_DIR = Path(__file__).resolve().parents[3] / "data" / "samples"


@pytest.fixture
def sample_listing() -> dict:
    """Real listing object from the Flatfox public API."""
    data = json.loads((SAMPLES_DIR / "flatfox_search.json").read_text())
    return data["results"][0]


@pytest.fixture
def zurich_listing() -> dict:
    return {
        "pk": 100001,
        "slug": "bahnhofstrasse-8001-zurich",
        "status": "act",
        "offer_type": "RENT",
        "object_category": "APARTMENT",
        "object_type": "APARTMENT",
        "rent_net": 2200,
        "rent_charges": 200,
        "rent_gross": 2400,
        "number_of_rooms": 3.5,
        "surface_living": 85.0,
        "street": "Bahnhofstrasse 10",
        "zipcode": 8001,
        "city": "Zürich",
        "public_address": "Bahnhofstrasse 10, 8001 Zürich",
        "latitude": 47.376,
        "longitude": 8.541,
        "published": "2024-01-15T09:30:00+01:00",
        "description": "Beautiful apartment in Zürich with lake view.",
        "images": [5001, 5002, 5003],
        "cover_image": 5001,
        "documents": [9001],
        "agency": {"name": "Muster AG"},
    }


# ── parse_flatfox_listing ─────────────────────────────────────────────────────


class TestParseFlatfoxListing:
    def test_basic_fields(self, zurich_listing):
        result = parse_flatfox_listing(zurich_listing)
        assert result.source == "flatfox"
        assert result.source_id == "100001"
        assert result.rent_net == 2200
        assert result.rent_charges == 200
        assert result.rent_gross == 2400
        assert result.rooms == 3.5
        assert result.area_m2 == 85.0
        assert result.plz == 8001
        assert result.city == "Zürich"
        assert result.lat == pytest.approx(47.376)
        assert result.lng == pytest.approx(8.541)

    def test_street_and_house_number_split(self, zurich_listing):
        """Street field like 'Bahnhofstrasse 10' should be split."""
        result = parse_flatfox_listing(zurich_listing)
        assert result.street == "Bahnhofstrasse"
        assert result.house_number == "10"

    def test_street_no_number(self):
        listing = {
            "pk": 2, "slug": "x", "status": "act", "offer_type": "RENT",
            "object_category": "APARTMENT",
            "street": "Musterstrasse",
            "zipcode": 8001, "city": "Zürich",
            "public_address": "Musterstrasse, 8001 Zürich",
        }
        result = parse_flatfox_listing(listing)
        assert result.street == "Musterstrasse"
        assert result.house_number is None

    def test_compound_house_number_slash(self):
        """'Hinterbergstrasse 108/110' → street='Hinterbergstrasse', number='108/110'."""
        listing = {
            "pk": 50, "slug": "x", "status": "act", "offer_type": "RENT",
            "object_category": "APARTMENT",
            "street": "Hinterbergstrasse 108/110",
            "zipcode": 8044, "city": "Zürich",
            "public_address": "Hinterbergstrasse 108/110, 8044 Zürich",
        }
        result = parse_flatfox_listing(listing)
        assert result.street == "Hinterbergstrasse"
        assert result.house_number == "108/110"

    def test_compound_house_number_with_letter(self):
        """'Seefeldstrasse 30/30a' → street='Seefeldstrasse', number='30/30a'."""
        listing = {
            "pk": 51, "slug": "x", "status": "act", "offer_type": "RENT",
            "object_category": "APARTMENT",
            "street": "Seefeldstrasse 30/30a",
            "zipcode": 8008, "city": "Zürich",
            "public_address": "Seefeldstrasse 30/30a, 8008 Zürich",
        }
        result = parse_flatfox_listing(listing)
        assert result.street == "Seefeldstrasse"
        assert result.house_number == "30/30a"

    def test_range_house_number_dash(self):
        """'Im Feld 10 - 24' → street='Im Feld', number='10-24'."""
        listing = {
            "pk": 52, "slug": "x", "status": "act", "offer_type": "RENT",
            "object_category": "APARTMENT",
            "street": "Im Feld 10 - 24",
            "zipcode": 8180, "city": "Bülach",
            "public_address": "Im Feld 10 - 24, 8180 Bülach",
        }
        result = parse_flatfox_listing(listing)
        assert result.street == "Im Feld"
        assert result.house_number == "10-24"

    def test_ung_prefix_stripped(self):
        """'UNG Feldeggstrasse 5' → prefix stripped, street='Feldeggstrasse', number='5'."""
        listing = {
            "pk": 53, "slug": "x", "status": "act", "offer_type": "RENT",
            "object_category": "APARTMENT",
            "street": "UNG Feldeggstrasse 5",
            "zipcode": 8008, "city": "Zürich",
            "public_address": "UNG Feldeggstrasse 5, 8008 Zürich",
        }
        result = parse_flatfox_listing(listing)
        assert result.street == "Feldeggstrasse"
        assert result.house_number == "5"

    def test_eh_suffix_stripped(self):
        """'Seestrasse 30, EH' → suffix removed, street='Seestrasse', number='30'."""
        listing = {
            "pk": 54, "slug": "x", "status": "act", "offer_type": "RENT",
            "object_category": "APARTMENT",
            "street": "Seestrasse 30, EH",
            "zipcode": 8002, "city": "Zürich",
            "public_address": "Seestrasse 30, EH, 8002 Zürich",
        }
        result = parse_flatfox_listing(listing)
        assert result.street == "Seestrasse"
        assert result.house_number == "30"

    def test_im_hof_range_with_slash(self):
        """'Im Hof 9/11' → street='Im Hof', number='9/11'."""
        listing = {
            "pk": 55, "slug": "x", "status": "act", "offer_type": "RENT",
            "object_category": "APARTMENT",
            "street": "Im Hof 9/11",
            "zipcode": 8355, "city": "Aadorf",
            "public_address": "Im Hof 9/11, 8355 Aadorf",
        }
        result = parse_flatfox_listing(listing)
        assert result.street == "Im Hof"
        assert result.house_number == "9/11"

    def test_status_mapping_act(self, zurich_listing):
        result = parse_flatfox_listing(zurich_listing)
        assert result.status == "active"

    def test_source_url_constructed(self, zurich_listing):
        result = parse_flatfox_listing(zurich_listing)
        assert "flatfox.ch" in result.source_url
        assert "100001" in result.source_url

    def test_address_raw_populated(self, zurich_listing):
        result = parse_flatfox_listing(zurich_listing)
        assert result.address_raw == "Bahnhofstrasse 10, 8001 Zürich"

    def test_description_extracted(self, zurich_listing):
        result = parse_flatfox_listing(zurich_listing)
        assert result.description == "Beautiful apartment in Zürich with lake view."

    def test_image_ids_extracted(self, zurich_listing):
        result = parse_flatfox_listing(zurich_listing)
        assert result.image_ids == [5001, 5002, 5003]

    def test_cover_image_id_extracted(self, zurich_listing):
        result = parse_flatfox_listing(zurich_listing)
        assert result.cover_image_id == 5001

    def test_document_ids_extracted(self, zurich_listing):
        result = parse_flatfox_listing(zurich_listing)
        assert result.document_ids == [9001]

    def test_slug_extracted(self, zurich_listing):
        result = parse_flatfox_listing(zurich_listing)
        assert result.slug == "bahnhofstrasse-8001-zurich"

    def test_slug_defaults_to_empty_string_when_missing(self):
        listing = {
            "pk": 42, "status": "act", "offer_type": "RENT",
            "object_category": "APARTMENT",
            "zipcode": 8001, "city": "Zürich",
            "public_address": "8001 Zürich",
        }
        result = parse_flatfox_listing(listing)
        assert result.slug == ""

    def test_missing_media_fields_default_empty(self):
        listing = {
            "pk": 99, "slug": "x", "status": "act", "offer_type": "RENT",
            "object_category": "APARTMENT",
            "street": "Test 1", "zipcode": 8001, "city": "Zürich",
            "public_address": "Test 1, 8001 Zürich",
        }
        result = parse_flatfox_listing(listing)
        assert result.description is None
        assert result.image_ids == []
        assert result.cover_image_id is None
        assert result.document_ids == []

    def test_nullable_fields_when_missing(self):
        listing = {
            "pk": 3, "slug": "x", "status": "act", "offer_type": "RENT",
            "object_category": "APARTMENT",
            "street": "Bergweg 1",
            "zipcode": 8004, "city": "Zürich",
            "public_address": "Bergweg 1, 8004 Zürich",
            "rent_net": None, "rent_gross": None, "rent_charges": None,
            "number_of_rooms": None, "surface_living": None,
            "latitude": None, "longitude": None,
        }
        result = parse_flatfox_listing(listing)
        assert result.rent_net is None
        assert result.rooms is None
        assert result.lat is None

    def test_real_sample_parses(self, sample_listing):
        result = parse_flatfox_listing(sample_listing)
        assert result.source == "flatfox"
        assert result.source_id is not None
        assert result.plz is not None


# ── FlatfoxListing Pydantic schema ────────────────────────────────────────────


class TestFlatfoxListingSchema:
    def test_is_zurich_area_true(self):
        listing = FlatfoxListing(
            source="flatfox", source_id="1",
            address_raw="X", street="X", plz=8001, city="Zürich",
            offer_type="RENT", status="active",
        )
        assert listing.is_zurich_area is True

    def test_is_zurich_area_false_outside(self):
        listing = FlatfoxListing(
            source="flatfox", source_id="2",
            address_raw="X", street="X", plz=5600, city="Lenzburg",
            offer_type="RENT", status="active",
        )
        assert listing.is_zurich_area is False

    def test_is_zurich_area_false_boundary_8999(self):
        """8999 is NOT in Kanton Zürich — PLZ whitelist rejects it."""
        listing = FlatfoxListing(
            source="flatfox", source_id="3",
            address_raw="X", street="X", plz=8999, city="Somewhere",
            offer_type="RENT", status="active",
        )
        assert listing.is_zurich_area is False

    def test_is_zurich_area_false_thurgau_8570(self):
        """8570 Weinfelden is Thurgau — should be excluded by GWR whitelist."""
        from strata_api.pipeline.connectors.flatfox import ZURICH_PLZS
        assert 8570 not in ZURICH_PLZS  # Weinfelden, TG

    def test_is_zurich_area_false_stgallen_8640(self):
        """8640 Rapperswil-Jona is St.Gallen — should be excluded by GWR whitelist."""
        from strata_api.pipeline.connectors.flatfox import ZURICH_PLZS
        assert 8640 not in ZURICH_PLZS  # Rapperswil SG

    def test_zurich_plzs_includes_winterthur(self):
        """8400 Winterthur should be in the whitelist."""
        from strata_api.pipeline.connectors.flatfox import ZURICH_PLZS
        assert 8400 in ZURICH_PLZS

    def test_zurich_plzs_includes_zurich_city(self):
        """8001–8099 Stadt Zürich PLZs should be in the whitelist."""
        from strata_api.pipeline.connectors.flatfox import ZURICH_PLZS
        assert 8001 in ZURICH_PLZS
        assert 8050 in ZURICH_PLZS

    def test_is_residential_true_for_apartment(self):
        listing = FlatfoxListing(
            source="flatfox", source_id="1", plz=8001,
            object_type="APARTMENT", offer_type="RENT", status="active",
        )
        assert listing.is_residential is True

    def test_is_residential_true_for_house(self):
        listing = FlatfoxListing(
            source="flatfox", source_id="2", plz=8001,
            object_type="HOUSE", offer_type="RENT", status="active",
        )
        assert listing.is_residential is True

    def test_is_residential_true_for_shared(self):
        listing = FlatfoxListing(
            source="flatfox", source_id="3", plz=8001,
            object_type="SHARED", offer_type="RENT", status="active",
        )
        assert listing.is_residential is True

    def test_is_residential_false_for_park(self):
        listing = FlatfoxListing(
            source="flatfox", source_id="4", plz=8001,
            object_type="PARK", offer_type="RENT", status="active",
        )
        assert listing.is_residential is False

    def test_is_residential_false_for_industry(self):
        listing = FlatfoxListing(
            source="flatfox", source_id="5", plz=8001,
            object_type="INDUSTRY", offer_type="RENT", status="active",
        )
        assert listing.is_residential is False

    def test_is_residential_true_when_object_type_none(self):
        """When object_type is missing, assume residential (don't discard)."""
        listing = FlatfoxListing(
            source="flatfox", source_id="6", plz=8001,
            object_type=None, offer_type="RENT", status="active",
        )
        assert listing.is_residential is True


# ── FlatfoxConnector ──────────────────────────────────────────────────────────


class TestFlatfoxConnector:
    def test_build_page_url(self):
        connector = FlatfoxConnector()
        url = connector._page_url(offset=0, limit=96)
        assert "flatfox.ch/api/v1/public-listing/" in url
        assert "limit=96" in url
        assert "offset=0" in url

    @pytest.mark.asyncio
    async def test_fetch_page_returns_listings(self):
        mock_response = {
            "count": 33698,
            "next": "https://flatfox.ch/api/v1/public-listing/?limit=2&offset=2",
            "previous": None,
            "results": [
                {
                    "pk": 200001,
                    "slug": "seestrasse-8002-zurich",
                    "status": "act",
                    "offer_type": "RENT",
                    "object_category": "APARTMENT",
                    "street": "Seestrasse 5",
                    "zipcode": 8002,
                    "city": "Zürich",
                    "public_address": "Seestrasse 5, 8002 Zürich",
                    "rent_net": 2500,
                    "rent_charges": 250,
                    "rent_gross": 2750,
                    "number_of_rooms": 4.5,
                    "surface_living": 100.0,
                    "latitude": 47.35,
                    "longitude": 8.54,
                    "published": "2024-02-01T10:00:00+01:00",
                },
            ],
        }

        async def fake_fetch(url: str) -> dict:
            return mock_response

        connector = FlatfoxConnector()
        connector._fetch_json = fake_fetch

        listings, has_more = await connector.fetch_page(offset=0, limit=2)
        assert len(listings) == 1
        assert listings[0].source_id == "200001"
        assert has_more is True

    @pytest.mark.asyncio
    async def test_fetch_page_no_more_when_no_next(self):
        mock_response = {
            "count": 1,
            "next": None,
            "previous": None,
            "results": [
                {
                    "pk": 300001,
                    "slug": "langstrasse-8004-zurich",
                    "status": "act",
                    "offer_type": "RENT",
                    "object_category": "APARTMENT",
                    "street": "Langstrasse 99",
                    "zipcode": 8004,
                    "city": "Zürich",
                    "public_address": "Langstrasse 99, 8004 Zürich",
                }
            ],
        }

        async def fake_fetch(url: str) -> dict:
            return mock_response

        connector = FlatfoxConnector()
        connector._fetch_json = fake_fetch

        _, has_more = await connector.fetch_page(offset=0, limit=96)
        assert has_more is False

    @pytest.mark.asyncio
    async def test_filters_non_zurich_results(self):
        mock_response = {
            "count": 3,
            "next": None,
            "previous": None,
            "results": [
                {
                    "pk": 1, "slug": "x", "status": "act", "offer_type": "RENT",
                    "object_category": "APARTMENT",
                    "street": "Seestr. 1", "zipcode": 8001, "city": "Zürich",
                    "public_address": "Seestr. 1, 8001 Zürich",
                },
                {
                    "pk": 2, "slug": "y", "status": "act", "offer_type": "RENT",
                    "object_category": "APARTMENT",
                    "street": "Main St 5", "zipcode": 3000, "city": "Bern",
                    "public_address": "Main St 5, 3000 Bern",
                },
                {
                    "pk": 3, "slug": "z", "status": "act", "offer_type": "RENT",
                    "object_category": "APARTMENT",
                    "street": "Bergstr. 7", "zipcode": 8400, "city": "Winterthur",
                    "public_address": "Bergstr. 7, 8400 Winterthur",
                },
            ],
        }

        async def fake_fetch(url: str) -> dict:
            return mock_response

        connector = FlatfoxConnector()
        connector._fetch_json = fake_fetch

        listings, _ = await connector.fetch_page(offset=0, limit=96)
        # Only Zürich (8001) and Winterthur (8400) should pass
        assert len(listings) == 2
        plzs = {listing.plz for listing in listings}
        assert 3000 not in plzs  # Bern excluded

    @pytest.mark.asyncio
    async def test_filters_non_residential_results(self):
        mock_response = {
            "count": 4,
            "next": None,
            "previous": None,
            "results": [
                {
                    "pk": 10, "slug": "x", "status": "act", "offer_type": "RENT",
                    "object_category": "APARTMENT",
                    "street": "Seestr. 1", "zipcode": 8001, "city": "Zürich",
                    "public_address": "Seestr. 1, 8001 Zürich",
                },
                {
                    "pk": 11, "slug": "y", "status": "act", "offer_type": "RENT",
                    "object_category": "PARK",
                    "street": "Parkhaus 1", "zipcode": 8001, "city": "Zürich",
                    "public_address": "Parkhaus 1, 8001 Zürich",
                },
                {
                    "pk": 12, "slug": "z", "status": "act", "offer_type": "RENT",
                    "object_category": "INDUSTRY",
                    "street": "Lager 5", "zipcode": 8001, "city": "Zürich",
                    "public_address": "Lager 5, 8001 Zürich",
                },
                {
                    "pk": 13, "slug": "w", "status": "act", "offer_type": "RENT",
                    "object_category": "SHARED",
                    "street": "WG-Zimmer 3", "zipcode": 8004, "city": "Zürich",
                    "public_address": "WG-Zimmer 3, 8004 Zürich",
                },
            ],
        }

        async def fake_fetch(url: str) -> dict:
            return mock_response

        connector = FlatfoxConnector()
        connector._fetch_json = fake_fetch

        listings, _ = await connector.fetch_page(offset=0, limit=96)
        # APARTMENT and SHARED pass, PARK and INDUSTRY excluded
        assert len(listings) == 2
        types = {listing.object_type for listing in listings}
        assert "APARTMENT" in types
        assert "SHARED" in types
        assert "PARK" not in types
        assert "INDUSTRY" not in types
