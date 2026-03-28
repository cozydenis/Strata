"""Aggregate Quartier geometry and demographics into an enriched GeoJSON FeatureCollection."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from strata_api.pipeline.neighborhoods.demographics_parser import QuartierDemographics
    from strata_api.pipeline.neighborhoods.quartier_parser import QuartierRecord

# Lazy import: only used when otp_base_url is provided
_compute_commute: object = None  # populated on first use

PCT_DECIMAL_PLACES = 4


def _safe_pct(count: int, total: int) -> float | None:
    if total == 0:
        return None
    return round(count / total * 100, PCT_DECIMAL_PLACES)


def _growth_rate(yoy_change: int | None, total: int) -> float | None:
    if yoy_change is None:
        return None
    prior = total - yoy_change
    if prior == 0:
        return None
    return yoy_change / prior * 100


def _trend(yoy_change: int | None) -> str | None:
    if yoy_change is None:
        return "stable"
    if yoy_change > 0:
        return "growing"
    if yoy_change < 0:
        return "declining"
    return "stable"


def _null_demo_props() -> dict:
    """Return a properties dict with all demographic fields set to None."""
    return {
        "total_population": None,
        "population_density": None,
        "swiss_pct": None,
        "foreign_pct": None,
        "yoy_change": None,
        "growth_rate": None,
        "trend": "stable",
        "age_0_17_pct": None,
        "age_18_29_pct": None,
        "age_30_44_pct": None,
        "age_45_64_pct": None,
        "age_65plus_pct": None,
    }


def _demo_props(demo: QuartierDemographics, area_km2: float | None) -> dict:
    """Compute all demographic properties from a QuartierDemographics record."""
    total = demo.total_population

    density = (total / area_km2) if (area_km2 is not None and area_km2 > 0) else None

    buckets = demo.age_buckets
    return {
        "total_population": total,
        "population_density": density,
        "swiss_pct": _safe_pct(demo.swiss_count, total),
        "foreign_pct": _safe_pct(demo.foreign_count, total),
        "yoy_change": demo.yoy_change,
        "growth_rate": _growth_rate(demo.yoy_change, total),
        "trend": _trend(demo.yoy_change),
        "age_0_17_pct": _safe_pct(buckets.get("0-17", 0), total),
        "age_18_29_pct": _safe_pct(buckets.get("18-29", 0), total),
        "age_30_44_pct": _safe_pct(buckets.get("30-44", 0), total),
        "age_45_64_pct": _safe_pct(buckets.get("45-64", 0), total),
        "age_65plus_pct": _safe_pct(buckets.get("65+", 0), total),
    }


def aggregate_quartier_geojson(
    quartier_records: dict[int, QuartierRecord],
    demographics: dict[int, QuartierDemographics],
    otp_base_url: str | None = None,
) -> dict:
    """Produce an enriched GeoJSON FeatureCollection.

    Each Feature contains:
    - geometry from the QuartierRecord
    - base properties: quartier_id, quartier_name, kreis
    - demographic properties (or nulls if no demographic data exists)
    - commute_hb_min: travel time to Zürich HB in minutes (only when otp_base_url provided)
    """
    # Optionally compute commute times for all quartiere
    commute_times: dict[int, int | None] = {}
    if otp_base_url is not None:
        from strata_api.pipeline.commute.quartier_commute import compute_quartier_commute_hb

        centroids: dict[int, tuple[float, float]] = {}
        for qid, rec in quartier_records.items():
            # Use geometry centroid if available (simple bbox center fallback)
            geom = rec.geometry
            if geom and geom.get("type") == "Point":
                coords = geom["coordinates"]
                centroids[qid] = (coords[1], coords[0])  # lat, lon
        commute_times = compute_quartier_commute_hb(centroids, otp_base_url)

    features: list[dict] = []

    for qid, rec in quartier_records.items():
        base_props: dict = {
            "quartier_id": rec.quartier_id,
            "quartier_name": rec.quartier_name,
            "kreis": rec.kreis,
        }

        demo = demographics.get(qid)
        demo_p = _demo_props(demo, rec.area_km2) if demo is not None else _null_demo_props()

        commute_p: dict = {}
        if otp_base_url is not None:
            commute_p["commute_hb_min"] = commute_times.get(qid)

        features.append({
            "type": "Feature",
            "geometry": rec.geometry,
            "properties": {**base_props, **demo_p, **commute_p},
        })

    return {"type": "FeatureCollection", "features": features}
