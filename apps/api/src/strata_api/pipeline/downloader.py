"""HTTP download helpers for GWR data sources."""
from __future__ import annotations

import io
import urllib.request
from typing import IO


# Stadt Zürich WFS endpoint (WFS 1.1.0, GeoJSON output)
# Layer names are lowercase; outputFormat must be the MIME type accepted by this server.
_WFS_BASE = (
    "https://www.ogd.stadt-zuerich.ch/wfs/geoportal/"
    "Gebaeude__und_Wohnungsregister_der_Stadt_Zuerich__GWZ__gemaess_GWR_Datenmodell"
    "?service=WFS&version=1.1.0&request=GetFeature"
    "&outputFormat=application/vnd.geo%2Bjson"
)
STADT_GEBAEUDE_URL = f"{_WFS_BASE}&typeName=gwr_stzh_gebaeude"
STADT_EINGAENGE_URL = f"{_WFS_BASE}&typeName=gwr_stzh_gebaeudeeingaenge"
STADT_WOHNUNGEN_URL = f"{_WFS_BASE}&typeName=gwr_stzh_wohnungen"

# Kanton Zürich open data CSV downloads
KANTON_GEBAEUDE_URL = (
    "https://www.web.statistik.zh.ch/ogd/daten/ressourcen/"
    "KTZH_00000124_00001783.csv"
)
KANTON_EINGAENGE_URL = (
    "https://www.web.statistik.zh.ch/ogd/daten/ressourcen/"
    "KTZH_00000124_00001784.csv"
)
KANTON_WOHNUNGEN_URL = (
    "https://www.web.statistik.zh.ch/ogd/daten/ressourcen/"
    "KTZH_00000124_00001785.csv"
)


def download_geojson(url: str) -> dict:
    """Fetch a GeoJSON URL and return parsed dict."""
    import json

    with urllib.request.urlopen(url, timeout=120) as resp:  # noqa: S310
        return json.loads(resp.read().decode("utf-8"))


def download_csv_stream(url: str) -> IO[str]:
    """Fetch a CSV URL and return a text stream (StringIO).

    Reads the entire response into memory — acceptable for canton CSVs
    which are typically <100 MB.
    """
    with urllib.request.urlopen(url, timeout=300) as resp:  # noqa: S310
        raw = resp.read().decode("utf-8-sig")  # strip BOM if present
    return io.StringIO(raw)
