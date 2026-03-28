# OTP Local Setup

OpenTripPlanner 2.x for commute isochrone generation.

## Prerequisites

- Docker + Docker Compose
- ~15 GB free disk space (OSM + GTFS data + OTP graph)
- ~10 GB RAM available for Docker

## Quick Start

```bash
# 1. Download data (Swiss OSM + GTFS, ~2 GB download)
./setup.sh

# 2. Start OTP (first run builds graph — takes 20-40 min)
docker compose up

# 3. Wait until healthy (check logs for "Listening for connections")
docker compose logs -f otp

# 4. Verify it works
curl http://localhost:8080/otp/routers/default
```

## Endpoints Used by Strata

| Endpoint | Purpose |
|----------|---------|
| `GET /otp/isochrone` | Isochrone polygons (LegacyRestApi) |
| `GET /otp/routers/default/plan` | Point-to-point travel time |

## Generate Isochrones

```bash
cd apps/api
uv run python -m strata_api.pipeline.commute.generator \
  --otp-url http://localhost:8080 \
  --output-dir apps/web/public/data/commutes/
```

## Notes

- OTP graph is stored in `otp-data/` (gitignored)
- Rebuild graph after updating GTFS/OSM: `docker compose down && docker compose up`
- `LegacyRestApi` must be enabled in `otp-config.json` for `/otp/isochrone` endpoint support
- First `docker compose up` builds the graph (20-40 min) then starts serving — subsequent starts load the saved `graph.obj` faster
