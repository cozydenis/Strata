"""Pure GeoJSON assembly for air-quality station points."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def _parameter_properties(aggregate) -> dict:
    """Build the per-parameter properties block: latest + 24h mean + unit."""
    out: dict[str, dict] = {}
    for parameter, summary in aggregate.parameters.items():
        out[parameter] = {
            "latest": summary.latest_value,
            "mean_24h": summary.mean_24h,
            "unit": summary.unit,
            "level": summary.level,
        }
    return out


def build_air_geojson(aggregates: dict, stations: dict) -> dict:
    """Build a FeatureCollection of station Points from aggregates + metadata.

    Each Feature is a Point at the station's WGS84 coordinates with properties:
      station, station_id, level, measured_at, parameters{param: {...}}.

    Stations present in the measurements but missing from ``stations`` metadata
    cannot be placed on the map and are skipped (with a warning). Stations in
    the metadata with no measurements simply produce no feature.
    """
    features: list[dict] = []
    missing_meta = 0

    for station_id, aggregate in sorted(aggregates.items()):
        station = stations.get(station_id)
        if station is None:
            missing_meta += 1
            logger.warning("build_air_geojson: no metadata for station %r — skipping", station_id)
            continue

        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [station.lng, station.lat]},
                "properties": {
                    "station": station.short_name,
                    "station_id": station_id,
                    "name": station.name,
                    "level": aggregate.level,
                    "measured_at": aggregate.measured_at.isoformat(),
                    "parameters": _parameter_properties(aggregate),
                },
            }
        )

    if missing_meta:
        logger.info("build_air_geojson: %d station(s) skipped for missing metadata", missing_meta)

    return {"type": "FeatureCollection", "features": features}
