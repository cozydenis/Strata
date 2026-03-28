"""Compute commute travel times from Quartier centroids to preset destinations."""
from __future__ import annotations

import logging

import httpx

from strata_api.pipeline.commute.destinations import DESTINATIONS

logger = logging.getLogger(__name__)

_HB = DESTINATIONS["hb"]


def fetch_travel_time(
    from_lat: float,
    from_lon: float,
    to_lat: float,
    to_lon: float,
    otp_base_url: str,
) -> int | None:
    """Fetch transit+walk travel time between two points via OTP.

    Calls ``GET /otp/routers/default/plan`` and extracts the first itinerary's
    duration.

    Args:
        from_lat: Origin latitude.
        from_lon: Origin longitude.
        to_lat: Destination latitude.
        to_lon: Destination longitude.
        otp_base_url: Base URL of the OTP instance.

    Returns:
        Travel time in minutes as an int, or None on error / no route.
    """
    url = f"{otp_base_url}/otp/routers/default/plan"
    params = {
        "fromPlace": f"{from_lat},{from_lon}",
        "toPlace": f"{to_lat},{to_lon}",
        "mode": "TRANSIT,WALK",
        "numItineraries": 1,
    }

    try:
        response = httpx.get(url, params=params)
        response.raise_for_status()
        data: dict = response.json()
    except httpx.HTTPError as exc:
        logger.warning("OTP plan request failed: %s", exc)
        return None

    itineraries = data.get("plan", {}).get("itineraries", [])
    if not itineraries:
        return None

    duration_seconds: int = itineraries[0].get("duration", 0)
    return int(duration_seconds) // 60


def compute_quartier_commute_hb(
    quartier_centroids: dict[int, tuple[float, float]],
    otp_base_url: str,
) -> dict[int, int | None]:
    """Compute travel time from each Quartier centroid to Zürich HB.

    Args:
        quartier_centroids: Mapping of quartier_id → (lat, lon).
        otp_base_url: Base URL of the OTP instance.

    Returns:
        Dict of quartier_id → travel time in minutes (or None on error).
    """
    hb_lat = _HB["lat"]
    hb_lon = _HB["lon"]

    result: dict[int, int | None] = {}
    for qid, (lat, lon) in quartier_centroids.items():
        minutes = fetch_travel_time(lat, lon, hb_lat, hb_lon, otp_base_url)
        result[qid] = minutes

    return result
