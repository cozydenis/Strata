"""Download Stadt Zürich UGZ air-quality data (stdlib urllib only).

Dataset: "Luftschadstoffmessung Stundenwerte" (ugz_luftschadstoffmessung_stundenwerte)
on data.stadt-zuerich.ch. One hourly CSV per year plus a station-metadata JSON.
The metadata resource is served gzip-compressed, so responses are transparently
decompressed when the gzip magic bytes are present.
"""

from __future__ import annotations

import gzip
import urllib.request
from datetime import datetime

_USER_AGENT = "Strata-Pipeline/1.0 (research; contact: hello@strata.ch)"

_DATASET_BASE = "https://data.stadt-zuerich.ch/dataset/ugz_luftschadstoffmessung_stundenwerte/download"
_AIR_CSV_TEMPLATE = _DATASET_BASE + "/ugz_ogd_air_h1_{year}.csv"
_STATIONS_URL = _DATASET_BASE + "/uzg_ogd_metadaten.json"

_GZIP_MAGIC = b"\x1f\x8b"


def air_csv_url(year: int) -> str:
    """Return the hourly-measurement CSV URL for a given year."""
    return _AIR_CSV_TEMPLATE.format(year=year)


def stations_url() -> str:
    """Return the station-metadata JSON URL."""
    return _STATIONS_URL


def _fetch_bytes(url: str, timeout: int = 120) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 (fixed https hosts)
        raw = resp.read()
    if raw[:2] == _GZIP_MAGIC:
        return gzip.decompress(raw)
    return raw


def download_air_csv(year: int | None = None, timeout: int = 120) -> str:
    """Download the hourly-measurement CSV for ``year`` (default: current year)."""
    resolved_year = year if year is not None else datetime.now().year
    raw = _fetch_bytes(air_csv_url(resolved_year), timeout=timeout)
    return raw.decode("utf-8", errors="replace")


def download_stations_json(timeout: int = 60) -> str:
    """Download the station-metadata JSON (transparently gunzipped) as text."""
    raw = _fetch_bytes(_STATIONS_URL, timeout=timeout)
    return raw.decode("utf-8", errors="replace")
