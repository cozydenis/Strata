"""CLI entry point for the neighborhood intelligence pipeline.

Usage:
    uv run python -m strata_api.pipeline.neighborhoods [--amenities] [--green] [--rents]

Writes quartiere.geojson + noise.geojson + green_spaces.geojson to
apps/web/public/data and copies quartiere.geojson to apps/api/data/neighborhoods
for the API router.
--amenities fetches OSM amenities from Overpass (otherwise a cached
amenities_raw.json in the output dir is reused if present).
--green fetches OSM green space from Overpass (otherwise a cached
green_raw.json in the output dir is reused if present).
--rents computes per-quartier asking-rent statistics from the listings DB
(requires DATABASE_URL to point at a populated database).
"""
from __future__ import annotations

import argparse
import logging
from pathlib import Path

from strata_api.pipeline.neighborhoods.runner import run_neighborhood_pipeline

_API_ROOT = Path(__file__).resolve().parents[4]
_REPO_ROOT = _API_ROOT.parents[1]
DEFAULT_OUTPUT_DIR = _REPO_ROOT / "apps" / "web" / "public" / "data"
DEFAULT_API_DATA_DIR = _API_ROOT / "data" / "neighborhoods"


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the neighborhood intelligence pipeline.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_DIR, help="GeoJSON output directory")
    parser.add_argument("--api-data", type=Path, default=DEFAULT_API_DATA_DIR, help="API data directory")
    parser.add_argument("--amenities", action="store_true", help="Fetch OSM amenities from Overpass")
    parser.add_argument("--green", action="store_true", help="Fetch OSM green space from Overpass")
    parser.add_argument("--rents", action="store_true", help="Compute per-quartier rent stats from the listings DB")
    parser.add_argument("--skip-noise", action="store_true", help="Skip the slow noise cadastre download")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    stats = run_neighborhood_pipeline(
        args.output,
        api_data_dir=args.api_data,
        fetch_amenities=args.amenities,
        fetch_green=args.green,
        include_rents=args.rents,
        skip_noise=args.skip_noise,
    )
    logging.getLogger(__name__).info("Pipeline complete: %s", stats)


if __name__ == "__main__":
    main()
