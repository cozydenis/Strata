"""Quartierüblichkeit — comparables math for initial-rent (OR Art. 270) analysis.

The "absolute method" of contesting an initial rent relies on *Quartierüblichkeit*:
comparing the rent of a flat with rents customary in the same quarter for
comparable objects (OR Art. 269a lit. a). A proper legal comparison needs at
least five genuinely comparable objects with documented characteristics.

Strata cannot produce a court-grade comparison. Instead it *approximates*
Quartierüblichkeit from its own listings corpus (asking rents, not concluded
rents) to give tenants an INDICATIVE signal of whether an asking rent looks
elevated versus the neighbourhood. Every result therefore carries an explicit
"not legal advice" framing, mirroring ``legal/herabsetzung.py``.

This module is pure math: it never touches the database. The router feeds it a
target listing and a candidate pool; selection + statistics happen here.
"""
from __future__ import annotations

import datetime
import statistics
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol


class ListingLike(Protocol):
    """Structural type for the listing fields this module reads.

    Both the SQLAlchemy ``Listing`` ORM object and lightweight test doubles
    satisfy it — the module never imports the DB model.
    """

    id: int
    rooms: float | None
    area_m2: float | None
    rent_net: float | None
    plz: int | None
    last_seen: datetime.datetime


# --- Comparison criteria (documented constants) ------------------------------
# Rooms within ±0.5 of the target: half-room granularity is how Swiss flats are
# advertised, so 3.5 rooms is comparable to 3.0/4.0 but not to 2.5/4.5.
ROOMS_TOLERANCE = 0.5
# Area within ±20% of the target: broad enough to gather a usable sample, tight
# enough that CHF/m² stays meaningful.
AREA_TOLERANCE_PCT = 0.20
# Only listings seen within the last 24 months count — older asking rents are a
# poor proxy for the current market.
RECENCY_MONTHS = 24
# Fewer than 5 comparables is not a defensible basis for any statement about the
# quarter, so the verdict is withheld (mirrors the legal 5-object minimum).
MIN_COMPARABLES = 5
# A target is only flagged "clearly above market" once it exceeds the 75th
# percentile by more than 10%. The margin is deliberately conservative: it
# favours false negatives (staying silent) over false positives (wrongly
# implying a contestable rent), because this is an indicative, not legal, tool.
CLEARLY_ABOVE_FACTOR = 1.10


@dataclass(frozen=True)
class ComparableCriteria:
    """Filters defining which listings count as comparable to a target."""

    rooms_tolerance: float = ROOMS_TOLERANCE
    area_tolerance_pct: float = AREA_TOLERANCE_PCT
    recency_months: int = RECENCY_MONTHS


DEFAULT_CRITERIA = ComparableCriteria()


class Verdict(StrEnum):
    """Indicative classification of a target's asking rent vs. the quarter."""

    INSUFFICIENT_DATA = "insufficient_data"
    WITHIN_RANGE = "within_range"
    ABOVE_MARKET = "above_market"
    CLEARLY_ABOVE_MARKET = "clearly_above_market"


@dataclass(frozen=True)
class InitialRentAnalysis:
    """Result of an indicative Quartierüblichkeit comparison."""

    verdict: Verdict
    target_chf_m2: float | None
    median_chf_m2: float | None
    p25_chf_m2: float | None
    p75_chf_m2: float | None
    comparable_count: int
    explanation: str


def _subtract_months(moment: datetime.datetime, months: int) -> datetime.datetime:
    """Return ``moment`` shifted back by ``months`` calendar months (day-clamped)."""
    total = (moment.year * 12 + (moment.month - 1)) - months
    year, month = divmod(total, 12)
    month += 1
    # Clamp the day so e.g. shifting from the 31st into a shorter month is valid.
    day = min(moment.day, [31, 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28,
                           31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1])
    return moment.replace(year=year, month=month, day=day)


def _chf_per_m2(listing: ListingLike) -> float | None:
    """CHF/m² of net rent for a listing, or None if rent or area is missing/invalid."""
    if listing.rent_net is None or listing.area_m2 is None or listing.area_m2 <= 0:
        return None
    return round(listing.rent_net / listing.area_m2, 2)


def _nearest_rank_percentile(sorted_values: list[float], pct: float) -> float:
    """Nearest-rank percentile of an already-sorted, non-empty list.

    rank = ceil(pct/100 * N), clamped to [1, N]; returns the rank-th value.
    Simple and exactly reproducible — the tests pin the expected outputs.
    """
    n = len(sorted_values)
    rank = -(-int(pct) * n // 100)  # ceil(pct * n / 100) via floor-division trick
    rank = max(1, min(rank, n))
    return sorted_values[rank - 1]


def select_comparables(
    target: ListingLike,
    candidates: list[ListingLike],
    *,
    criteria: ComparableCriteria = DEFAULT_CRITERIA,
    now: datetime.datetime | None = None,
) -> list[ListingLike]:
    """Filter ``candidates`` down to those comparable to ``target``.

    Excludes: the target itself (by id), listings missing rent_net or area_m2,
    a different PLZ, rooms outside ±tolerance, area outside ±tolerance, and
    listings last seen before the recency window. If the target lacks an area
    (or rooms, when comparing) the result is empty — comparability is undefined.
    """
    if target.area_m2 is None or target.area_m2 <= 0:
        return []
    now = now or datetime.datetime.utcnow()
    cutoff = _subtract_months(now, criteria.recency_months)
    area_lo = target.area_m2 * (1 - criteria.area_tolerance_pct)
    area_hi = target.area_m2 * (1 + criteria.area_tolerance_pct)

    selected: list[ListingLike] = []
    for c in candidates:
        if c.id == target.id:
            continue
        if c.rent_net is None or c.area_m2 is None or c.area_m2 <= 0:
            continue
        if c.plz != target.plz:
            continue
        if target.rooms is not None and (
            c.rooms is None or abs(c.rooms - target.rooms) > criteria.rooms_tolerance
        ):
            continue
        if not (area_lo <= c.area_m2 <= area_hi):
            continue
        if c.last_seen < cutoff:
            continue
        selected.append(c)
    return selected


def _classify(target_chf_m2: float, p75: float, count: int) -> Verdict:
    if count < MIN_COMPARABLES:
        return Verdict.INSUFFICIENT_DATA
    if target_chf_m2 <= p75:
        return Verdict.WITHIN_RANGE
    if target_chf_m2 <= p75 * CLEARLY_ABOVE_FACTOR:
        return Verdict.ABOVE_MARKET
    return Verdict.CLEARLY_ABOVE_MARKET


_DISCLAIMER = (
    "This is an indicative comparison against Strata's listing corpus (asking rents), "
    "not a Quartierüblichkeit expert report and not legal advice."
)


def analyze_initial_rent(
    target: ListingLike,
    comparables: list[ListingLike],
) -> InitialRentAnalysis:
    """Compute an indicative initial-rent verdict for ``target`` vs. ``comparables``.

    ``comparables`` should already be filtered via :func:`select_comparables`.
    """
    target_chf_m2 = _chf_per_m2(target)
    values = sorted(v for v in (_chf_per_m2(c) for c in comparables) if v is not None)
    count = len(values)

    if target_chf_m2 is None:
        return InitialRentAnalysis(
            verdict=Verdict.INSUFFICIENT_DATA,
            target_chf_m2=None,
            median_chf_m2=None,
            p25_chf_m2=None,
            p75_chf_m2=None,
            comparable_count=count,
            explanation=(
                "This listing has no net rent and/or living area on record, so its "
                f"CHF/m² cannot be computed. No indicative comparison is possible. {_DISCLAIMER}"
            ),
        )

    if count < MIN_COMPARABLES:
        return InitialRentAnalysis(
            verdict=Verdict.INSUFFICIENT_DATA,
            target_chf_m2=target_chf_m2,
            median_chf_m2=None,
            p25_chf_m2=None,
            p75_chf_m2=None,
            comparable_count=count,
            explanation=(
                f"Only {count} comparable listing(s) found in this quarter "
                f"(minimum {MIN_COMPARABLES} required). Asking rent is CHF {target_chf_m2:.1f}/m², "
                f"but there is not enough local data for an indicative verdict. {_DISCLAIMER}"
            ),
        )

    median = round(statistics.median(values), 2)
    p25 = _nearest_rank_percentile(values, 25)
    p75 = _nearest_rank_percentile(values, 75)
    verdict = _classify(target_chf_m2, p75, count)

    explanation = (
        f"Asking CHF {target_chf_m2:.1f}/m² vs. quartier median CHF {median:.1f}/m² "
        f"(p25 CHF {p25:.1f}, p75 CHF {p75:.1f}) across {count} comparable listings. "
        f"{_verdict_sentence(verdict, target_chf_m2, p75)} {_DISCLAIMER}"
    )
    return InitialRentAnalysis(
        verdict=verdict,
        target_chf_m2=target_chf_m2,
        median_chf_m2=median,
        p25_chf_m2=p25,
        p75_chf_m2=p75,
        comparable_count=count,
        explanation=explanation,
    )


def _verdict_sentence(verdict: Verdict, target_chf_m2: float, p75: float) -> str:
    if verdict is Verdict.WITHIN_RANGE:
        return "The asking rent sits within the customary range for the quarter (at or below the 75th percentile)."
    if verdict is Verdict.ABOVE_MARKET:
        return (
            f"The asking rent is above the 75th percentile (CHF {p75:.1f}/m²) but within 10% of it — "
            "somewhat elevated, worth a closer look."
        )
    if verdict is Verdict.CLEARLY_ABOVE_MARKET:
        return (
            f"The asking rent exceeds the 75th percentile (CHF {p75:.1f}/m²) by more than 10% — "
            "clearly elevated versus the neighbourhood; an initial-rent challenge may be worth exploring."
        )
    return "There is not enough local data for an indicative verdict."
