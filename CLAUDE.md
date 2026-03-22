# Strata

## What This Is
Strata is a spatial intelligence platform for the Zurich housing market.
It models every residential unit in the city as a persistent object in a
living registry — whether available or not. Users explore neighborhoods,
watch specific units, and apply through a verified profile system.

## Current Phase
Phase 0 — Foundation. Building the GWR data pipeline and proof-of-concept map.

## Tech Stack
- **Frontend**: Next.js 15 (App Router) + MapLibre GL JS + Tailwind CSS — in `apps/web/`
- **Backend**: Python 3.12 + FastAPI + SQLAlchemy — in `apps/api/`
- **Database**: PostgreSQL (Supabase)
- **Shared types/contracts**: `packages/shared/`
- **Deployment**: Vercel (frontend), Railway or Supabase (backend)
- **CI**: GitHub Actions

## Key Commands
- `cd apps/web && npm run dev` — frontend dev server
- `cd apps/api && uvicorn main:app --reload` — backend dev server
- `cd apps/api && pytest` — run backend tests
- `cd apps/web && npm test` — run frontend tests

## Data Model — Unit Registry
Every unit is a persistent object identified by EGID (building) + EWID (dwelling)
from the GWR. Key fields: building_id, unit_id, floor, room_count, area_m2,
construction_year, building_type, coordinates, verwaltung (when known).

## Swiss-Specific Terminology
- **GWR** (Gebaude- und Wohnungsregister): Federal building/dwelling register
- **EGID**: Eidgenossischer Gebaudeidentifikator (building ID)
- **EWID**: Eidgenossischer Wohnungsidentifikator (dwelling ID)
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
- Unit Registry is the single source of truth — listings, predictions, and profiles reference it
- Privacy by design: tenant data never exposed without explicit consent

## Conventions
- Python: snake_case, type hints on all functions, ruff for linting
- TypeScript: strict mode, no `any`, Prettier for formatting
- Commits: conventional commits (feat:, fix:, chore:)
- Never hardcode API keys — use environment variables
- No console.log in production code
