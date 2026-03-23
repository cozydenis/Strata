# Strata

## What This Is
Strata is a spatial intelligence platform for the Zurich housing market.
It models every residential unit in the city as a persistent object in a
living registry — whether available or not. Users explore neighborhoods,
watch specific units, and apply through a verified profile system.

## Current Phase
Phase 0 — Foundation (Apr–May 2026). Nearing completion, with Phase 2 listing
ingestion pulled forward.

**Done:**
- Monorepo scaffold (Next.js 15 + FastAPI + shared types)
- CI/CD (GitHub Actions: lint + test on every PR)
- GWR pipeline: Stadt Zurich (GeoJSON) + Kanton Zurich (CSV) parsers
- Pipeline runner with dedup (Stadt takes priority over Kanton by EGID)
- DB models: Building, Unit, Entrance, PipelineRun with Alembic migrations
- Registry API: CRUD endpoints for buildings/units with pagination
- Admin pipeline API: trigger pipeline runs via POST
- GeoJSON export script for map consumption
- Proof-of-concept map: MapLibre with era-colored buildings, clustering, click popups
- BuildingPopup, Legend, ListingCards components
- **Listing ingestion pipeline** (pulled forward from Phase 2):
  - Flatfox connector (public API, async pagination, Zurich PLZ filter)
  - Homegate connector (HTML scraper, __INITIAL_STATE__ parser)
  - Listing DB models: Listing, ListingUnitMatch, ListingHistory, ListingImage, ListingDocument
  - Address matcher: exact → fuzzy (0.85 threshold) → geo fallback (50m) → unit narrowing
  - Listing loader with upsert + deactivation of disappeared listings
  - Media downloader (Flatfox image scraping + local storage)
  - Listings API: GET /registry/buildings/{egid}/listings
  - Listings GeoJSON export
  - ListingCards frontend component with image gallery, description, floor plans
- Test coverage across all modules (pipeline, parsers, connectors, loaders, matchers, routers)

**Remaining Phase 0:**
- Connect to real PostgreSQL (Supabase) — currently using SQLite for dev
- Run pipeline against live GWR data and validate output
- Deploy: Vercel (frontend), Railway/Supabase (backend)
- Run listing pipeline against live Flatfox API

**Next: Phase 1 (Jun–Aug 2026)** — Core product: full Explore Mode, neighborhood
intelligence layers (noise, sunlight, demographics, commute), comparison mode.

## Tech Stack
- **Frontend**: Next.js 15 (App Router) + MapLibre GL JS + Tailwind CSS — `apps/web/`
- **Backend**: Python 3.12 + FastAPI + SQLAlchemy 2.0 — `apps/api/`
- **Database**: PostgreSQL (Supabase) — Alembic for migrations
- **Shared types/contracts**: `packages/shared/`
- **Package manager**: npm workspaces (frontend), uv (backend)
- **Testing**: Vitest (frontend), pytest + httpx (backend)
- **Linting**: ESLint + Prettier (frontend), ruff (backend)
- **Deployment**: Vercel (frontend), Railway or Supabase (backend)
- **CI**: GitHub Actions — `.github/workflows/ci.yml`

## Key Commands
```bash
# Frontend
cd apps/web && npm run dev          # http://localhost:3000
cd apps/web && npm test             # Vitest

# Backend
cd apps/api && uv run uvicorn strata_api.main:app --reload  # http://localhost:8000
cd apps/api && uv run pytest        # pytest
cd apps/api && uv run ruff check .  # lint

# Pipeline
cd apps/api && uv run python -m strata_api.pipeline  # run GWR pipeline

# Full install
npm install                         # root + workspaces
cd apps/api && uv venv && uv pip install -e ".[dev]"
```

## Data Model

### gwr_buildings
`egid` (PK), `gstat`, `gkat` (category), `gklas` (class), `gbauj` (construction year),
`gabbj` (demolition year), `garea` (footprint m2), `gastw` (floors), `ganzwhg` (unit count),
`lat`, `lon` (WGS84), `municipality`, `municipality_code`, `canton`, `data_source`

### gwr_units
`egid` + `ewid` (composite PK), `edid` (entrance ref), `wstwk` (floor code),
`wstwklang` (floor label), `wazim` (rooms), `warea` (area m2), `wkche` (kitchen),
`wstat` (status), `wbauj`, `wabbj`, address fields (`dplz4`, `dplzname`, `strname`, `deinr`),
`lat`, `lon`, `data_source`

### gwr_entrances
`egid` + `edid` (composite PK), address fields, `lat`, `lon`, `data_source`

### listings
`id` (PK), `source` + `source_id` (unique), pricing (`rent_net`, `rent_gross`, `rent_charges`),
`rooms`, `area_m2`, address fields (raw + normalized), `lat`/`lng`, `object_type`, `offer_type`,
`status`, `source_url`, `description`, `first_seen`, `last_seen`, `is_active`

### listing_unit_matches
Links listings to GWR units: `listing_id` → `egid`/`ewid` with `match_confidence`
(exact | probable | building_only)

### listing_images / listing_documents
Media associated with listings: URLs, local paths, captions, ordering, type classification

### listing_history
Tracks field changes over time (price changes, status changes)

### pipeline_runs
`id` (PK), `run_type` (stadt/kanton), `status`, timestamps, counts, `error_message`

## Pipeline Architecture

### GWR Pipeline
Two-source with Stadt-priority dedup:
1. **Stadt Zurich** — GeoJSON from Stadt open data portal (higher quality)
2. **Kanton Zurich** — CSV from housing-stat.ch (broader agglomeration coverage)
Flow: download → parse → (kanton: dedup against Stadt EGIDs) → upsert

### Listing Pipeline
Connector-based architecture:
1. **Flatfox** — public REST API, async pagination, Kanton ZH PLZ filter, residential-only
2. **Homegate** — HTML scraper extracting `window.__INITIAL_STATE__` JSON
Flow: fetch → parse → upsert (with change detection) → deactivate missing → address match

### Address Matcher
Links listings to GWR entries via 3-tier matching:
1. **Exact**: normalized street + house number + PLZ → entrance lookup
2. **Probable**: fuzzy street similarity (SequenceMatcher >= 0.85) within same PLZ
3. **Building-only**: nearest entrance within 50m geo radius (haversine)
4. **Unit narrowing**: within matched EGID, filter by rooms (±0.5) and area (±10%)

Street normalization handles Swiss abbreviations (Str.→strasse, Pl.→platz) and
umlaut→digraph mapping (ae, oe, ue).

## API Endpoints
- `GET /health` — health check
- `GET /registry/buildings` — paginated building list (filter by data_source)
- `GET /registry/buildings/{egid}` — single building
- `GET /registry/buildings/{egid}/summary` — building + address (for map popups)
- `GET /registry/buildings/{egid}/units` — units in a building
- `GET /registry/buildings/{egid}/units/{ewid}` — single unit
- `GET /registry/buildings/{egid}/listings` — active listings matched to building
- `POST /admin/pipeline/run` — trigger pipeline run

## Swiss-Specific Terminology
- **GWR** (Gebaude- und Wohnungsregister): Federal building/dwelling register
- **EGID**: Eidgenossischer Gebaudeidentifikator (building ID)
- **EWID**: Eidgenossischer Wohnungsidentifikator (dwelling ID)
- **EDID**: Eidgenossischer Eingangsidentifikator (entrance ID)
- **Verwaltung**: Property management company
- **Nebenkosten**: Ancillary costs (utilities, maintenance)
- **Referenzzinssatz**: Reference interest rate governing legal rent adjustments
- **Herabsetzungsbegehren**: Formal rent reduction request
- **Schlichtungsbehorde**: Free tenancy mediation authority
- **Baugesuch/Baubewilligung**: Building permit application/approval
- **Genossenschaft**: Housing cooperative
- **Quartier**: City district/neighborhood

## Architecture Principles
- Data pipelines in Python, API in FastAPI, frontend in Next.js
- Every feature test-covered via /tdd before implementation
- Map layers are toggleable MapLibre layers, each backed by a GeoJSON API endpoint
- Unit Registry is the single source of truth — listings reference it via address matching
- Privacy by design: tenant data never exposed without explicit consent
- Stadt data takes priority over Kanton data (dedup by EGID)
- Listing connectors are pluggable — each source implements parse + fetch

## Conventions
- Python: snake_case, type hints on all functions, ruff for linting
- TypeScript: strict mode, no `any`, Prettier for formatting
- Commits: conventional commits (feat:, fix:, chore:)
- Never hardcode API keys — use environment variables
- No console.log in production code
