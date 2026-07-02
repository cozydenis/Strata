"""Asking-rent statistics per Quartier from Strata's own listings corpus.

Produces, per Quartier:
  - rent_median_chf_m2:  median asking CHF/m² over *active* listings
  - rent_listing_count:  number of active listings behind that median
  - rent_trend:          monthly median CHF/m² over the last TREND_MONTHS months —
                         a listing counts in every month of its first_seen..last_seen
                         span; months with fewer than MIN_MONTHLY_N listings are omitted

Approximations (deliberate, documented):
  - Each listing uses its *final* rent_net across its whole visibility span;
    intermediate price changes in listing_history are not replayed. Asking-rent
    levels move slowly enough for a v1 trend line.
  - Quartier assignment is point-in-polygon on the listing's coordinates.
    Listings without coordinates, or outside every Quartier polygon, are skipped
    (counts logged) — no PLZ fallback, since PLZ↔Quartier is not a clean mapping.
  - Implausible records are excluded: rent_net <= 0 or area below MIN_AREA_M2.
"""
from __future__ import annotations

import datetime
import logging
import statistics
from dataclasses import dataclass

from sqlalchemy import Engine, select
from sqlalchemy.orm import Session

from strata_api.pipeline.neighborhoods.geometry import point_in_geometry
from strata_api.pipeline.neighborhoods.quartier_parser import QuartierRecord

logger = logging.getLogger(__name__)

MIN_AREA_M2 = 8.0     # below this, area is a data error and CHF/m² is meaningless
MIN_MONTHLY_N = 3     # a monthly median needs at least this many listings
TREND_MONTHS = 12     # trend window, counting back from `now` inclusive


@dataclass(frozen=True)
class ListingObservation:
    """The slice of a listing relevant to rent statistics."""

    rent_net: int | None
    area_m2: float | None
    lng: float | None
    lat: float | None
    first_seen: datetime.datetime
    last_seen: datetime.datetime
    is_active: bool


@dataclass(frozen=True)
class RentStats:
    """Per-quartier rent statistics, ready for GeoJSON property merging."""

    median_chf_m2: float | None
    listing_count: int
    trend: tuple[dict, ...]  # ({"month": "YYYY-MM", "median_chf_m2": float, "n": int}, ...)


def chf_per_m2(rent_net: int | None, area_m2: float | None) -> float | None:
    """Asking rent per m², or None when inputs are missing or implausible."""
    if rent_net is None or area_m2 is None:
        return None
    if rent_net <= 0 or area_m2 < MIN_AREA_M2:
        return None
    return round(rent_net / area_m2, 2)


def months_spanned(first_seen: datetime.datetime, last_seen: datetime.datetime) -> list[str]:
    """All "YYYY-MM" months the span touches, inclusive on both ends, ascending."""
    months: list[str] = []
    year, month = first_seen.year, first_seen.month
    while (year, month) <= (last_seen.year, last_seen.month):
        months.append(f"{year:04d}-{month:02d}")
        month += 1
        if month > 12:
            year, month = year + 1, 1
    return months


def _window_months(now: datetime.datetime) -> list[str]:
    """The last TREND_MONTHS months ending at `now`'s month, ascending."""
    year, month = now.year, now.month
    months: list[str] = []
    for _ in range(TREND_MONTHS):
        months.append(f"{year:04d}-{month:02d}")
        month -= 1
        if month < 1:
            year, month = year - 1, 12
    return sorted(months)


def _assign_quartier(obs: ListingObservation, quartiers: dict[int, QuartierRecord]) -> int | None:
    if obs.lng is None or obs.lat is None:
        return None
    for qid, rec in quartiers.items():
        if point_in_geometry(obs.lng, obs.lat, rec.geometry):
            return qid
    return None


def compute_rent_stats(
    listings: list[ListingObservation],
    quartiers: dict[int, QuartierRecord],
    now: datetime.datetime,
) -> dict[int, RentStats]:
    """Compute current-level and monthly-trend rent statistics per Quartier."""
    window = set(_window_months(now))
    current: dict[int, list[float]] = {qid: [] for qid in quartiers}
    monthly: dict[int, dict[str, list[float]]] = {qid: {} for qid in quartiers}

    skipped_value = skipped_coords = skipped_outside = 0
    for obs in listings:
        value = chf_per_m2(obs.rent_net, obs.area_m2)
        if value is None:
            skipped_value += 1
            continue
        if obs.lng is None or obs.lat is None:
            skipped_coords += 1
            continue
        qid = _assign_quartier(obs, quartiers)
        if qid is None:
            skipped_outside += 1
            continue

        if obs.is_active:
            current[qid].append(value)
        for month in months_spanned(obs.first_seen, obs.last_seen):
            if month in window:
                monthly[qid].setdefault(month, []).append(value)

    if skipped_value or skipped_coords or skipped_outside:
        logger.info(
            "rent_trends: skipped %d listings with implausible rent/area, %d without coordinates, %d outside all quartiers",
            skipped_value, skipped_coords, skipped_outside,
        )

    stats: dict[int, RentStats] = {}
    for qid in quartiers:
        values = current[qid]
        trend = tuple(
            {"month": month, "median_chf_m2": round(statistics.median(vals), 2), "n": len(vals)}
            for month, vals in sorted(monthly[qid].items())
            if len(vals) >= MIN_MONTHLY_N
        )
        stats[qid] = RentStats(
            median_chf_m2=round(statistics.median(values), 2) if values else None,
            listing_count=len(values),
            trend=trend,
        )
    return stats


def load_listing_observations(engine: Engine) -> list[ListingObservation]:
    """Load the rent-relevant listing slice from the database."""
    from strata_api.db.models.listing import Listing

    with Session(engine) as session:
        rows = session.execute(
            select(
                Listing.rent_net, Listing.area_m2, Listing.lng, Listing.lat,
                Listing.first_seen, Listing.last_seen, Listing.is_active,
            )
        ).all()
    return [
        ListingObservation(
            rent_net=r.rent_net, area_m2=r.area_m2, lng=r.lng, lat=r.lat,
            first_seen=r.first_seen, last_seen=r.last_seen, is_active=r.is_active,
        )
        for r in rows
    ]
