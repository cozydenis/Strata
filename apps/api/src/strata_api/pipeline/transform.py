"""Coordinate transformation and type-coercion helpers for the GWR pipeline."""
from __future__ import annotations

from pyproj import Transformer

# LV95 (Swiss national grid) → WGS84.  always_xy=True ensures (east, north) → (lon, lat).
_LV95_TO_WGS84 = Transformer.from_crs("EPSG:2056", "EPSG:4326", always_xy=True)


def lv95_to_wgs84(
    e: float | None,
    n: float | None,
) -> tuple[float | None, float | None]:
    """Convert LV95 easting/northing to (lat, lon) WGS84.

    Returns (None, None) if either coordinate is missing.
    """
    if e is None or n is None:
        return None, None
    lon, lat = _LV95_TO_WGS84.transform(float(e), float(n))
    return float(lat), float(lon)


def parse_optional_int(value: object) -> int | None:
    """Coerce *value* to int, returning None for empty / non-numeric input."""
    if value is None:
        return None
    if isinstance(value, int):
        return value
    try:
        return int(str(value).strip())
    except (ValueError, TypeError):
        return None


def parse_optional_float(value: object) -> float | None:
    """Coerce *value* to float, returning None for empty / non-numeric input."""
    if value is None:
        return None
    if isinstance(value, float):
        return value
    try:
        return float(str(value).strip())
    except (ValueError, TypeError):
        return None
