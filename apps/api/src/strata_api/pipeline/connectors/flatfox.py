"""Flatfox API connector — fetches rental listings from flatfox.ch/api/v1/public-listing/."""
from __future__ import annotations

import asyncio
import json
import logging
import re
import time
import urllib.request
from typing import Any

from pydantic import BaseModel, computed_field

logger = logging.getLogger(__name__)

# Kanton Zürich PLZ whitelist — derived from GWR entrances (255 PLZs).
# Excludes other cantons sharing the 8xxx range (Thurgau, St.Gallen, Schwyz, Glarus, etc.).
ZURICH_PLZS: frozenset[int] = frozenset({
    8001, 8002, 8003, 8004, 8005, 8006, 8008, 8032, 8037, 8038, 8041, 8044,
    8045, 8046, 8047, 8048, 8049, 8050, 8051, 8052, 8053, 8055, 8057, 8064,
    8102, 8103, 8104, 8105, 8106, 8107, 8108, 8112, 8113, 8114, 8115, 8117,
    8118, 8121, 8122, 8123, 8124, 8125, 8126, 8127, 8132, 8133, 8134, 8135,
    8136, 8142, 8143, 8152, 8153, 8154, 8155, 8156, 8157, 8158, 8162, 8164,
    8165, 8166, 8172, 8173, 8174, 8175, 8180, 8181, 8182, 8184, 8185, 8187,
    8192, 8193, 8194, 8195, 8196, 8197, 8212, 8245, 8246, 8247, 8248, 8302,
    8303, 8304, 8305, 8306, 8307, 8308, 8309, 8310, 8311, 8312, 8314, 8315,
    8317, 8320, 8322, 8330, 8331, 8332, 8335, 8340, 8342, 8344, 8345, 8352,
    8353, 8354, 8355, 8363, 8400, 8404, 8405, 8406, 8408, 8409, 8412, 8413,
    8414, 8415, 8416, 8418, 8421, 8422, 8424, 8425, 8426, 8427, 8428, 8442,
    8444, 8447, 8450, 8451, 8452, 8453, 8457, 8458, 8459, 8460, 8461, 8462,
    8463, 8464, 8465, 8466, 8467, 8468, 8471, 8472, 8474, 8475, 8476, 8477,
    8478, 8479, 8482, 8483, 8484, 8486, 8487, 8488, 8489, 8492, 8493, 8494,
    8495, 8496, 8497, 8498, 8499, 8500, 8523, 8525, 8542, 8543, 8544, 8545,
    8546, 8548, 8600, 8602, 8603, 8604, 8605, 8606, 8607, 8608, 8610, 8614,
    8615, 8616, 8617, 8618, 8620, 8623, 8624, 8625, 8626, 8627, 8630, 8632,
    8633, 8634, 8635, 8636, 8637, 8700, 8702, 8703, 8704, 8706, 8707, 8708,
    8712, 8713, 8714, 8800, 8802, 8803, 8804, 8805, 8810, 8815, 8816, 8820,
    8824, 8825, 8833, 8902, 8903, 8904, 8906, 8907, 8908, 8909, 8910, 8911,
    8912, 8913, 8914, 8915, 8925, 8926, 8932, 8933, 8934, 8942, 8951, 8952,
    8953, 8954, 8955,
})

BASE_URL = "https://flatfox.ch/api/v1/public-listing/"
_DEFAULT_LIMIT = 96
_REQUEST_DELAY_S = 0.5  # polite delay between pages

# Residential object categories — skip parking, industrial, commercial
_RESIDENTIAL_TYPES = frozenset({"APARTMENT", "HOUSE", "SHARED", "SECONDARY", "TERRACE_HOUSE"})


class FlatfoxListing(BaseModel):
    """Parsed listing from Flatfox, ready for DB upsert."""

    source: str = "flatfox"
    source_id: str
    slug: str = ""
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
    status: str | None = None
    source_url: str | None = None
    description: str | None = None
    image_ids: list[int] = []
    cover_image_id: int | None = None
    document_ids: list[int] = []

    @computed_field  # type: ignore[misc]
    @property
    def is_zurich_area(self) -> bool:
        return self.plz is not None and self.plz in ZURICH_PLZS

    @computed_field  # type: ignore[misc]
    @property
    def is_residential(self) -> bool:
        """True for apartments, houses, shared — False for parking, industrial."""
        if self.object_type is None:
            return True  # don't discard listings with unknown type
        return self.object_type.upper() in _RESIDENTIAL_TYPES


_STATUS_MAP = {"act": "active", "inact": "inactive", "res": "reserved"}

# Matches street + house number, where house number can be:
#   "10", "10a", "108/110", "30/30a", "10-24", "10 - 24"
_STREET_NUM_RE = re.compile(
    r"^(.*?)[\s,]+(\d[\w]*(?:\s*[-/]\s*\d[\w]*)*)$"
)

# Common Swiss listing prefixes/suffixes to strip before parsing
# UNG = Untergeschoss (basement), EH = Einstellhalle (parking garage),
# TG = Tiefgarage (underground garage), EKZ = Einkaufszentrum
_STRIP_PREFIX_RE = re.compile(r"^(?:UNG|TG|EKZ)\s+", re.I)
_STRIP_SUFFIX_RE = re.compile(r",\s*(?:EH|TG|UNG|Einstellhalle|Tiefgarage)\s*$", re.I)


def _split_street(raw: str | None) -> tuple[str | None, str | None]:
    """Split 'Bahnhofstrasse 10' → ('Bahnhofstrasse', '10').

    Handles compound house numbers (108/110, 30/30a, 10 - 24)
    and strips parking/basement prefixes (UNG, EH, TG, EKZ).
    """
    if not raw:
        return None, None
    s = raw.strip()
    # Strip known prefixes/suffixes
    s = _STRIP_PREFIX_RE.sub("", s)
    s = _STRIP_SUFFIX_RE.sub("", s)
    s = s.strip()
    m = _STREET_NUM_RE.match(s)
    if m:
        street = m.group(1).strip()
        number = re.sub(r"\s+", "", m.group(2))  # "10 - 24" → "10-24"
        return street, number
    return s, None


def parse_flatfox_listing(raw: dict[str, Any]) -> FlatfoxListing:
    pk = raw["pk"]
    slug = raw.get("slug", "")
    street_raw = raw.get("street")
    street, house_number = _split_street(street_raw)

    status_raw = raw.get("status", "")
    status = _STATUS_MAP.get(status_raw, status_raw)

    source_url = f"https://flatfox.ch/en/flat/{slug}/{pk}/"

    return FlatfoxListing(
        source="flatfox",
        source_id=str(pk),
        slug=slug,
        rent_net=raw.get("rent_net"),
        rent_gross=raw.get("rent_gross"),
        rent_charges=raw.get("rent_charges"),
        rooms=raw.get("number_of_rooms"),
        area_m2=raw.get("surface_living"),
        address_raw=raw.get("public_address"),
        street=street,
        house_number=house_number,
        plz=raw.get("zipcode"),
        city=raw.get("city"),
        lat=raw.get("latitude"),
        lng=raw.get("longitude"),
        object_type=raw.get("object_category"),
        offer_type=raw.get("offer_type"),
        status=status,
        source_url=source_url,
        description=raw.get("description"),
        image_ids=raw.get("images") or [],
        cover_image_id=raw.get("cover_image"),
        document_ids=raw.get("documents") or [],
    )


class FlatfoxConnector:
    """Iterates through all Flatfox listings page by page."""

    def __init__(self, limit: int = _DEFAULT_LIMIT) -> None:
        self._limit = limit

    def _page_url(self, offset: int, limit: int) -> str:
        return f"{BASE_URL}?limit={limit}&offset={offset}"

    async def _fetch_json(self, url: str) -> dict:
        """Async-compatible wrapper around urllib (no extra deps required)."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._sync_fetch, url)

    def _sync_fetch(self, url: str) -> dict:
        req = urllib.request.Request(
            url,
            headers={
                "Accept": "application/json",
                "User-Agent": "Strata-Pipeline/1.0 (research; contact: hello@strata.ch)",
            },
        )
        for attempt in range(1, 4):
            try:
                with urllib.request.urlopen(req, timeout=60) as resp:
                    return json.loads(resp.read())
            except Exception as exc:
                if attempt == 3:
                    raise
                wait = 5 * attempt
                logger.warning(
                    "Fetch failed (attempt %d/3): %s — retrying in %ds", attempt, exc, wait
                )
                time.sleep(wait)

    async def fetch_page(
        self, offset: int = 0, limit: int | None = None
    ) -> tuple[list[FlatfoxListing], bool]:
        """Fetch one page of listings.

        Returns (listings_in_kanton_zuerich, has_more).
        """
        lim = limit if limit is not None else self._limit
        url = self._page_url(offset=offset, limit=lim)
        data = await self._fetch_json(url)

        results = data.get("results", [])
        has_more = data.get("next") is not None

        listings = [parse_flatfox_listing(r) for r in results]
        zh_listings = [lst for lst in listings if lst.is_zurich_area and lst.is_residential]
        return zh_listings, has_more

    async def fetch_all_zurich(self) -> list[FlatfoxListing]:
        """Fetch ALL pages and return only Kanton Zürich listings."""
        all_listings: list[FlatfoxListing] = []
        offset = 0

        while True:
            listings, has_more = await self.fetch_page(offset=offset)
            all_listings.extend(listings)
            logger.info("Flatfox offset=%d fetched=%d zh_total=%d", offset, len(listings), len(all_listings))
            if not has_more:
                break
            offset += self._limit
            await asyncio.sleep(_REQUEST_DELAY_S)

        return all_listings
