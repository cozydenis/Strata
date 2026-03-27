# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

Strata is a spatial intelligence platform for the Zurich housing market. It models every residential unit as a persistent object in a living registry (from the GWR federal register), enriched with listing data scraped from Flatfox/Homegate, neighborhood intelligence, and map visualization. Not a listing platform — housing infrastructure.

**Current Phase:** Phase 0 — Foundation (Apr–May 2026). GWR pipeline, listing ingestion, and proof-of-concept map are built. Remaining: connect to real PostgreSQL (Supabase), deploy, validate against live data.

## Tech Stack

| Layer | Stack | Location |
|-------|-------|----------|
| Frontend | Next.js 15 (App Router) + MapLibre GL JS + Tailwind CSS | `apps/web/` |
| Backend | Python 3.12 + FastAPI + SQLAlchemy 2.0 | `apps/api/` |
| Database | SQLite (dev) → PostgreSQL/Supabase (prod), Alembic migrations | `apps/api/alembic/` |
| Shared types | TypeScript package consumed by web | `packages/shared/` |
| Package mgmt | npm workspaces (frontend), uv (backend) | |
| CI | GitHub Actions — lint + test on PR | `.github/workflows/ci.yml` |

## Commands

### Frontend (apps/web)
```bash
cd apps/web && npm run dev            # dev server on :3000
cd apps/web && npm test               # vitest run (all tests)
cd apps/web && npx vitest run src/components/map/Map.test.tsx  # single test file
cd apps/web && npx vitest run --coverage  # with coverage
cd apps/web && npm run lint           # eslint
```

### Backend (apps/api)
```bash
cd apps/api && uv run uvicorn strata_api.main:app --reload  # dev server on :8000
cd apps/api && uv run pytest                    # all tests
cd apps/api && uv run pytest tests/pipeline/test_dedup.py   # single test file
cd apps/api && uv run pytest -k test_parse_buildings        # single test by name
cd apps/api && uv run pytest --cov=strata_api               # with coverage
cd apps/api && uv run ruff check .              # lint
cd apps/api && uv run ruff format .             # auto-format
```

### Pipelines
```bash
cd apps/api && uv run python -m strata_api.pipeline         # GWR pipeline (download + parse + load)
cd apps/api && uv run python -m strata_api.pipeline.listing_runner  # listing pipeline
```

### Database migrations (Alembic)
```bash
cd apps/api && uv run alembic upgrade head      # apply all migrations
cd apps/api && uv run alembic revision --autogenerate -m "description"  # new migration
cd apps/api && uv run alembic downgrade -1      # rollback one
```

### Full install
```bash
npm install                                     # root + workspaces
cd apps/api && uv venv && uv pip install -e ".[dev]"
```

### GeoJSON export (for map consumption)
```bash
cd apps/api && DATABASE_URL=... uv run python -m strata_api.scripts.export_buildings_geojson > ../web/public/data/buildings.geojson
cd apps/api && DATABASE_URL=... uv run python -m strata_api.scripts.export_listings_geojson > ../web/public/data/listings.geojson
```

## Architecture

### Monorepo layout
```
apps/
  web/              Next.js frontend — map is the primary interface
    src/
      components/map/   Map.tsx (MapLibre), BuildingPopup, Legend, ListingCards, LayerPanel, QuartierProfile
      lib/              api.ts (fetch wrappers), map/ (era-colors, noise-colors, quartier-colors)
      app/              page.tsx (single-page map app), layout.tsx
  api/              Python backend
    src/strata_api/
      main.py           FastAPI app entry point, mounts routers + static media
      config.py         pydantic-settings (DATABASE_URL, CORS_ORIGINS, PIPELINE_API_KEY)
      db/               SQLAlchemy models (building, unit, entrance, listing, pipeline_run), session factory, Base
      routers/          registry, listings, neighborhoods, admin_pipeline
      pipeline/
        runner.py           GWR pipeline orchestrator (stadt + kanton sources)
        listing_runner.py   Listing pipeline orchestrator
        parsers/            stadt_parser (GeoJSON), kanton_parser (CSV)
        connectors/         flatfox (REST API), homegate (HTML scraper), recon
        address_matcher.py  3-tier matching: exact → fuzzy → geo fallback
        listing_loader.py   Upsert with change detection + deactivation
        loader.py           GWR upsert (buildings, entrances, units)
        dedup.py            Kanton dedup against Stadt EGIDs
        neighborhoods/      Quartier data: noise, demographics, aggregator
      scripts/          GeoJSON export scripts
    alembic/            DB migrations (3 versions: initial, listings, listing media)
    tests/              Mirrors src structure — pipeline/, routers/, db/, fixtures/
    data/               Downloaded media (images, neighborhoods, recon)
packages/
  shared/           TypeScript types (Unit interface) shared between web and API contracts
```

### Key data flow
1. **GWR Pipeline**: Stadt Zurich (GeoJSON, higher quality) + Kanton Zurich (CSV, broader coverage) → parse → Kanton dedup by EGID → upsert to DB
2. **Listing Pipeline**: Flatfox API / Homegate scraper → parse → upsert with change tracking → deactivate disappeared → address match to GWR entries
3. **Address Matcher**: normalized street+PLZ exact match → fuzzy (SequenceMatcher ≥0.85) → geo fallback (50m haversine) → unit narrowing (rooms ±0.5, area ±10%)
4. **Frontend**: MapLibre loads GeoJSON, displays era-colored buildings with clustering. Click → popup with building summary + listings via API calls.

### Database
- `gwr_buildings` (PK: egid), `gwr_units` (PK: egid+ewid), `gwr_entrances` (PK: egid+edid)
- `listings` (PK: id, unique: source+source_id), `listing_unit_matches`, `listing_images`, `listing_documents`, `listing_history`
- `pipeline_runs` tracks each pipeline execution with status and counts
- Currently SQLite for dev (`apps/api/local.db`), migrating to Supabase PostgreSQL

### API endpoints
- `GET /health`
- `GET /registry/buildings[/{egid}[/summary|/units[/{ewid}]|/listings]]`
- `GET /neighborhoods/{quartier_id}/profile`
- `POST /admin/pipeline/run`

### Testing
- Backend: pytest + httpx `AsyncClient` with `ASGITransport` against the FastAPI app. Fixtures in `tests/fixtures/`.
- Frontend: Vitest + Testing Library + jsdom. Setup in `src/test/setup.ts`.
- Tests mirror source structure in both apps.

## Swiss-Specific Terminology

- **GWR** (Gebäude- und Wohnungsregister): Federal building/dwelling register
- **EGID**: Building identifier, **EWID**: Dwelling identifier, **EDID**: Entrance identifier
- **Verwaltung**: Property management company
- **Nebenkosten**: Ancillary costs (utilities, maintenance)
- **Genossenschaft**: Housing cooperative
- **Quartier**: City district/neighborhood
- **Referenzzinssatz**: Reference interest rate governing legal rent adjustments
- **Herabsetzungsbegehren**: Formal rent reduction request
- **Schlichtungsbehörde**: Free tenancy mediation authority

## Conventions

- Python: snake_case, type hints on all functions, ruff for lint+format (line-length=130)
- TypeScript: strict mode, no `any`, Prettier for formatting
- Commits: conventional commits (feat:, fix:, chore:, refactor:, test:, docs:)
- Stadt data takes priority over Kanton data (dedup by EGID)
- Listing connectors are pluggable — each source implements fetch + parse
- Map layers are toggleable MapLibre layers, each backed by a GeoJSON source
- Unit Registry is the single source of truth — listings reference it via address matching
- Frontend env: `NEXT_PUBLIC_API_URL` points to the backend base URL
- Backend env: `DATABASE_URL`, `CORS_ORIGINS`, `PIPELINE_API_KEY`
