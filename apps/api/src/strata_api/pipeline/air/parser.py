"""Pure parsing of Stadt Zürich UGZ air-quality data into frozen records.

Hourly measurement CSV (ugz_ogd_air_h1_<year>.csv)
--------------------------------------------------
Verified against the live 2026 file (downloaded 2026-07-01). The file is
UTF-8 with a BOM, comma-separated, with every string field double-quoted.

Columns:
  Datum      -> ISO timestamp with UTC offset, e.g. "2026-07-01T21:00+0100"
  Standort   -> station id, e.g. "Zch_Stampfenbachstrasse"
  Parameter  -> NO, NO2, NOx, O3, PM10, PM2.5 (station dependent)
  Intervall  -> aggregation interval, always "h1" for this dataset
  Einheit    -> unit, e.g. "µg/m3", "mg/m3", "ppb"
  Wert       -> measured value (float); may be empty when no measurement
  Status     -> "bereinigt" (validated) or "provisorisch" (provisional)

Status handling
---------------
Historic years are fully "bereinigt"; the *current* year is entirely
"provisorisch" (real-time, not yet quality-checked). Both represent genuine
measurements, so both are accepted by default — dropping provisional rows
would discard the entire current year. Rows whose status is anything else,
whose value is empty/non-numeric, or that are missing required columns are
skipped explicitly and counted in the log.

Station metadata JSON (uzg_ogd_metadaten.json)
----------------------------------------------
`{"Standorte": [{"ID", "Name", "Kurzname",
   "Koordinaten_WGS84_lat", "Koordinaten_WGS84_lng", "Adresse", ...}]}`
Coordinates are already WGS84 (lat/lng) — no LV95 transform needed.
"""

from __future__ import annotations

import csv
import io
import json
import logging
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

# Statuses that denote a usable measurement. See module docstring.
VALID_STATUSES: frozenset[str] = frozenset({"bereinigt", "provisorisch"})

_REQUIRED_COLUMNS = ("Datum", "Standort", "Parameter", "Einheit", "Wert", "Status")
_TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M%z"


@dataclass(frozen=True)
class AirMeasurement:
    """A single hourly air-quality measurement at one station."""

    station: str
    parameter: str
    timestamp: datetime
    value: float
    unit: str
    status: str


@dataclass(frozen=True)
class Station:
    """Air-quality measuring station location metadata (WGS84)."""

    station_id: str
    name: str
    short_name: str
    lat: float
    lng: float
    address: str | None


def _parse_timestamp(raw: str) -> datetime | None:
    """Parse a UGZ ISO timestamp like '2026-07-01T21:00+0100' (tz-aware)."""
    try:
        return datetime.strptime(raw.strip(), _TIMESTAMP_FORMAT)
    except (ValueError, AttributeError):
        return None


def parse_air_csv(csv_text: str, valid_statuses: frozenset[str] = VALID_STATUSES) -> list[AirMeasurement]:
    """Parse the UGZ hourly CSV into a list of AirMeasurement records.

    Skips (and logs a count for) rows that are missing required columns,
    have an empty/non-numeric value, an unparseable timestamp, or a status
    not in ``valid_statuses``. Never raises on individual bad rows.
    """
    text = csv_text.lstrip("﻿")
    reader = csv.DictReader(io.StringIO(text))

    measurements: list[AirMeasurement] = []
    skipped_missing = 0
    skipped_status = 0
    skipped_value = 0
    skipped_timestamp = 0

    for row in reader:
        if any(col not in row or row[col] is None for col in _REQUIRED_COLUMNS):
            skipped_missing += 1
            continue

        status = str(row["Status"]).strip()
        if status not in valid_statuses:
            skipped_status += 1
            continue

        raw_value = str(row["Wert"]).strip()
        if raw_value == "":
            skipped_value += 1
            continue
        try:
            value = float(raw_value)
        except ValueError:
            skipped_value += 1
            continue

        timestamp = _parse_timestamp(str(row["Datum"]))
        if timestamp is None:
            skipped_timestamp += 1
            continue

        measurements.append(
            AirMeasurement(
                station=str(row["Standort"]).strip(),
                parameter=str(row["Parameter"]).strip(),
                timestamp=timestamp,
                value=value,
                unit=str(row["Einheit"]).strip(),
                status=status,
            )
        )

    total_skipped = skipped_missing + skipped_status + skipped_value + skipped_timestamp
    if total_skipped:
        logger.info(
            "parse_air_csv: kept %d rows, skipped %d (missing_cols=%d, status=%d, value=%d, timestamp=%d)",
            len(measurements),
            total_skipped,
            skipped_missing,
            skipped_status,
            skipped_value,
            skipped_timestamp,
        )
    return measurements


def parse_stations(json_source: str | dict) -> dict[str, Station]:
    """Parse the station-metadata JSON into a map of station_id -> Station.

    Accepts raw JSON text or an already-decoded dict. Entries missing an ID or
    valid WGS84 coordinates are skipped and counted in the log.
    """
    data = json.loads(json_source) if isinstance(json_source, str) else json_source
    standorte = data.get("Standorte", []) if isinstance(data, dict) else []

    stations: dict[str, Station] = {}
    skipped = 0
    for entry in standorte:
        station_id = entry.get("ID")
        lat = entry.get("Koordinaten_WGS84_lat")
        lng = entry.get("Koordinaten_WGS84_lng")
        if not station_id or lat is None or lng is None:
            skipped += 1
            continue
        try:
            lat_f = float(lat)
            lng_f = float(lng)
        except (TypeError, ValueError):
            skipped += 1
            continue

        stations[station_id] = Station(
            station_id=station_id,
            name=str(entry.get("Name") or station_id),
            short_name=str(entry.get("Kurzname") or entry.get("Name") or station_id),
            lat=lat_f,
            lng=lng_f,
            address=(str(entry["Adresse"]) if entry.get("Adresse") else None),
        )

    if skipped:
        logger.info("parse_stations: kept %d stations, skipped %d incomplete entries", len(stations), skipped)
    return stations
