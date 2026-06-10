"""Neighborhood pipeline runner — orchestrates download → parse → aggregate → write."""
from __future__ import annotations

import json
import logging
from pathlib import Path

from strata_api.pipeline.neighborhoods.aggregator import aggregate_quartier_geojson
from strata_api.pipeline.neighborhoods.amenities import (
    count_amenities_per_quartier,
    fetch_overpass_amenities,
    parse_overpass_amenities,
)
from strata_api.pipeline.neighborhoods.demographics_parser import parse_demographics_csv
from strata_api.pipeline.neighborhoods.downloader import (
    download_demographics_csv,
    download_noise_geojson,
    download_quartier_geojson,
)
from strata_api.pipeline.neighborhoods.noise_parser import parse_noise_geojson
from strata_api.pipeline.neighborhoods.quartier_parser import parse_quartier_geojson

logger = logging.getLogger(__name__)


def run_neighborhood_pipeline(
    output_dir: Path,
    api_data_dir: Path | None = None,
    fetch_amenities: bool = False,
) -> dict:
    """Orchestrate the neighborhood intelligence pipeline.

    Steps:
    1. Download Quartier WFS GeoJSON
    2. Download demographics CSV
    3. Download noise cadastre WFS GeoJSON
    4. Amenities: reuse output_dir/amenities_raw.json if present, else fetch
       from Overpass when fetch_amenities=True (skipped entirely otherwise)
    5. Parse all sources
    6. Aggregate into enriched GeoJSON FeatureCollection
    7. Write quartiere.geojson and noise.geojson to output_dir
       Also copies quartiere.geojson to api_data_dir if provided (for the API router).

    Returns stats dict: {"quartiere": N, "noise_points": N, "year": YYYY, "amenities": N|None}
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

    # ── Amenities (cached raw Overpass response, network only when asked) ──
    amenity_counts: dict[int, dict[str, int]] | None = None
    amenity_total: int | None = None
    amenities_raw_path = output_dir / "amenities_raw.json"
    if amenities_raw_path.exists():
        logger.info("Reusing cached Overpass amenities: %s", amenities_raw_path)
        amenities_raw = json.loads(amenities_raw_path.read_text(encoding="utf-8"))
    elif fetch_amenities:
        logger.info("Fetching amenities from Overpass API...")
        amenities_raw = fetch_overpass_amenities()
        amenities_raw_path.write_text(json.dumps(amenities_raw, ensure_ascii=False), encoding="utf-8")
    else:
        amenities_raw = None

    if amenities_raw is not None:
        amenity_points = parse_overpass_amenities(amenities_raw)
        amenity_counts = count_amenities_per_quartier(amenity_points, quartier_records)
        amenity_total = sum(sum(c.values()) for c in amenity_counts.values())
        logger.info("Assigned %d of %d amenity points to quartiere", amenity_total, len(amenity_points))

    logger.info("Aggregating into GeoJSON...")
    geojson = aggregate_quartier_geojson(quartier_records, demographics, amenities=amenity_counts)

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
        "amenities": amenity_total,
    }
