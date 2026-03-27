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

from pydantic import BaseModel


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
    area_km2 is None unless explicitly provided in properties (WFS does not include it).
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

        records[quartier_id] = QuartierRecord(
            quartier_id=quartier_id,
            quartier_name=quartier_name,
            kreis=kreis,
            area_km2=float(area_km2) if area_km2 is not None else None,
            geometry=geom,
        )

    return records
