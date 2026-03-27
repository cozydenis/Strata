"""Download neighborhood data from Stadt Zürich open data sources.

Sources (discovered via recon):
- Quartier WFS GeoJSON: ogd.stadt-zuerich.ch WFS
- Demographics CSV: CKAN dataset -> direct CSV download URL
- Noise cadastre WFS: ogd.stadt-zuerich.ch WFS, typename=strlaerm_ep
"""
from __future__ import annotations

import json
import urllib.request

_USER_AGENT = "Strata-Pipeline/1.0 (research; contact: hello@strata.ch)"

_QUARTIER_WFS_URL = (
    "https://www.ogd.stadt-zuerich.ch/wfs/geoportal/Statistische_Quartiere"
    "?service=WFS&version=1.1.0&request=GetFeature"
    "&typename=adm_statistische_quartiere_map&outputFormat=GeoJSON"
)

_DEMOGRAPHICS_CSV_URL = (
    "https://data.stadt-zuerich.ch/dataset/"
    "bev_bestand_jahr_quartier_alter_herkunft_geschlecht_od3903/"
    "download/BEV390OD3903.csv"
)

_NOISE_WFS_BASE = (
    "https://www.ogd.stadt-zuerich.ch/wfs/geoportal/Strassenlaermkataster_der_Stadt_Zuerich"
    "?service=WFS&version=1.1.0&request=GetFeature"
    "&typename=strlaerm_ep&outputFormat=GeoJSON"
)
_NOISE_PAGE_SIZE = 50_000


def _fetch_bytes(url: str, timeout: int = 60) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def download_quartier_geojson() -> dict:
    """Fetch the Quartier WFS GeoJSON and return parsed dict."""
    raw = _fetch_bytes(_QUARTIER_WFS_URL, timeout=60)
    return json.loads(raw)


def download_demographics_csv() -> str:
    """Download the demographics CSV and return as text."""
    raw = _fetch_bytes(_DEMOGRAPHICS_CSV_URL, timeout=120)
    return raw.decode("utf-8", errors="replace")


def download_noise_geojson() -> dict:
    """Fetch the full noise cadastre WFS GeoJSON (strlaerm_ep) via paginated requests.

    The WFS server returns features in object-ID order and caps results per request,
    so a single maxFeatures fetch gives a spatially biased northeast-only sample.
    Pagination via startIndex gives full city coverage.
    """
    all_features: list[dict] = []
    offset = 0
    while True:
        url = (
            f"{_NOISE_WFS_BASE}"
            f"&maxFeatures={_NOISE_PAGE_SIZE}"
            f"&startIndex={offset}"
        )
        raw = _fetch_bytes(url, timeout=120)
        page = json.loads(raw)
        features = page.get("features") or []
        all_features.extend(features)
        if len(features) < _NOISE_PAGE_SIZE:
            break
        offset += _NOISE_PAGE_SIZE
    return {"type": "FeatureCollection", "features": all_features}
