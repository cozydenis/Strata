"""OSM amenities for the walkability layer — Overpass fetch, categorize, count per Quartier.

Data source: OpenStreetMap via the public Overpass API. Elements are matched to
seven amenity categories relevant to "where should I live?" and assigned to
statistical Quartiere by point-in-polygon against the WFS boundaries.
"""
from __future__ import annotations

import json
import logging
import time
import urllib.parse
import urllib.request
from typing import TYPE_CHECKING

from pydantic import BaseModel

if TYPE_CHECKING:
    from strata_api.pipeline.neighborhoods.quartier_parser import QuartierRecord

logger = logging.getLogger(__name__)

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# Stadt Zürich bounding box (south, west, north, east)
ZURICH_BBOX = (47.30, 8.43, 47.45, 8.65)

# category -> (tag key, accepted values)
AMENITY_CATEGORIES: dict[str, tuple[str, frozenset[str]]] = {
    "groceries": ("shop", frozenset({"supermarket", "convenience", "greengrocer"})),
    "cafes": ("amenity", frozenset({"cafe"})),
    "restaurants": ("amenity", frozenset({"restaurant", "fast_food"})),
    "bars": ("amenity", frozenset({"bar", "pub"})),
    "pharmacies": ("amenity", frozenset({"pharmacy"})),
    "schools": ("amenity", frozenset({"school", "kindergarten"})),
    "fitness": ("leisure", frozenset({"fitness_centre", "sports_centre"})),
}


class AmenityPoint(BaseModel, frozen=True):
    """A single categorized amenity location."""

    category: str
    name: str | None
    lat: float
    lon: float


def categorize_tags(tags: dict) -> str | None:
    """Map an OSM tag dict to one of AMENITY_CATEGORIES, or None if irrelevant."""
    for category, (key, values) in AMENITY_CATEGORIES.items():
        if tags.get(key) in values:
            return category
    return None


def build_overpass_query(bbox: tuple[float, float, float, float] = ZURICH_BBOX) -> str:
    """Build a single Overpass QL query covering all amenity categories."""
    bbox_str = ",".join(str(v) for v in bbox)
    # Several categories share a tag key (amenity) — union their values per key
    merged: dict[str, set[str]] = {}
    for key, values in AMENITY_CATEGORIES.values():
        merged.setdefault(key, set()).update(values)

    clauses = []
    for key, values in merged.items():
        regex = "|".join(sorted(values))
        clauses.append(f'  node["{key}"~"^({regex})$"]({bbox_str});')
        clauses.append(f'  way["{key}"~"^({regex})$"]({bbox_str});')
    body = "\n".join(clauses)
    return f"[out:json][timeout:180];\n(\n{body}\n);\nout center;"


def parse_overpass_amenities(data: dict) -> list[AmenityPoint]:
    """Parse an Overpass JSON response into categorized amenity points.

    Nodes carry lat/lon directly; ways/relations carry a "center". Elements
    without coordinates or without a matching category are skipped.
    """
    points: list[AmenityPoint] = []
    for el in data.get("elements", []):
        tags = el.get("tags")
        if not tags:
            continue
        category = categorize_tags(tags)
        if category is None:
            continue

        if "lat" in el and "lon" in el:
            lat, lon = el["lat"], el["lon"]
        elif "center" in el:
            lat, lon = el["center"]["lat"], el["center"]["lon"]
        else:
            continue

        points.append(AmenityPoint(category=category, name=tags.get("name"), lat=lat, lon=lon))
    return points


def fetch_overpass_amenities(bbox: tuple[float, float, float, float] = ZURICH_BBOX) -> dict:
    """Fetch raw amenity elements from the public Overpass API (with retries)."""
    query = build_overpass_query(bbox)
    payload = urllib.parse.urlencode({"data": query}).encode()
    req = urllib.request.Request(
        OVERPASS_URL,
        data=payload,
        headers={"User-Agent": "Strata-Pipeline/1.0 (research; contact: hello@strata.ch)"},
    )
    for attempt in range(1, 4):
        try:
            with urllib.request.urlopen(req, timeout=240) as resp:
                return json.loads(resp.read())
        except Exception as exc:
            if attempt == 3:
                raise
            wait = 15 * attempt
            logger.warning("Overpass fetch failed (attempt %d/3): %s — retrying in %ds", attempt, exc, wait)
            time.sleep(wait)
    raise RuntimeError("unreachable")


# Point-in-polygon lives in the shared geometry module; re-exported here for
# back-compat (green_space and older callers import it from amenities).
from strata_api.pipeline.neighborhoods.geometry import point_in_geometry  # noqa: E402, F401


def count_amenities_per_quartier(
    points: list[AmenityPoint],
    quartier_records: dict[int, QuartierRecord],
) -> dict[int, dict[str, int]]:
    """Assign each amenity point to its containing Quartier and count per category.

    Points outside every Quartier (lake, agglomeration) are dropped.
    """
    counts: dict[int, dict[str, int]] = {
        qid: dict.fromkeys(AMENITY_CATEGORIES, 0) for qid in quartier_records
    }
    for point in points:
        for qid, rec in quartier_records.items():
            if point_in_geometry(point.lon, point.lat, rec.geometry):
                counts[qid][point.category] += 1
                break
    return counts
