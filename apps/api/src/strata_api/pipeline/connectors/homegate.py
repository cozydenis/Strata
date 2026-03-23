"""Homegate scraper connector — extracts rental listings from __INITIAL_STATE__ JSON."""
from __future__ import annotations

import json
import re
from typing import Any

from pydantic import BaseModel, computed_field

from strata_api.pipeline.connectors.flatfox import ZURICH_PLZS

_BASE_URL = "https://www.homegate.ch/rent/real-estate/city-zurich/matching-list"

# Matches: window.__INITIAL_STATE__ = {...};  (whitespace-tolerant, no semicolon required)
_INITIAL_STATE_RE = re.compile(
    r"window\.__INITIAL_STATE__\s*=\s*(\{.*?\})(?:\s*;|(?=\s*</script>))",
    re.DOTALL,
)

# Matches street + house number, including compound forms (108/110, 30/30a, 10-24)
_STREET_NUM_RE = re.compile(
    r"^(.*?)[\s,]+(\d[\w]*(?:\s*[-/]\s*\d[\w]*)*)$"
)

# Strip parking/basement prefixes/suffixes before parsing
_STRIP_PREFIX_RE = re.compile(r"^(?:UNG|TG|EKZ)\s+", re.I)
_STRIP_SUFFIX_RE = re.compile(r",\s*(?:EH|TG|UNG|Einstellhalle|Tiefgarage)\s*$", re.I)


def extract_initial_state(html: str) -> dict | None:
    """Extract the ``window.__INITIAL_STATE__`` JSON object from Homegate HTML."""
    m = _INITIAL_STATE_RE.search(html)
    if m is None:
        return None
    try:
        return json.loads(m.group(1))
    except json.JSONDecodeError:
        return None


def _split_street(raw: str | None) -> tuple[str | None, str | None]:
    """Split 'Birchlenstrasse 37' → ('Birchlenstrasse', '37').

    Handles compound house numbers (108/110, 30/30a, 10 - 24)
    and strips parking/basement prefixes (UNG, EH, TG, EKZ).
    """
    if not raw:
        return None, None
    s = raw.strip()
    s = _STRIP_PREFIX_RE.sub("", s)
    s = _STRIP_SUFFIX_RE.sub("", s)
    s = s.strip()
    m = _STREET_NUM_RE.match(s)
    if m:
        street = m.group(1).strip()
        number = re.sub(r"\s+", "", m.group(2))
        return street, number
    return s, None


class HomogateListing(BaseModel):
    """Parsed listing from Homegate, ready for DB upsert."""

    source: str = "homegate"
    source_id: str
    rent_net: int | None = None
    rent_gross: int | None = None
    rent_charges: int | None = None
    rooms: float | None = None
    area_m2: float | None = None
    address_raw: str | None = None
    street: str | None = None
    house_number: str | None = None
    plz: int | None = None
    city: str | None = None
    lat: float | None = None
    lng: float | None = None
    object_type: str | None = None
    offer_type: str | None = None
    status: str = "active"
    source_url: str | None = None

    @computed_field  # type: ignore[misc]
    @property
    def is_zurich_area(self) -> bool:
        return self.plz is not None and self.plz in ZURICH_PLZS


def parse_homegate_listing(raw: dict[str, Any]) -> HomogateListing:
    listing_id = str(raw["id"])
    listing = raw.get("listing", {})

    address = listing.get("address", {})
    street_raw = address.get("street")
    street, house_number = _split_street(street_raw)
    plz_raw = address.get("postalCode")
    plz = int(plz_raw) if plz_raw else None
    city = address.get("locality")
    geo = address.get("geoCoordinates") or {}
    lat = geo.get("latitude")
    lng = geo.get("longitude")

    chars = listing.get("characteristics", {})
    rooms = chars.get("numberOfRooms")
    area_m2 = chars.get("livingSpace")

    prices = listing.get("prices", {}) or {}
    rent = prices.get("rent", {}) or {}
    rent_net = rent.get("net")
    rent_gross = rent.get("gross")
    rent_charges = rent.get("extra")
    currency = prices.get("currency")

    offer_type = listing.get("offerType")
    categories = listing.get("categories", [])
    object_type = categories[0] if categories else None

    address_raw = f"{street_raw}, {plz} {city}" if street_raw and plz and city else None
    source_url = f"https://www.homegate.ch/rent/{listing_id}"

    return HomogateListing(
        source_id=listing_id,
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
        lat=lat,
        lng=lng,
        object_type=object_type,
        offer_type=offer_type,
        source_url=source_url,
    )


class HomegateConnector:
    """Parses Homegate search result HTML pages (live fetching requires stealth browser)."""

    def _page_url(self, page: int = 1) -> str:
        return f"{_BASE_URL}?ep={page}"

    def parse_page(self, html: str) -> tuple[list[HomogateListing], int]:
        """Extract listings from a Homegate HTML page.

        Returns (listings, total_pages).  Returns ([], 0) if state is missing.
        """
        state = extract_initial_state(html)
        if state is None:
            return [], 0

        result = (
            state.get("resultList", {})
            .get("search", {})
            .get("fullSearch", {})
            .get("result", {})
        )
        raw_listings = result.get("listings", [])
        total_pages = result.get("pageCount", 0)

        listings = [parse_homegate_listing(r) for r in raw_listings]
        return listings, total_pages
