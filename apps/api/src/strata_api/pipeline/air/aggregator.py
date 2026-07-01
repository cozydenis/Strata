"""Pure aggregation of air measurements into per-station summaries + LRV level.

For every station and parameter we compute the latest valid measurement and a
24-hour rolling mean (over the window ending at that station/parameter's latest
timestamp). Each station is then classified with an overall air-quality level
relative to the Swiss LRV limit values.

LRV limit values (Luftreinhalte-Verordnung, SR 814.318.142.1, Anhang 7)
-----------------------------------------------------------------------
Verified 2026-07-01 against BAFU / OSTLUFT (Immissionsgrenzwerte der LRV):

  NO2   : Jahresmittel 30 µg/m³ · 24-Std-Mittel 80 µg/m³ (max 1×/Jahr)
          · 95 %-Wert der ½-h-Werte 100 µg/m³
  O3    : 1-Std-Mittel 120 µg/m³ (max 1×/Jahr)
          · 98 %-Wert der ½-h-Werte eines Monats ≤ 100 µg/m³
  PM10  : Jahresmittel 20 µg/m³ · 24-Std-Mittel 50 µg/m³ (max 1×/Jahr)
  PM2.5 : Jahresmittel 10 µg/m³ (kein 24-Std-Grenzwert in der LRV)
  CO    : 24-Std-Mittel 8 mg/m³

Level classification (documented, honest thresholds)
----------------------------------------------------
Because we only have real-time hourly data, each parameter is compared against
the most relevant *short-term* LRV limit, using the statistic that limit is
defined over:

  NO2   -> 24h mean vs 80 µg/m³
  O3    -> latest hourly value vs 120 µg/m³
  PM10  -> 24h mean vs 50 µg/m³
  PM2.5 -> 24h mean vs the 10 µg/m³ annual limit (proxy — the LRV defines no
           24h PM2.5 limit; documented as such, not an official comparison)

NO and NOx have no LRV immission limit and are reported but not classified.

The ratio (value / limit) maps to a level:
  ratio ≤ 0.5            -> "good"
  0.5 < ratio ≤ 1.0      -> "moderate"
  ratio > 1.0            -> "high"   (LRV limit exceeded)

A station's overall level is the worst level among its classified parameters.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

# --- LRV Immissionsgrenzwerte (see module docstring for sources) -------------
LRV_NO2_ANNUAL_UGM3 = 30.0
LRV_NO2_24H_UGM3 = 80.0
LRV_NO2_95PCT_UGM3 = 100.0
LRV_O3_1H_UGM3 = 120.0
LRV_O3_98PCT_UGM3 = 100.0
LRV_PM10_ANNUAL_UGM3 = 20.0
LRV_PM10_24H_UGM3 = 50.0
LRV_PM25_ANNUAL_UGM3 = 10.0
LRV_CO_24H_MGM3 = 8.0

_STAT_LATEST = "latest"
_STAT_MEAN_24H = "mean_24h"

# parameter -> (limit value, which statistic to compare). Parameters absent
# here (NO, NOx) are reported but not classified.
_CLASSIFICATION: dict[str, tuple[float, str]] = {
    "NO2": (LRV_NO2_24H_UGM3, _STAT_MEAN_24H),
    "O3": (LRV_O3_1H_UGM3, _STAT_LATEST),
    "PM10": (LRV_PM10_24H_UGM3, _STAT_MEAN_24H),
    "PM2.5": (LRV_PM25_ANNUAL_UGM3, _STAT_MEAN_24H),
}

_GOOD_RATIO = 0.5
_MODERATE_RATIO = 1.0

LEVEL_GOOD = "good"
LEVEL_MODERATE = "moderate"
LEVEL_HIGH = "high"

_LEVEL_RANK = {LEVEL_GOOD: 0, LEVEL_MODERATE: 1, LEVEL_HIGH: 2}

_MEAN_WINDOW = timedelta(hours=24)


@dataclass(frozen=True)
class ParameterSummary:
    """Aggregated view of a single parameter at a single station."""

    parameter: str
    latest_value: float
    latest_at: datetime
    unit: str
    mean_24h: float | None
    level: str | None


@dataclass(frozen=True)
class StationAggregate:
    """All parameter summaries + an overall level for one station."""

    station: str
    measured_at: datetime
    parameters: dict[str, ParameterSummary]
    level: str | None


def _classify(parameter: str, latest_value: float, mean_24h: float | None) -> str | None:
    """Classify one parameter's level against its LRV limit, or None if unrated."""
    rule = _CLASSIFICATION.get(parameter)
    if rule is None:
        return None
    limit, stat = rule
    reference = latest_value if stat == _STAT_LATEST else mean_24h
    if reference is None or limit <= 0:
        return None
    ratio = reference / limit
    if ratio <= _GOOD_RATIO:
        return LEVEL_GOOD
    if ratio <= _MODERATE_RATIO:
        return LEVEL_MODERATE
    return LEVEL_HIGH


def _worst_level(levels: list[str]) -> str | None:
    """Return the highest-severity level, or None if the list is empty."""
    rated = [level for level in levels if level is not None]
    if not rated:
        return None
    return max(rated, key=lambda level: _LEVEL_RANK[level])


def _summarize_parameter(parameter: str, records: list) -> ParameterSummary:
    """Build a ParameterSummary from that parameter's measurements at one station."""
    ordered = sorted(records, key=lambda m: m.timestamp)
    latest = ordered[-1]

    window_start = latest.timestamp - _MEAN_WINDOW
    window_values = [m.value for m in ordered if m.timestamp > window_start]
    mean_24h = round(sum(window_values) / len(window_values), 3) if window_values else None

    level = _classify(parameter, latest.value, mean_24h)
    return ParameterSummary(
        parameter=parameter,
        latest_value=latest.value,
        latest_at=latest.timestamp,
        unit=latest.unit,
        mean_24h=mean_24h,
        level=level,
    )


def aggregate_measurements(measurements: list) -> dict[str, StationAggregate]:
    """Aggregate flat measurements into per-station, per-parameter summaries.

    Returns a map of station id -> StationAggregate. Stations/parameters with no
    measurements simply do not appear. Pure — no I/O.
    """
    by_station: dict[str, dict[str, list]] = {}
    for m in measurements:
        by_station.setdefault(m.station, {}).setdefault(m.parameter, []).append(m)

    aggregates: dict[str, StationAggregate] = {}
    for station, params in by_station.items():
        summaries: dict[str, ParameterSummary] = {}
        for parameter, records in params.items():
            if records:
                summaries[parameter] = _summarize_parameter(parameter, records)

        if not summaries:
            continue

        measured_at = max(s.latest_at for s in summaries.values())
        overall = _worst_level([s.level for s in summaries.values() if s.level is not None])
        aggregates[station] = StationAggregate(
            station=station,
            measured_at=measured_at,
            parameters=summaries,
            level=overall,
        )

    return aggregates
