"""Air-quality data pipeline (Stadt Zürich UGZ hourly measurements).

Pipeline stages (each a small, focused module):
- downloader: fetch the current-year hourly CSV + station metadata JSON.
- parser: CSV/JSON text -> frozen dataclass records (pure).
- aggregator: latest + 24h-mean per station/parameter + LRV level (pure).
- geojson: build a station-point FeatureCollection (pure).
- runner / __main__: orchestrate download -> parse -> aggregate -> write.
"""

from __future__ import annotations
