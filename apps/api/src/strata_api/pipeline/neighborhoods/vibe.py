"""Vibe profiles — explainable character tags per Quartier.

Tags are derived from each Quartier's metrics *relative to the citywide
distribution* (quartiles across all Quartiere), never from absolute magic
numbers. Every tag carries a human-readable evidence string, per the product
principle that every inference must be explainable.
"""
from __future__ import annotations

import math
from collections.abc import Callable

MAX_TAGS = 4

# Minimum venue counts so tiny areas don't produce artifact densities
_MIN_NIGHTLIFE_COUNT = 8
_MIN_CAFE_COUNT = 4
_MIN_SCHOOL_COUNT = 4
_MIN_CONSTRUCTION_COUNT = 4


def _quantile(values: list[float], q: float) -> float:
    """Nearest-rank quantile; values need not be sorted."""
    ordered = sorted(values)
    idx = max(0, math.ceil(q * len(ordered)) - 1)
    return ordered[idx]


def _metrics(props: dict) -> dict | None:
    """Extract the metric vector for one Quartier, or None without demographics."""
    if props.get("total_population") is None:
        return None
    area = props.get("area_km2")
    amenities = props.get("amenities")

    def per_km2(count: int | None) -> float | None:
        if count is None or area is None or area <= 0:
            return None
        return count / area

    nightlife = None
    if amenities is not None:
        nightlife = (amenities.get("bars") or 0) + (amenities.get("restaurants") or 0)

    construction = props.get("construction")
    construction_total = None
    if construction is not None:
        construction_total = (construction.get("approved_projects") or 0) + (
            construction.get("started_projects") or 0
        )

    return {
        "construction_total": construction_total,
        "young": props.get("age_18_29_pct"),
        "old": props.get("age_65plus_pct"),
        "foreign": props.get("foreign_pct"),
        "density": props.get("population_density"),
        "growth": props.get("growth_rate"),
        "nightlife_count": nightlife,
        "nightlife_km2": per_km2(nightlife),
        "cafes_count": amenities.get("cafes") if amenities else None,
        "cafes_km2": per_km2(amenities.get("cafes")) if amenities else None,
        "schools_count": amenities.get("schools") if amenities else None,
        "schools_km2": per_km2(amenities.get("schools")) if amenities else None,
        "amenity_km2": amenities.get("per_km2") if amenities else None,
    }


# (tag, summary phrase, builder) — order is priority; first MAX_TAGS wins
def _tag_builders() -> list[tuple[str, str, Callable[[dict, dict], str | None]]]:
    # "top" also requires clearing the bottom quartile (and vice versa) so a
    # degenerate distribution (everyone equal) produces no tag — and a quartier
    # can never be tagged both ends of the same metric.
    def top(metric: str, value_fmt: Callable[[float], str]):
        def check(m: dict, q: dict) -> str | None:
            v = m.get(metric)
            hi = q.get((metric, 0.75))
            lo = q.get((metric, 0.25))
            if v is None or hi is None or v < hi or v <= lo:
                return None
            return value_fmt(v)
        return check

    def bottom(metric: str, value_fmt: Callable[[float], str]):
        def check(m: dict, q: dict) -> str | None:
            v = m.get(metric)
            hi = q.get((metric, 0.75))
            lo = q.get((metric, 0.25))
            if v is None or lo is None or v > lo or v >= hi:
                return None
            return value_fmt(v)
        return check

    def with_min_count(inner, count_key: str, minimum: int):
        def check(m: dict, q: dict) -> str | None:
            if (m.get(count_key) or 0) < minimum:
                return None
            return inner(m, q)
        return check

    return [
        ("young crowd", "a young crowd",
         top("young", lambda v: f"{v:.0f}% aged 18–29 — top quartile in Zürich")),
        ("settled & older", "older and settled",
         top("old", lambda v: f"{v:.0f}% aged 65+ — top quartile in Zürich")),
        ("international", "strongly international",
         top("foreign", lambda v: f"{v:.0f}% foreign residents — top quartile in Zürich")),
        ("predominantly Swiss", "predominantly Swiss",
         bottom("foreign", lambda v: f"{v:.0f}% foreign residents — bottom quartile in Zürich")),
        ("nightlife hub", "buzzing bars and restaurants",
         with_min_count(
             top("nightlife_km2", lambda v: f"{v:.0f} bars & restaurants per km² — top quartile in Zürich"),
             "nightlife_count", _MIN_NIGHTLIFE_COUNT)),
        ("café culture", "thick with cafés",
         with_min_count(
             top("cafes_km2", lambda v: f"{v:.1f} cafés per km² — top quartile in Zürich"),
             "cafes_count", _MIN_CAFE_COUNT)),
        ("quiet residential", "quiet and residential",
         bottom("amenity_km2", lambda v: f"{v:.0f} amenities per km² — bottom quartile in Zürich")),
        ("dense urban fabric", "dense and urban",
         top("density", lambda v: f"{v:,.0f} residents per km² — top quartile in Zürich")),
        ("low-rise & spacious", "low-rise and spacious",
         bottom("density", lambda v: f"{v:,.0f} residents per km² — bottom quartile in Zürich")),
        ("family infrastructure", "strong family infrastructure",
         with_min_count(
             top("schools_km2", lambda v: f"{v:.1f} schools & kindergartens per km² — top quartile in Zürich"),
             "schools_count", _MIN_SCHOOL_COUNT)),
        ("rapidly growing", "growing fast",
         top("growth", lambda v: f"population grew {v:.1f}% year over year — top quartile in Zürich")),
        ("building boom", "a wave of new construction",
         with_min_count(
             top("construction_total",
                 lambda v: f"{v:.0f} new-construction projects approved or underway — top quartile in Zürich"),
             "construction_total", _MIN_CONSTRUCTION_COUNT)),
    ]


def _summary(phrases: list[str]) -> str:
    text = ", ".join(phrases[:3])
    return text[0].upper() + text[1:] + "."


def compute_vibes(features: list[dict]) -> dict[int, dict | None]:
    """Vibe profile per quartier_id from a full FeatureCollection's features.

    Needs all features at once: tags are quartile thresholds over the city.
    """
    all_metrics: dict[int, dict | None] = {}
    for feature in features:
        props = feature.get("properties", {})
        all_metrics[props.get("quartier_id")] = _metrics(props)

    # Quartile thresholds per metric over quartiere that have a value
    quantiles: dict[tuple[str, float], float] = {}
    metric_keys = {k for m in all_metrics.values() if m for k in m}
    for key in metric_keys:
        values = [m[key] for m in all_metrics.values() if m and m.get(key) is not None]
        if values:
            quantiles[(key, 0.75)] = _quantile(values, 0.75)
            quantiles[(key, 0.25)] = _quantile(values, 0.25)

    builders = _tag_builders()
    vibes: dict[int, dict | None] = {}
    for qid, metrics in all_metrics.items():
        if metrics is None:
            vibes[qid] = None
            continue
        tags: list[dict] = []
        phrases: list[str] = []
        for tag, phrase, build in builders:
            if len(tags) >= MAX_TAGS:
                break
            evidence = build(metrics, quantiles)
            if evidence is not None:
                tags.append({"tag": tag, "evidence": evidence})
                phrases.append(phrase)
        if not tags:
            tags.append({
                "tag": "balanced mix",
                "evidence": "no metric stands out from the citywide quartiles — an even profile",
            })
            phrases.append("an even, balanced profile")
        vibes[qid] = {"tags": tags, "summary": _summary(phrases)}
    return vibes
