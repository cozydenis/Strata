"""Parse Quartier WFS GeoJSON into structured records.

Data source: Stadt Zürich WFS — adm_statistische_quartiere_map
Real field names discovered via recon:
  qnr      -> quartier_id  (int)
  qname    -> quartier_name (str)
  knr      -> kreis         (int)
  kname    -> kreis_name    (str, unused in model but available)
  objectid -> internal WFS ID (ignored)
  geometrie_gdo -> always null in GeoJSON output (ignored)
"""
from __future__ import annotations

import math

from pydantic import BaseModel

# Metres per degree of latitude (WGS84 mean); longitude scales with cos(lat)
_M_PER_DEG_LAT = 111_320.0


def _ring_area_km2(ring: list) -> float:
    """Planar shoelace area of a lon/lat ring using an equirectangular projection.

    Accurate to well under 1% at city scale, which is plenty for density figures.
    """
    if len(ring) < 4:
        return 0.0
    lat0 = math.radians(sum(pt[1] for pt in ring) / len(ring))
    m_per_deg_lon = _M_PER_DEG_LAT * math.cos(lat0)

    area2 = 0.0
    j = len(ring) - 1
    for i in range(len(ring)):
        xi, yi = ring[i][0] * m_per_deg_lon, ring[i][1] * _M_PER_DEG_LAT
        xj, yj = ring[j][0] * m_per_deg_lon, ring[j][1] * _M_PER_DEG_LAT
        area2 += xj * yi - xi * yj
        j = i
    return abs(area2) / 2 / 1_000_000


def _polygon_area_km2(rings: list) -> float:
    """Exterior ring area minus holes."""
    if not rings:
        return 0.0
    area = _ring_area_km2(rings[0])
    for hole in rings[1:]:
        area -= _ring_area_km2(hole)
    return max(area, 0.0)


def geometry_area_km2(geometry: dict) -> float | None:
    """Area of a GeoJSON Polygon or MultiPolygon in km², None for other types."""
    gtype = geometry.get("type")
    if gtype == "Polygon":
        return _polygon_area_km2(geometry.get("coordinates", []))
    if gtype == "MultiPolygon":
        return sum(_polygon_area_km2(rings) for rings in geometry.get("coordinates", []))
    return None


class QuartierRecord(BaseModel, frozen=True):
    """Immutable record for a single statistical Quartier."""

    quartier_id: int
    quartier_name: str
    kreis: int
    area_km2: float | None
    geometry: dict


def parse_quartier_geojson(geojson_data: dict) -> dict[int, QuartierRecord]:
    """Parse WFS GeoJSON FeatureCollection into a dict keyed by quartier_id.

    Skips features with null/missing geometry.
    area_km2 comes from properties when provided; otherwise it is computed
    from the polygon geometry (the WFS does not include it).
    """
    records: dict[int, QuartierRecord] = {}

    for feature in geojson_data.get("features", []):
        geom = feature.get("geometry")
        if not geom:
            continue

        props = feature.get("properties", {}) or {}
        quartier_id: int = int(props["qnr"])
        quartier_name: str = str(props["qname"])
        kreis: int = int(props["knr"])
        area_km2: float | None = props.get("area_km2")
        if area_km2 is None:
            area_km2 = geometry_area_km2(geom)

        records[quartier_id] = QuartierRecord(
            quartier_id=quartier_id,
            quartier_name=quartier_name,
            kreis=kreis,
            area_km2=float(area_km2) if area_km2 is not None else None,
            geometry=geom,
        )

    return records
