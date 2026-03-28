"""Neighborhoods API — quartier profiles with demographic intelligence."""
from __future__ import annotations

import json
import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/neighborhoods", tags=["neighborhoods"])

# Default path to the pre-generated quartiere.geojson.
# Resolved relative to the project data directory at import time.
# Tests may override this module-level variable via patch().
_QUARTIERE_PATH: Path = (
    Path(__file__).resolve().parents[3] / "data" / "neighborhoods" / "quartiere.geojson"
)

# Module-level cache: None = not yet loaded, dict = loaded data
_cache: dict | None = None


def _reset_cache() -> None:
    """Reset the module-level cache (used in tests)."""
    global _cache
    _cache = None


def _load_geojson() -> dict:
    """Load and cache the quartiere.geojson FeatureCollection."""
    global _cache
    if _cache is not None:
        return _cache
    if not _QUARTIERE_PATH.exists():
        logger.warning("quartiere.geojson not found at %s — run neighborhood pipeline first", _QUARTIERE_PATH)
        _cache = {"type": "FeatureCollection", "features": []}
        return _cache
    _cache = json.loads(_QUARTIERE_PATH.read_text(encoding="utf-8"))
    return _cache


def _find_feature(geojson: dict, quartier_id: int) -> dict | None:
    for feat in geojson.get("features", []):
        if feat.get("properties", {}).get("quartier_id") == quartier_id:
            return feat
    return None


def _build_profile(feat: dict) -> dict:
    """Transform a GeoJSON feature into the API response shape."""
    p = feat.get("properties", {})

    age_distribution = [
        {"bucket": "0-17", "pct": p.get("age_0_17_pct")},
        {"bucket": "18-29", "pct": p.get("age_18_29_pct")},
        {"bucket": "30-44", "pct": p.get("age_30_44_pct")},
        {"bucket": "45-64", "pct": p.get("age_45_64_pct")},
        {"bucket": "65+", "pct": p.get("age_65plus_pct")},
    ]

    return {
        "quartier_id": p.get("quartier_id"),
        "quartier_name": p.get("quartier_name"),
        "kreis": p.get("kreis"),
        "population": {
            "total": p.get("total_population"),
            "density_per_km2": p.get("population_density"),
            "swiss_pct": p.get("swiss_pct"),
            "foreign_pct": p.get("foreign_pct"),
            "growth_rate": p.get("growth_rate"),
            "trend": p.get("trend"),
        },
        "age_distribution": age_distribution,
        "commute_hb_min": p.get("commute_hb_min"),
    }


@router.get("/{quartier_id}/profile")
def get_quartier_profile(quartier_id: int) -> dict:
    """Return demographic profile for a Quartier by ID."""
    geojson = _load_geojson()
    feat = _find_feature(geojson, quartier_id)
    if feat is None:
        raise HTTPException(status_code=404, detail="Quartier not found")
    return _build_profile(feat)
