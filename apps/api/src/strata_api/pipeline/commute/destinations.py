"""Preset commute destinations and isochrone contour configuration."""
from __future__ import annotations

DESTINATIONS: dict[str, dict] = {
    "hb": {"name": "Zürich HB", "lat": 47.3769, "lon": 8.5417},
    "eth": {"name": "ETH Zentrum", "lat": 47.3763, "lon": 8.5482},
    "airport": {"name": "Flughafen", "lat": 47.4502, "lon": 8.5622},
    "technopark": {"name": "Technopark", "lat": 47.3901, "lon": 8.5158},
}

CONTOUR_MINUTES: list[int] = [10, 20, 30, 45]
