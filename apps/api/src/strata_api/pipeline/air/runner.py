"""Air-quality pipeline runner — download → parse → aggregate → write GeoJSON."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from strata_api.pipeline.air.aggregator import aggregate_measurements
from strata_api.pipeline.air.downloader import download_air_csv, download_stations_json
from strata_api.pipeline.air.geojson import build_air_geojson
from strata_api.pipeline.air.parser import parse_air_csv, parse_stations

logger = logging.getLogger(__name__)

OUTPUT_FILENAME = "air_quality.geojson"


def run_air_pipeline(output_dir: Path, year: int | None = None) -> dict:
    """Run the air-quality pipeline and write ``air_quality.geojson``.

    Steps: download the hourly CSV + station metadata, parse both, aggregate to
    per-station summaries with LRV levels, build a station-point FeatureCollection
    and write it to ``output_dir``.

    Returns a stats dict: {"stations", "features", "measurements", "year",
    "levels"} where ``levels`` counts stations per overall level.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Downloading UGZ hourly air-quality CSV...")
    csv_text = download_air_csv(year)

    logger.info("Downloading UGZ station metadata...")
    stations_text = download_stations_json()

    logger.info("Parsing measurements + station metadata...")
    measurements = parse_air_csv(csv_text)
    stations = parse_stations(stations_text)

    logger.info("Aggregating %d measurements across %d stations...", len(measurements), len(stations))
    aggregates = aggregate_measurements(measurements)

    geojson = build_air_geojson(aggregates, stations)

    output_path = output_dir / OUTPUT_FILENAME
    output_path.write_text(json.dumps(geojson, ensure_ascii=False), encoding="utf-8")
    logger.info("Wrote %s (%d features)", output_path, len(geojson["features"]))

    level_counts: dict[str, int] = {}
    for agg in aggregates.values():
        key = agg.level or "unrated"
        level_counts[key] = level_counts.get(key, 0) + 1

    return {
        "measurements": len(measurements),
        "stations": len(aggregates),
        "features": len(geojson["features"]),
        "year": year,
        "levels": level_counts,
    }
