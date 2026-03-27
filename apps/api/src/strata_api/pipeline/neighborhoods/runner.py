"""Neighborhood pipeline runner — orchestrates download → parse → aggregate → write."""
from __future__ import annotations

import json
import logging
from pathlib import Path

from strata_api.pipeline.neighborhoods.aggregator import aggregate_quartier_geojson
from strata_api.pipeline.neighborhoods.demographics_parser import parse_demographics_csv
from strata_api.pipeline.neighborhoods.downloader import (
    download_demographics_csv,
    download_noise_geojson,
    download_quartier_geojson,
)
from strata_api.pipeline.neighborhoods.noise_parser import parse_noise_geojson
from strata_api.pipeline.neighborhoods.quartier_parser import parse_quartier_geojson

logger = logging.getLogger(__name__)


def run_neighborhood_pipeline(output_dir: Path, api_data_dir: Path | None = None) -> dict:
    """Orchestrate the neighborhood intelligence pipeline.

    Steps:
    1. Download Quartier WFS GeoJSON
    2. Download demographics CSV
    3. Download noise cadastre WFS GeoJSON
    4. Parse all sources
    5. Aggregate into enriched GeoJSON FeatureCollection
    6. Write quartiere.geojson and noise.geojson to output_dir
       Also copies quartiere.geojson to api_data_dir if provided (for the API router).

    Returns stats dict: {"quartiere": N, "noise_points": N, "year": YYYY}
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Downloading Quartier boundaries...")
    quartier_raw = download_quartier_geojson()

    logger.info("Downloading demographics CSV...")
    demo_csv = download_demographics_csv()

    logger.info("Downloading noise cadastre...")
    noise_raw = download_noise_geojson()

    logger.info("Parsing Quartier boundaries...")
    quartier_records = parse_quartier_geojson(quartier_raw)

    logger.info("Parsing demographics CSV...")
    demographics = parse_demographics_csv(demo_csv)

    logger.info("Parsing noise cadastre...")
    noise_geojson_all = parse_noise_geojson(noise_raw)
    # Keep only moderate+ (>=50 dB day), then deduplicate on a ~11m grid
    # (4 decimal places) keeping max db_day per cell.  Strips Z coordinate and
    # renames db_day -> "d" to minimise the static file (200 MB -> ~8 MB).
    _grid: dict[tuple[float, float], float] = {}
    for f in noise_geojson_all["features"]:
        db = f["properties"].get("db_day") or 0
        if db < 50:
            continue
        coords = f["geometry"]["coordinates"]
        cell = (round(coords[0], 4), round(coords[1], 4))
        if cell not in _grid or db > _grid[cell]:
            _grid[cell] = db

    noise_geojson: dict = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [lon, lat]},
                "properties": {"d": round(db, 1)},
            }
            for (lon, lat), db in _grid.items()
        ],
    }

    logger.info("Aggregating into GeoJSON...")
    geojson = aggregate_quartier_geojson(quartier_records, demographics)

    quartiere_path = output_dir / "quartiere.geojson"
    quartiere_path.write_text(json.dumps(geojson, ensure_ascii=False), encoding="utf-8")
    logger.info("Wrote %s (%d features)", quartiere_path, len(geojson["features"]))

    noise_path = output_dir / "noise.geojson"
    noise_path.write_text(json.dumps(noise_geojson, ensure_ascii=False), encoding="utf-8")
    logger.info("Wrote %s (%d features)", noise_path, len(noise_geojson["features"]))

    # Also copy quartiere.geojson to the API data dir so the /neighborhoods API can read it
    if api_data_dir is not None:
        api_data_dir = Path(api_data_dir)
        api_data_dir.mkdir(parents=True, exist_ok=True)
        api_quartiere_path = api_data_dir / "quartiere.geojson"
        api_quartiere_path.write_text(json.dumps(geojson, ensure_ascii=False), encoding="utf-8")
        logger.info("Wrote API copy: %s", api_quartiere_path)

    year = max((d.year for d in demographics.values()), default=0)

    return {
        "quartiere": len(geojson["features"]),
        "noise_points": len(noise_geojson["features"]),
        "year": year,
    }
