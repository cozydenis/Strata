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
from strata_api.pipeline.neighborhoods.construction_parser import parse_construction_csv
from strata_api.pipeline.neighborhoods.demographics_parser import parse_demographics_csv
from strata_api.pipeline.neighborhoods.downloader import (
    download_construction_csv,
    download_demographics_csv,
    download_noise_geojson,
    download_quartier_geojson,
)
from strata_api.pipeline.neighborhoods.green_space import (
    build_green_geojson,
    compute_green_metrics,
    fetch_overpass_green,
    parse_overpass_green,
)
from strata_api.pipeline.neighborhoods.noise_parser import parse_noise_geojson
from strata_api.pipeline.neighborhoods.quartier_parser import parse_quartier_geojson

logger = logging.getLogger(__name__)


def run_neighborhood_pipeline(
    output_dir: Path,
    api_data_dir: Path | None = None,
    fetch_amenities: bool = False,
    fetch_green: bool = False,
    include_rents: bool = False,
    skip_noise: bool = False,
) -> dict:
    """Orchestrate the neighborhood intelligence pipeline.

    Steps:
    1. Download Quartier WFS GeoJSON
    2. Download demographics CSV
    3. Download noise cadastre WFS GeoJSON
    4. Amenities: reuse output_dir/amenities_raw.json if present, else fetch
       from Overpass when fetch_amenities=True (skipped entirely otherwise)
    5. Green space: reuse output_dir/green_raw.json if present, else fetch from
       Overpass when fetch_green=True (skipped entirely otherwise)
    6. Parse all sources
    7. Aggregate into enriched GeoJSON FeatureCollection
    8. Write quartiere.geojson, noise.geojson and green_spaces.geojson to output_dir
       Also copies quartiere.geojson to api_data_dir if provided (for the API router).

    skip_noise=True skips the (slow, ~200 MB) noise download and leaves any
    existing noise.geojson untouched — useful when only quartier enrichment changed.

    Returns stats dict: {"quartiere": N, "noise_points": N|None, "year": YYYY, "amenities": N|None}
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Downloading Quartier boundaries...")
    quartier_raw = download_quartier_geojson()

    logger.info("Downloading demographics CSV...")
    demo_csv = download_demographics_csv()

    logger.info("Downloading construction projects CSV...")
    construction_csv = download_construction_csv()

    if skip_noise:
        logger.info("Skipping noise cadastre download (--skip-noise)")
        noise_raw = None
    else:
        logger.info("Downloading noise cadastre...")
        noise_raw = download_noise_geojson()

    logger.info("Parsing Quartier boundaries...")
    quartier_records = parse_quartier_geojson(quartier_raw)

    logger.info("Parsing demographics CSV...")
    demographics = parse_demographics_csv(demo_csv)

    logger.info("Parsing construction projects CSV...")
    construction = parse_construction_csv(construction_csv)

    noise_geojson: dict | None = None
    if noise_raw is not None:
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

        noise_geojson = {
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

    # ── Green space (cached raw Overpass response, network only when asked) ──
    green_metrics: dict[int, dict] | None = None
    green_geojson: dict | None = None
    green_area_count: int | None = None
    green_raw_path = output_dir / "green_raw.json"
    if green_raw_path.exists():
        logger.info("Reusing cached Overpass green data: %s", green_raw_path)
        green_raw = json.loads(green_raw_path.read_text(encoding="utf-8"))
    elif fetch_green:
        logger.info("Fetching green space from Overpass API...")
        green_raw = fetch_overpass_green()
        green_raw_path.write_text(json.dumps(green_raw, ensure_ascii=False), encoding="utf-8")
    else:
        green_raw = None

    if green_raw is not None:
        green_areas = parse_overpass_green(green_raw)
        populations = {qid: (d.total_population if (d := demographics.get(qid)) else None) for qid in quartier_records}
        green_metrics = compute_green_metrics(green_areas, quartier_records, populations)
        green_geojson = build_green_geojson(green_areas)
        green_area_count = sum(1 for m in green_metrics.values() if m["green_area_m2"] > 0)
        logger.info("Parsed %d green polygons; %d quartiere have green area", len(green_areas), green_area_count)

    # ── Rent trends (reads the listings DB; only when asked) ────────────────
    rent_stats = None
    if include_rents:
        import datetime

        from strata_api.db.session import get_engine
        from strata_api.pipeline.neighborhoods.rent_trends import compute_rent_stats, load_listing_observations

        try:
            observations = load_listing_observations(get_engine())
            rent_stats = compute_rent_stats(observations, quartier_records, now=datetime.datetime.utcnow())
            with_rents = sum(1 for s in rent_stats.values() if s.median_chf_m2 is not None)
            logger.info("Computed rent stats from %d listings; %d quartiere have medians", len(observations), with_rents)
        except Exception:
            logger.exception("Rent-trends step failed; continuing without rent properties")
            rent_stats = None

    logger.info("Aggregating into GeoJSON...")
    geojson = aggregate_quartier_geojson(
        quartier_records, demographics, amenities=amenity_counts, construction=construction, green=green_metrics,
        rents=rent_stats,
    )

    quartiere_path = output_dir / "quartiere.geojson"
    quartiere_path.write_text(json.dumps(geojson, ensure_ascii=False), encoding="utf-8")
    logger.info("Wrote %s (%d features)", quartiere_path, len(geojson["features"]))

    if noise_geojson is not None:
        noise_path = output_dir / "noise.geojson"
        noise_path.write_text(json.dumps(noise_geojson, ensure_ascii=False), encoding="utf-8")
        logger.info("Wrote %s (%d features)", noise_path, len(noise_geojson["features"]))

    if green_geojson is not None:
        green_path = output_dir / "green_spaces.geojson"
        green_path.write_text(json.dumps(green_geojson, ensure_ascii=False), encoding="utf-8")
        logger.info("Wrote %s (%d features)", green_path, len(green_geojson["features"]))

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
        "noise_points": len(noise_geojson["features"]) if noise_geojson is not None else None,
        "year": year,
        "amenities": amenity_total,
        "construction_quartiere": len(construction),
        "green_areas": green_area_count,
        "green_polygons": len(green_geojson["features"]) if green_geojson is not None else None,
        "rent_quartiere": (
            sum(1 for s in rent_stats.values() if s.median_chf_m2 is not None) if rent_stats is not None else None
        ),
    }
