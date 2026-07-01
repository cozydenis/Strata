"""CLI entry point for the air-quality pipeline.

Usage:
    uv run python -m strata_api.pipeline.air [--year YYYY] [--output DIR]

Writes air_quality.geojson to apps/web/public/data (same location as the
neighborhoods pipeline output).
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from strata_api.pipeline.air.runner import run_air_pipeline

_API_ROOT = Path(__file__).resolve().parents[4]
_REPO_ROOT = _API_ROOT.parents[1]
DEFAULT_OUTPUT_DIR = _REPO_ROOT / "apps" / "web" / "public" / "data"


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the air-quality pipeline.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_DIR, help="GeoJSON output directory")
    parser.add_argument("--year", type=int, default=None, help="Measurement year (default: current year)")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    stats = run_air_pipeline(args.output, year=args.year)
    logging.getLogger(__name__).info("Air pipeline complete: %s", stats)


if __name__ == "__main__":
    main()
