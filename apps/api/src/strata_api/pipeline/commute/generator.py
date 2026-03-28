"""Commute isochrone generator — fetches isochrones and writes GeoJSON files.

Supports two backends:
- **OTP** (local OpenTripPlanner): used when ``otp_base_url`` is reachable.
- **TravelTime API**: used when env vars ``TRAVELTIME_APP_ID`` and
  ``TRAVELTIME_API_KEY`` are set.  Free tier allows 5 req/min.

CLI usage (from apps/api):
    uv run python -m strata_api.pipeline.commute.generator \\
        --output-dir ../web/public/data/commutes

Set TRAVELTIME_APP_ID and TRAVELTIME_API_KEY in the environment to use
TravelTime; otherwise falls back to OTP at http://localhost:8080.
"""
from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path

import httpx

from strata_api.pipeline.commute.destinations import CONTOUR_MINUTES, DESTINATIONS

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# OTP backend
# ---------------------------------------------------------------------------


def fetch_isochrone(
    destination_key: str,
    otp_base_url: str,
    contour_minutes: list[int],
    arrive_by: bool = True,
) -> dict:
    """Fetch a travel-time isochrone FeatureCollection from OTP.

    Calls the LegacyRestApi isochrone endpoint and tags each feature with
    ``contour_minutes`` (int) converted from the OTP ``time`` property (seconds).

    Args:
        destination_key: Key into DESTINATIONS (e.g. "hb").
        otp_base_url: Base URL of the OTP instance (e.g. "http://localhost:8080").
        contour_minutes: List of travel-time thresholds in minutes.
        arrive_by: When True, isochrones indicate areas reachable to arrive
                   at the destination by 08:00.

    Returns:
        GeoJSON FeatureCollection dict with contour_minutes property on each feature.
    """
    dest = DESTINATIONS[destination_key]
    lat = dest["lat"]
    lon = dest["lon"]

    # OTP 2.x LegacyRestApi endpoint — cutoffSec in seconds, repeated per threshold
    # arriveBy=true: areas from which you can ARRIVE at destination within N minutes
    place_param = "toPlace" if arrive_by else "fromPlace"
    cutoff_secs = [m * 60 for m in contour_minutes]

    params: list[tuple[str, str]] = [
        (place_param, f"{lat},{lon}"),
        ("mode", "TRANSIT,WALK"),
        ("time", "2026-03-27T08:00:00"),
        ("arriveBy", str(arrive_by).lower()),
    ]
    for s in cutoff_secs:
        params.append(("cutoffSec", str(s)))

    url = f"{otp_base_url}/otp/routers/default/isochrone"
    response = httpx.get(url, params=params)
    response.raise_for_status()

    geojson: dict = response.json()

    # Tag each feature: convert OTP's `time` property (seconds) → contour_minutes (int)
    for feature in geojson.get("features", []):
        props = feature.setdefault("properties", {})
        time_seconds = props.get("time", 0)
        props["contour_minutes"] = int(time_seconds) // 60

    return geojson


def generate_all(otp_base_url: str, output_dir: str) -> None:
    """Generate isochrone GeoJSON files for all preset destinations via OTP.

    For each destination key in DESTINATIONS, calls fetch_isochrone and writes
    the result to ``{output_dir}/{key}.geojson``.

    Args:
        otp_base_url: Base URL of the OTP instance.
        output_dir: Directory path where GeoJSON files will be written.
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    for key in DESTINATIONS:
        logger.info("Fetching isochrone for destination: %s", key)
        geojson = fetch_isochrone(key, otp_base_url, CONTOUR_MINUTES)
        filepath = out / f"{key}.geojson"
        filepath.write_text(json.dumps(geojson, ensure_ascii=False), encoding="utf-8")
        logger.info("Written %s", filepath)


# ---------------------------------------------------------------------------
# TravelTime API backend
# ---------------------------------------------------------------------------

_TRAVELTIME_URL = "https://api.traveltimeapp.com/v4/time-map"
# Zürich morning rush-hour arrival: 09:00 CET (UTC+1 in winter)
_DEFAULT_ARRIVAL_TIME = "2026-03-27T09:00:00+01:00"
# Free tier: 5 req/min — throttle to stay within limit
_TRAVELTIME_REQUEST_INTERVAL_SECS = 13.0


def _traveltime_shapes_to_geojson_feature(shapes: list[dict], contour_minutes: int) -> dict:
    """Convert TravelTime API shapes to a GeoJSON Feature (Polygon or MultiPolygon)."""
    polygons = []
    for shape in shapes:
        shell = [[pt["lng"], pt["lat"]] for pt in shape["shell"]]
        if shell and shell[0] != shell[-1]:
            shell.append(shell[0])

        holes = []
        for hole in shape.get("holes", []):
            ring = [[pt["lng"], pt["lat"]] for pt in hole]
            if ring and ring[0] != ring[-1]:
                ring.append(ring[0])
            holes.append(ring)

        polygons.append([shell] + holes)

    if len(polygons) == 1:
        geometry: dict = {"type": "Polygon", "coordinates": polygons[0]}
    else:
        geometry = {"type": "MultiPolygon", "coordinates": polygons}

    return {"type": "Feature", "geometry": geometry, "properties": {"contour_minutes": contour_minutes}}


def fetch_isochrone_traveltime(
    destination_key: str,
    app_id: str,
    api_key: str,
    contour_minutes: list[int],
    arrival_time: str = _DEFAULT_ARRIVAL_TIME,
) -> dict:
    """Fetch a travel-time isochrone FeatureCollection from TravelTime API.

    Sends one POST request with multiple ``arrival_searches`` (one per time band).
    Each result is tagged with ``contour_minutes``.

    Args:
        destination_key: Key into DESTINATIONS (e.g. "hb").
        app_id: TravelTime application ID (TRAVELTIME_APP_ID env var).
        api_key: TravelTime API key (TRAVELTIME_API_KEY env var).
        contour_minutes: List of travel-time thresholds in minutes.
        arrival_time: ISO-8601 arrival time for the reverse isochrone query.

    Returns:
        GeoJSON FeatureCollection with contour_minutes property on each feature.
    """
    dest = DESTINATIONS[destination_key]
    lat = dest["lat"]
    lon = dest["lon"]

    searches = [
        {
            "id": f"{destination_key}_{minutes}min",
            "coords": {"lat": lat, "lng": lon},
            "travel_time": minutes * 60,
            "arrival_time": arrival_time,
            "transportation": {"type": "public_transport"},
        }
        for minutes in contour_minutes
    ]

    response = httpx.post(
        _TRAVELTIME_URL,
        headers={
            "X-Application-Id": app_id,
            "X-Api-Key": api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        json={"arrival_searches": searches},
        timeout=60.0,
    )
    response.raise_for_status()

    data = response.json()

    features = []
    for result in data.get("results", []):
        search_id: str = result["search_id"]
        # Parse minutes from id like "hb_10min"
        minutes = int(search_id.rsplit("_", 1)[-1].replace("min", ""))
        feature = _traveltime_shapes_to_geojson_feature(result.get("shapes", []), minutes)
        features.append(feature)

    # Largest band first so smaller (more specific) bands render on top
    features.sort(key=lambda f: -f["properties"]["contour_minutes"])

    return {"type": "FeatureCollection", "features": features}


def generate_all_traveltime(app_id: str, api_key: str, output_dir: str) -> None:
    """Generate isochrone GeoJSON files for all preset destinations via TravelTime API.

    Makes one request per destination (throttled to respect 5 req/min free tier).
    Each request contains all 4 time bands as separate arrival_searches.

    Args:
        app_id: TravelTime application ID.
        api_key: TravelTime API key.
        output_dir: Directory where GeoJSON files will be written.
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    keys = list(DESTINATIONS.keys())
    for i, key in enumerate(keys):
        if i > 0:
            logger.info("Throttling %.0fs (TravelTime free tier: 5 req/min)...", _TRAVELTIME_REQUEST_INTERVAL_SECS)
            time.sleep(_TRAVELTIME_REQUEST_INTERVAL_SECS)

        logger.info("Fetching TravelTime isochrone for destination: %s", key)
        geojson = fetch_isochrone_traveltime(key, app_id, api_key, CONTOUR_MINUTES)
        filepath = out / f"{key}.geojson"
        filepath.write_text(json.dumps(geojson, ensure_ascii=False), encoding="utf-8")
        feature_count = len(geojson.get("features", []))
        logger.info("Written %s (%d features)", filepath, feature_count)


# ---------------------------------------------------------------------------
# Auto-detecting entry point
# ---------------------------------------------------------------------------


def generate_all_auto(output_dir: str, otp_base_url: str = "http://localhost:8080") -> None:
    """Generate isochrone GeoJSON files, auto-selecting backend.

    Uses TravelTime API if TRAVELTIME_APP_ID and TRAVELTIME_API_KEY env vars
    are set; otherwise falls back to OTP at ``otp_base_url``.
    """
    app_id = os.environ.get("TRAVELTIME_APP_ID")
    api_key = os.environ.get("TRAVELTIME_API_KEY")

    if app_id and api_key:
        logger.info("Using TravelTime API backend (TRAVELTIME_APP_ID is set)")
        generate_all_traveltime(app_id, api_key, output_dir)
    else:
        logger.info("Using OTP backend at %s", otp_base_url)
        generate_all(otp_base_url, output_dir)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    parser = argparse.ArgumentParser(description="Generate commute isochrone GeoJSON files")
    parser.add_argument(
        "--output-dir",
        default="../web/public/data/commutes",
        help="Directory to write GeoJSON files (default: ../web/public/data/commutes)",
    )
    parser.add_argument(
        "--otp-url",
        default="http://localhost:8080",
        help="OTP base URL (used when TravelTime env vars are not set)",
    )
    args = parser.parse_args()

    generate_all_auto(args.output_dir, args.otp_url)
