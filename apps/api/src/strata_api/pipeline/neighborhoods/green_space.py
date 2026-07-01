"""OSM green space for the "green access" layer — Overpass fetch, parse, per-Quartier metrics.

Data source: OpenStreetMap via the public Overpass API. Areal green features
(leisure=park/garden, landuse=grass/meadow/forest, natural=wood) are fetched as
ways + relations *with geometry* (`out geom`) and turned into polygons.

Metrics per statistical Quartier:
  - green_area_m2:        total usable green area whose centroid falls in the Quartier
  - green_share_pct:      green_area_m2 / quartier_area_m2 * 100
  - green_m2_per_capita:  green_area_m2 / total_population

DOCUMENTED APPROXIMATIONS (no geometry-clipping dependency):
  1. Assignment is by *centroid*: each green polygon counts fully toward the
     single Quartier that contains its centroid. A park straddling a boundary is
     NOT split — it is attributed entirely to its centroid's Quartier. This can
     over/under-count large border parks but keeps the module dependency-free.
  2. Relation (multipolygon) handling is conservative: only OUTER member rings
     are used, each as its own polygon; INNER rings (holes) are ignored. This
     slightly OVER-counts area for parks with internal voids (ponds, buildings).
  3. Polygon area uses the repo's equirectangular shoelace method
     (`quartier_parser.geometry_area_km2`), accurate to well under 1% at city
     scale — reused here and converted km² -> m².
"""
from __future__ import annotations

import json
import logging
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import TYPE_CHECKING

from strata_api.pipeline.neighborhoods.amenities import point_in_geometry
from strata_api.pipeline.neighborhoods.quartier_parser import geometry_area_km2

if TYPE_CHECKING:
    from strata_api.pipeline.neighborhoods.quartier_parser import QuartierRecord

logger = logging.getLogger(__name__)

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# Stadt Zürich bounding box (south, west, north, east)
ZURICH_BBOX = (47.30, 8.43, 47.45, 8.65)

# category -> (tag key, accepted values). Documented, single source of truth for
# both the Overpass query and the parser's categorization.
GREEN_CATEGORIES: dict[str, tuple[str, frozenset[str]]] = {
    "park": ("leisure", frozenset({"park"})),
    "garden": ("leisure", frozenset({"garden"})),
    "grass": ("landuse", frozenset({"grass"})),
    "meadow": ("landuse", frozenset({"meadow"})),
    "forest": ("landuse", frozenset({"forest"})),
    "wood": ("natural", frozenset({"wood"})),
}

_M2_PER_KM2 = 1_000_000
_PCT_DECIMALS = 4
_AREA_DECIMALS = 1
_MIN_RING_POINTS = 3


def categorize_green_tags(tags: dict) -> str | None:
    """Map an OSM tag dict to one of GREEN_CATEGORIES, or None if irrelevant."""
    for category, (key, values) in GREEN_CATEGORIES.items():
        if tags.get(key) in values:
            return category
    return None


def build_green_overpass_query(bbox: tuple[float, float, float, float] = ZURICH_BBOX) -> str:
    """Build a single Overpass QL query for all green polygons in the bbox.

    Fetches ways + relations only (green space is areal — nodes are meaningless)
    and requests `out geom` so every element carries its vertex geometry.
    """
    bbox_str = ",".join(str(v) for v in bbox)
    # Categories sharing a tag key (leisure, landuse) are unioned per key.
    merged: dict[str, set[str]] = {}
    for key, values in GREEN_CATEGORIES.values():
        merged.setdefault(key, set()).update(values)

    clauses = []
    for key, values in merged.items():
        regex = "|".join(sorted(values))
        clauses.append(f'  way["{key}"~"^({regex})$"]({bbox_str});')
        clauses.append(f'  relation["{key}"~"^({regex})$"]({bbox_str});')
    body = "\n".join(clauses)
    return f"[out:json][timeout:180];\n(\n{body}\n);\nout geom;"


def fetch_overpass_green(bbox: tuple[float, float, float, float] = ZURICH_BBOX) -> dict:
    """Fetch raw green elements from the public Overpass API (with retries)."""
    query = build_green_overpass_query(bbox)
    payload = urllib.parse.urlencode({"data": query}).encode()
    req = urllib.request.Request(
        OVERPASS_URL,
        data=payload,
        headers={"User-Agent": "Strata-Pipeline/1.0 (research; contact: hello@strata.ch)"},
    )
    for attempt in range(1, 4):
        try:
            with urllib.request.urlopen(req, timeout=240) as resp:  # noqa: S310 (fixed https host)
                return json.loads(resp.read())
        except Exception as exc:
            if attempt == 3:
                raise
            wait = 15 * attempt
            logger.warning("Overpass green fetch failed (attempt %d/3): %s — retrying in %ds", attempt, exc, wait)
            time.sleep(wait)
    raise RuntimeError("unreachable")


# ── Area / centroid helpers (reuse the repo's shoelace area method) ─────────────


def green_area_m2(coordinates: list[list[float]]) -> float:
    """Area of a single lon/lat ring in m² via the repo's equirectangular method."""
    km2 = geometry_area_km2({"type": "Polygon", "coordinates": [coordinates]})
    return round((km2 or 0.0) * _M2_PER_KM2, _AREA_DECIMALS)


def _ring_centroid(coordinates: list[list[float]]) -> tuple[float, float]:
    """Area-weighted polygon centroid (lon, lat); falls back to vertex mean."""
    n = len(coordinates)
    a2 = 0.0
    cx = 0.0
    cy = 0.0
    for i in range(n - 1):
        x0, y0 = coordinates[i]
        x1, y1 = coordinates[i + 1]
        cross = x0 * y1 - x1 * y0
        a2 += cross
        cx += (x0 + x1) * cross
        cy += (y0 + y1) * cross
    if a2 == 0:  # degenerate / collinear — average the vertices instead
        xs = [p[0] for p in coordinates]
        ys = [p[1] for p in coordinates]
        return (sum(xs) / n, sum(ys) / n)
    return (cx / (3 * a2), cy / (3 * a2))


# ── Green area dataclass ────────────────────────────────────────────────────────


@dataclass(frozen=True)
class GreenArea:
    """A single areal green feature (immutable). Coordinates are a closed lon/lat ring."""

    name: str | None
    category: str
    coordinates: tuple[tuple[float, float], ...]
    area_m2: float
    centroid: tuple[float, float]  # (lon, lat)

    @classmethod
    def from_ring(cls, name: str | None, category: str, coordinates: list[list[float]]) -> GreenArea:
        """Build a GreenArea from a lon/lat ring, precomputing area and centroid."""
        coords = tuple((float(lon), float(lat)) for lon, lat in coordinates)
        return cls(
            name=name,
            category=category,
            coordinates=coords,
            area_m2=green_area_m2(coordinates),
            centroid=_ring_centroid(coordinates),
        )

    @property
    def ring(self) -> list[list[float]]:
        """The ring as a GeoJSON-style list of [lon, lat] pairs."""
        return [[lon, lat] for lon, lat in self.coordinates]


def _geometry_to_ring(geometry: list[dict]) -> list[list[float]]:
    """Convert an Overpass `geometry` list of {lat, lon} nodes to a lon/lat ring."""
    return [[node["lon"], node["lat"]] for node in geometry if "lon" in node and "lat" in node]


def parse_overpass_green(data: dict) -> list[GreenArea]:
    """Parse an Overpass JSON response (`out geom`) into GreenArea polygons.

    - Ways: their `geometry` ring becomes one GreenArea.
    - Relations: each OUTER member ring becomes one GreenArea (inner rings/holes
      ignored — documented conservative simplification).
    - Rings with fewer than 3 points are degenerate and skipped (logged count).
    - Elements without a matching green category are skipped.
    """
    areas: list[GreenArea] = []
    degenerate = 0

    for el in data.get("elements", []):
        tags = el.get("tags")
        if not tags:
            continue
        category = categorize_green_tags(tags)
        if category is None:
            continue
        name = tags.get("name")

        rings: list[list[list[float]]] = []
        if el.get("type") == "way":
            rings.append(_geometry_to_ring(el.get("geometry", [])))
        elif el.get("type") == "relation":
            for member in el.get("members", []):
                if member.get("role") == "outer" and member.get("geometry"):
                    rings.append(_geometry_to_ring(member["geometry"]))

        for ring in rings:
            if len(ring) < _MIN_RING_POINTS:
                degenerate += 1
                continue
            areas.append(GreenArea.from_ring(name=name, category=category, coordinates=ring))

    if degenerate:
        logger.info("Skipped %d degenerate green geometries (<%d points)", degenerate, _MIN_RING_POINTS)
    return areas


# ── Per-quartier metrics ────────────────────────────────────────────────────────


def _share_pct(green_m2: float, area_km2: float | None) -> float | None:
    if area_km2 is None or area_km2 <= 0:
        return None
    return round(green_m2 / (area_km2 * _M2_PER_KM2) * 100, _PCT_DECIMALS)


def _per_capita(green_m2: float, population: int | None) -> float | None:
    if not population or population <= 0:
        return None
    return round(green_m2 / population, _AREA_DECIMALS)


def compute_green_metrics(
    green_areas: list[GreenArea],
    quartier_records: dict[int, QuartierRecord],
    populations: dict[int, int | None],
) -> dict[int, dict]:
    """Assign each green polygon to the Quartier containing its centroid and aggregate.

    Returns per-quartier {green_area_m2, green_share_pct, green_m2_per_capita}.
    Polygons whose centroid lies outside every Quartier (lake, agglomeration) are
    dropped. See the module docstring for the centroid-assignment approximation.
    """
    totals: dict[int, float] = dict.fromkeys(quartier_records, 0.0)

    for area in green_areas:
        lon, lat = area.centroid
        for qid, rec in quartier_records.items():
            if point_in_geometry(lon, lat, rec.geometry):
                totals[qid] += area.area_m2
                break

    metrics: dict[int, dict] = {}
    for qid, rec in quartier_records.items():
        green_m2 = round(totals[qid], _AREA_DECIMALS)
        metrics[qid] = {
            "green_area_m2": green_m2,
            "green_share_pct": _share_pct(green_m2, rec.area_km2),
            "green_m2_per_capita": _per_capita(green_m2, populations.get(qid)),
        }
    return metrics


# ── GeoJSON builder for the map layer ───────────────────────────────────────────


def build_green_geojson(green_areas: list[GreenArea]) -> dict:
    """Build a FeatureCollection of green polygons for the toggleable map layer."""
    features = [
        {
            "type": "Feature",
            "geometry": {"type": "Polygon", "coordinates": [area.ring]},
            "properties": {"name": area.name, "category": area.category, "area_m2": area.area_m2},
        }
        for area in green_areas
    ]
    return {"type": "FeatureCollection", "features": features}
