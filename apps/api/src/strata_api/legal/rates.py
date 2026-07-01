"""Referenzzinssatz history and current-value resolution.

The BWO (Bundesamt für Wohnungswesen) publishes the mortgage reference rate
quarterly, rounded to the nearest 0.25. RATE_HISTORY is the documented series of
change points; the current value (1.25% — verified against bwo.admin.ch, June
2026, unchanged since Sept 2025) is the last entry.

At runtime the DB `reference_rates` table is the source of truth (seeded from
this series via migration). These pure helpers back that seed and the
"assumed from first_seen" inference for listings without a recorded base rate.
"""
from __future__ import annotations

import datetime

# (effective_date, rate_percent) — documented BWO series, ascending by date.
RATE_HISTORY: tuple[tuple[datetime.date, float], ...] = (
    (datetime.date(2008, 9, 1), 3.50),
    (datetime.date(2009, 6, 1), 3.25),
    (datetime.date(2009, 9, 1), 3.00),
    (datetime.date(2010, 6, 1), 2.75),
    (datetime.date(2011, 9, 1), 2.50),
    (datetime.date(2012, 6, 1), 2.25),
    (datetime.date(2013, 9, 1), 2.00),
    (datetime.date(2015, 6, 1), 1.75),
    (datetime.date(2017, 6, 1), 1.50),
    (datetime.date(2020, 3, 1), 1.25),
    (datetime.date(2023, 6, 1), 1.50),
    (datetime.date(2023, 12, 1), 1.75),
    (datetime.date(2025, 3, 3), 1.50),
    (datetime.date(2025, 9, 1), 1.25),
)

FALLBACK_REFERENCE_RATE: float = 1.25


def rate_at(on_date: datetime.date | datetime.datetime, history=RATE_HISTORY) -> float | None:
    """Return the reference rate effective on ``on_date``, or None if before the series."""
    if isinstance(on_date, datetime.datetime):
        on_date = on_date.date()
    effective: float | None = None
    for eff_date, rate in history:
        if eff_date <= on_date:
            effective = rate
        else:
            break
    return effective


def latest_rate(history=RATE_HISTORY) -> float:
    """Return the most recent rate in the documented series."""
    return history[-1][1]
