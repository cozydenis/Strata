"""Parse noise cadastre WFS GeoJSON into a normalized FeatureCollection.

Data source: Stadt Zürich WFS — strlaerm_ep (Strassenlaermkataster)
Geometry: Point (Fassadenpunkte = facade measurement points)

Key fields discovered via recon:
  lr_day   -> db_day  (float, dB daytime noise level)
  lr_night -> db_night (float, dB nighttime noise level)
  egid     -> egid     (int | None, building identifier)

Noise category thresholds (day level):
  < 50 dB  -> "quiet"
  50-60 dB -> "moderate"
  60-70 dB -> "loud"
  > 70 dB  -> "very_loud"
"""
from __future__ import annotations


def _noise_category(db_day: float | None) -> str | None:
    """Categorize noise level by daytime dB."""
    if db_day is None:
        return None
    if db_day < 50:
        return "quiet"
    if db_day < 60:
        return "moderate"
    if db_day < 70:
        return "loud"
    return "very_loud"


def parse_noise_geojson(data: dict) -> dict:
    """Parse WFS GeoJSON noise cadastre into a normalized FeatureCollection.

    Renames lr_day -> db_day, lr_night -> db_night.
    Skips features with null geometry or both dB values null.
    Adds noise_category property based on daytime dB level.
    """
    features: list[dict] = []

    for feature in data.get("features", []):
        geom = feature.get("geometry")
        if not geom:
            continue

        props = feature.get("properties", {}) or {}
        db_day_raw = props.get("lr_day")
        db_night_raw = props.get("lr_night")

        # Skip if both values are null
        if db_day_raw is None and db_night_raw is None:
            continue

        db_day = float(db_day_raw) if db_day_raw is not None else None
        db_night = float(db_night_raw) if db_night_raw is not None else None
        egid_raw = props.get("egid")
        egid = int(egid_raw) if egid_raw is not None else None

        features.append({
            "type": "Feature",
            "geometry": geom,
            "properties": {
                "egid": egid,
                "db_day": db_day,
                "db_night": db_night,
                "noise_category": _noise_category(db_day),
            },
        })

    return {"type": "FeatureCollection", "features": features}
