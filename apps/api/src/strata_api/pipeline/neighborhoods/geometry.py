"""Shared point-in-polygon containment helpers (pure python ray casting, WGS84 lon/lat).

Extracted from amenities.py so amenities, green_space and rent_trends all share a
single implementation for assigning points to Quartier boundaries.
"""
from __future__ import annotations


def _point_in_ring(lon: float, lat: float, ring: list) -> bool:
    inside = False
    j = len(ring) - 1
    for i in range(len(ring)):
        xi, yi = ring[i][0], ring[i][1]
        xj, yj = ring[j][0], ring[j][1]
        if (yi > lat) != (yj > lat) and lon < (xj - xi) * (lat - yi) / (yj - yi) + xi:
            inside = not inside
        j = i
    return inside


def _point_in_polygon(lon: float, lat: float, rings: list) -> bool:
    if not rings or not _point_in_ring(lon, lat, rings[0]):
        return False
    # Inside the exterior ring — check it is not inside a hole
    return not any(_point_in_ring(lon, lat, hole) for hole in rings[1:])


def point_in_geometry(lon: float, lat: float, geometry: dict) -> bool:
    """True if (lon, lat) falls inside a GeoJSON Polygon or MultiPolygon."""
    gtype = geometry.get("type")
    if gtype == "Polygon":
        return _point_in_polygon(lon, lat, geometry.get("coordinates", []))
    if gtype == "MultiPolygon":
        return any(_point_in_polygon(lon, lat, rings) for rings in geometry.get("coordinates", []))
    return False
