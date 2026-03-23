"""Tests for Homegate scraper connector (TDD — RED phase)."""
import json
from pathlib import Path

import pytest

from strata_api.pipeline.connectors.homegate import (
    HomegateConnector,
    HomogateListing,
    extract_initial_state,
    parse_homegate_listing,
)

SAMPLES_DIR = Path(__file__).resolve().parents[3] / "data" / "samples"


@pytest.fixture
def sample_state() -> dict:
    """Synthetic __INITIAL_STATE__ from our recon notes."""
    return json.loads((SAMPLES_DIR / "homegate_search.json").read_text())


@pytest.fixture
def raw_listing() -> dict:
    """A single raw listing object from __INITIAL_STATE__."""
    state = json.loads((SAMPLES_DIR / "homegate_search.json").read_text())
    return state["resultList"]["search"]["fullSearch"]["result"]["listings"][0]


@pytest.fixture
def minimal_listing() -> dict:
    return {
        "id": "4009876543",
        "listing": {
            "address": {
                "street": "Langstrasse 100",
                "postalCode": "8004",
                "locality": "Zürich",
                "geoCoordinates": {"latitude": 47.378, "longitude": 8.531},
            },
            "characteristics": {"numberOfRooms": 2.5, "livingSpace": 60},
            "prices": {"rent": {"net": 1750, "gross": 1950, "extra": 200}, "currency": "CHF"},
            "offerType": "RENT",
        },
        "meta": {"createdAt": "2024-03-01T12:00:00Z"},
    }


# ── extract_initial_state ─────────────────────────────────────────────────────


class TestExtractInitialState:
    def test_extracts_from_html(self):
        payload = json.dumps({"resultList": {"search": {"fullSearch": {"result": {"listings": []}}}}})
        html = f"<html><head></head><body><script>window.__INITIAL_STATE__ = {payload};</script></body></html>"
        result = extract_initial_state(html)
        assert result is not None
        assert "resultList" in result

    def test_returns_none_when_missing(self):
        html = "<html><body>No state here</body></html>"
        result = extract_initial_state(html)
        assert result is None

    def test_handles_whitespace_variants(self):
        payload = json.dumps({"resultList": {}})
        html = f"<script>window.__INITIAL_STATE__={payload}</script>"
        result = extract_initial_state(html)
        assert result is not None

    def test_extracts_listings_from_sample(self, sample_state):
        """Sample JSON should have the correct nested structure."""
        result = sample_state.get("resultList", {})
        listings = (
            result.get("search", {})
            .get("fullSearch", {})
            .get("result", {})
            .get("listings", [])
        )
        assert len(listings) >= 1


# ── parse_homegate_listing ────────────────────────────────────────────────────


class TestParseHomegateListng:
    def test_basic_fields(self, minimal_listing):
        result = parse_homegate_listing(minimal_listing)
        assert result.source == "homegate"
        assert result.source_id == "4009876543"
        assert result.rent_net == 1750
        assert result.rent_gross == 1950
        assert result.rent_charges == 200
        assert result.rooms == 2.5
        assert result.area_m2 == 60
        assert result.plz == 8004
        assert result.city == "Zürich"
        assert result.lat == pytest.approx(47.378)
        assert result.lng == pytest.approx(8.531)

    def test_street_and_house_number_split(self, minimal_listing):
        result = parse_homegate_listing(minimal_listing)
        assert result.street == "Langstrasse"
        assert result.house_number == "100"

    def test_offer_type(self, minimal_listing):
        result = parse_homegate_listing(minimal_listing)
        assert result.offer_type == "RENT"

    def test_source_url_constructed(self, minimal_listing):
        result = parse_homegate_listing(minimal_listing)
        assert "homegate.ch" in result.source_url
        assert "4009876543" in result.source_url

    def test_nullable_coords_when_missing(self):
        listing = {
            "id": "999",
            "listing": {
                "address": {
                    "street": "Bergweg 5",
                    "postalCode": "8008",
                    "locality": "Zürich",
                    # no geoCoordinates
                },
                "offerType": "RENT",
            },
        }
        result = parse_homegate_listing(listing)
        assert result.lat is None
        assert result.lng is None

    def test_nullable_prices_when_missing(self):
        listing = {
            "id": "888",
            "listing": {
                "address": {"street": "X", "postalCode": "8001", "locality": "Zürich"},
                "offerType": "RENT",
                # no prices block
            },
        }
        result = parse_homegate_listing(listing)
        assert result.rent_net is None
        assert result.rent_gross is None

    def test_real_sample_parses(self, raw_listing):
        result = parse_homegate_listing(raw_listing)
        assert result.source == "homegate"
        assert result.source_id is not None
        assert result.plz is not None


# ── HomogateListing schema ────────────────────────────────────────────────────


class TestHomogateListingSchema:
    def test_is_zurich_area_true(self):
        listing = HomogateListing(
            source="homegate", source_id="1",
            address_raw="X", street="X", plz=8001, city="Zürich",
            offer_type="RENT", status="active",
        )
        assert listing.is_zurich_area is True

    def test_is_zurich_area_false(self):
        listing = HomogateListing(
            source="homegate", source_id="2",
            address_raw="X", street="X", plz=3000, city="Bern",
            offer_type="RENT", status="active",
        )
        assert listing.is_zurich_area is False


# ── HomegateConnector ─────────────────────────────────────────────────────────


class TestHomegateConnector:
    def test_build_page_url(self):
        connector = HomegateConnector()
        url = connector._page_url(page=1)
        assert "homegate.ch" in url
        assert "ep=1" in url or "ep=1" in url

    def test_build_page_url_page_2(self):
        connector = HomegateConnector()
        url = connector._page_url(page=2)
        assert "ep=2" in url

    @pytest.mark.asyncio
    async def test_parse_page_html(self):
        """parse_page should extract listings from valid HTML."""
        listings_data = [
            {
                "id": "5001",
                "listing": {
                    "address": {
                        "street": "Seefeldstrasse 15",
                        "postalCode": "8008",
                        "locality": "Zürich",
                    },
                    "characteristics": {"numberOfRooms": 3.5, "livingSpace": 85},
                    "prices": {"rent": {"net": 2800, "gross": 3100, "extra": 300}},
                    "offerType": "RENT",
                },
                "meta": {"createdAt": "2024-04-01T08:00:00Z"},
            }
        ]
        state_json = json.dumps({
            "resultList": {
                "search": {
                    "fullSearch": {
                        "result": {
                            "listings": listings_data,
                            "totalCount": 1,
                            "pageCount": 1,
                        }
                    }
                }
            }
        })
        html = f"<html><script>window.__INITIAL_STATE__ = {state_json};</script></html>"

        connector = HomegateConnector()
        listings, total_pages = connector.parse_page(html)
        assert len(listings) == 1
        assert listings[0].source_id == "5001"
        assert total_pages == 1

    @pytest.mark.asyncio
    async def test_parse_page_returns_empty_on_missing_state(self):
        connector = HomegateConnector()
        listings, total_pages = connector.parse_page("<html>no state</html>")
        assert listings == []
        assert total_pages == 0
