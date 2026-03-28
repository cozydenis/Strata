#!/usr/bin/env bash
# setup.sh — Download Swiss GTFS and OSM data for OpenTripPlanner
# Usage: ./setup.sh
# Data is written to ./otp-data/

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_DIR="${SCRIPT_DIR}/otp-data"

mkdir -p "${DATA_DIR}"

echo "[otp-setup] Downloading Swiss GTFS feed (SBB 2026)..."
# Official Swiss public transport GTFS 2026 from opentransportdata.swiss
curl -fSL \
  "https://opentransportdata.swiss/wp-content/uploads/2026/01/gtfs_fp2026_20260126_mit-frequencies_v2.zip" \
  -o "${DATA_DIR}/swiss-gtfs.zip"

# Validate it's a real ZIP (not an HTML error page)
if ! unzip -t "${DATA_DIR}/swiss-gtfs.zip" > /dev/null 2>&1; then
  echo "[otp-setup] ERROR: swiss-gtfs.zip is not a valid ZIP file."
  echo "[otp-setup] The download URL may have changed. Check:"
  echo "[otp-setup]   https://data.opentransportdata.swiss/dataset/timetable-2026-gtfs2020"
  rm -f "${DATA_DIR}/swiss-gtfs.zip"
  exit 1
fi
echo "[otp-setup] GTFS ZIP validated OK."

echo "[otp-setup] Downloading Switzerland OSM extract..."
# Downloaded to script dir (NOT otp-data) — will be cropped to Zürich bbox below
curl -fSL \
  "https://download.geofabrik.de/europe/switzerland-latest.osm.pbf" \
  -o "${SCRIPT_DIR}/switzerland.osm.pbf"

echo "[otp-setup] Cropping OSM to Zürich bbox (17 MB vs 503 MB)..."
# Zürich bbox: lon 8.43–8.63, lat 47.32–47.43
# Uses osmium via Docker — no host install needed
docker run --rm \
  -v "${SCRIPT_DIR}:/data" \
  stefda/osmium-tool \
  osmium extract \
  --bbox 8.43,47.32,8.63,47.43 \
  /data/switzerland.osm.pbf \
  -o /data/otp-data/zurich.osm.pbf \
  --overwrite
echo "[otp-setup] OSM crop done: $(du -sh "${DATA_DIR}/zurich.osm.pbf" | cut -f1)"

echo "[otp-setup] Copying OTP config files to data directory..."
cp "${SCRIPT_DIR}/otp-config.json" "${DATA_DIR}/otp-config.json"

echo "[otp-setup] Done. Data directory contents:"
ls -lh "${DATA_DIR}"
echo ""
echo "[otp-setup] Start OTP with: docker compose up"
