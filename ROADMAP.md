# STRATA — Roadmap

> Last updated: June 2026
> Status: Layer 1 complete, Layer 2 in progress — deployment DOWN (Supabase paused, Railway credits out), see Next Actions

---

## How This Works

- **This file** = high-level overview of every layer, feature, and milestone
- **GitHub Issues** = detailed specs for each item (linked below)
- **Labels**: `layer:sensory`, `layer:social`, `layer:practical`, `layer:trajectory`, `feature:core`, `feature:marketplace`, `infra`, `data-source`
- **Status**: 🟢 Done | 🟡 In Progress | ⚪ Planned | 💡 Idea

Update this file when phases shift. Claude Code reads it every session via CLAUDE.md reference.

---

## Current Stats

| Metric | Value |
|--------|-------|
| Buildings in registry | 399,029 |
| Units (dwellings) | 890,603 |
| Active listings (Flatfox) | 4,209 |
| Listing match rate | 93% |
| Photos stored | 565+ |
| Quartiere with profiles | 34 |
| Noise data points | 1,071,340 |
| Backend tests | 727 |
| Frontend tests | 344 |

---

## The Seven Layers (from Vision Doc)

### Foundation: Unit Registry 🟢
The core data asset. Every residential unit in Kanton Zürich.

| Component | Status | Issue |
|-----------|--------|-------|
| GWR pipeline (Stadt Zürich daily) | 🟢 Done | — |
| GWR pipeline (Kanton Zürich quarterly) | 🟢 Done | — |
| Building/entrance/unit data model | 🟢 Done | — |
| Daily refresh mechanism | 🟢 Done | — |
| Baugesuch/Baubewilligung enrichment | ⚪ Planned | #TBD |

---

### Layer 1: Neighborhood Intelligence 🟡

The layer that answers "where should I live?" Four dimensions.

#### Sensory Dimension

| Component | Status | Data Source | Issue |
|-----------|--------|-------------|-------|
| **Noise map** | 🟢 Done | Stadt Zürich Strassenlärmkataster | — |
| **Sunlight / shadow** | 💡 Idea | Stadt Zürich 3D-Stadtmodell (shadow simulation) | #TBD |
| **Air quality** | 🟢 Done — UGZ hourly pipeline (LRV levels) + toggleable station layer with per-parameter popup | #4 |
| **Green space** | 🟡 Pipeline done — 6,912 OSM green polygons, per-quartier share/per-capita metrics; map layer + profile UI pending | #7 |

#### Social & Cultural Dimension

| Component | Status | Data Source | Issue |
|-----------|--------|-------------|-------|
| **Demographics** (age, origin, gender) | 🟢 Done | Statistik Stadt Zürich CSV | — |
| **Population density** | 🟢 Done | Derived from demographics + Quartier area | — |
| **Venue typology** (cafés, nightlife, culture) | ⚪ Planned | OSM Overpass API or Google Places | #TBD |
| **Vibe / character profiles** | 🟢 Done — quartile-based explainable tags + summary | — |

#### Practical Dimension

| Component | Status | Data Source | Issue |
|-----------|--------|-------------|-------|
| **Commute isochrones** | 🟢 Done | Travel time pipeline + map visualization (PR #22) | — |
| **Amenities & walkability** | 🟢 Done | OSM Overpass — 7 categories per Quartier + density | — |
| **Parking** | 💡 Idea | Stadt Zürich Parkleitsystem | #TBD |
| **School proximity + quality** | 💡 Idea | Volksschulamt data | #TBD |

#### Trajectory Dimension

| Component | Status | Data Source | Issue |
|-----------|--------|-------------|-------|
| **Population growth/decline** | 🟢 Done | YoY from demographics CSV (back to 1993) | — |
| **Construction activity** | 🟢 Done | GWR construction year distribution per Quartier | — |
| **Rent trends per Quartier** | 🟡 Partial | From listing data (need historical depth) | #TBD |
| **Commercial activity** (new venues opening) | 💡 Idea | Handelsregister or OSM changeset history | #TBD |
| **Construction pipeline** (approved + under construction per Quartier) | 🟢 Done — OGD BAU501OD5011, profile + comparison + vibe | — |

#### Neighborhood Features

| Component | Status | Issue |
|-----------|--------|-------|
| Quartier boundary polygons | 🟢 Done | — |
| Choropleth with metric selector | 🟢 Done | — |
| Quartier profile panel (slide-out) | 🟢 Done | — |
| Layer toggle panel | 🟢 Done | — |
| **Comparison mode** (two Quartiere side by side) | 🟢 Done — compare from profile panel, swap by map click | — |
| **Personalized match scoring** ("your match: 87%") | 🟢 Done — stateless client-side v1: 6 explainable dimensions, localStorage prefs, match choropleth + profile breakdown | #9 |

---

### Layer 2: Tenant & Demand Side ⚪

| Component | Status | Issue |
|-----------|--------|-------|
| Authentication (Supabase Auth, JWT-verified API) | 🟢 Done — needs live Supabase project creds | — |
| Watchlist API (watch building or specific unit) | 🟢 Done | — |
| Watch buttons (building + per-unit) in popup | 🟢 Done | — |
| Watchlist panel | 🟢 Done | — |
| Unit list in building popup (registry surfaced) | 🟢 Done | — |
| Profile vault (personal info, documents) | ⚪ Planned | #TBD |
| Wishlist — broad search alerts | ⚪ Planned | #TBD |
| Wishlist — building typology matching | ⚪ Planned | #TBD |
| Watch Mode feed (new/gone listings, price changes in watched buildings) | 🟢 Done — v1 in watchlist panel | — |
| Notification system (email-first) | 🟢 Done — watch-event digests, ConsoleSender dry-run default / SMTP via env, `POST /admin/pipeline/run-notifications` | — |

---

### Layer 3: Privacy & Trust ⚪

| Component | Status | Issue |
|-----------|--------|-------|
| Credential presentation (not document handoff) | ⚪ Planned | #TBD |
| Anonymized demand aggregation | ⚪ Planned | #TBD |
| Betreibungsauszug verification | 💡 Idea | #TBD |
| Income verification (Open Banking / bLink) | 💡 Idea | #TBD |
| Identity KYC (SwissID / IDnow) | 💡 Idea | #TBD |
| Structured references (Y/N questions) | 💡 Idea | #TBD |

---

### Layer 4: Availability & Prediction ⚪

| Component | Status | Issue |
|-----------|--------|-------|
| Structural turnover base rates | ⚪ Planned (needs listing history) | #TBD |
| Referenzzinssatz change triggers | ⚪ Planned | #TBD |
| New construction pull (from Baugesuch) | ⚪ Planned | #TBD |
| Nachmieter pipeline | 💡 Idea | #TBD |
| Availability heat indicator (low/moderate/high) | ⚪ Planned | #TBD |

---

### Layer 5: Marketplace ⚪

| Component | Status | Issue |
|-----------|--------|-------|
| Application engine (one-tap apply) | ⚪ Planned | #TBD |
| Verwaltung dashboard (MVP) | ⚪ Planned | #TBD |
| Act Mode UI | ⚪ Planned | #TBD |
| Application tracking (submitted → viewed → result) | ⚪ Planned | #TBD |
| Tenant-side freemium + Pro tier | ⚪ Planned | #TBD |
| Verwaltung SaaS pricing | ⚪ Planned | #TBD |

---

### Layer 6: Financial Modeling ⚪

| Component | Status | Issue |
|-----------|--------|-------|
| True cost of living per unit | ⚪ Planned | #TBD |
| Nebenkosten estimation | ⚪ Planned (needs tenant contributions) | #TBD |
| Gemeinde tax impact calculator | ⚪ Planned | #TBD |
| Commute cost integration | ⚪ Planned | #TBD |
| Rent trajectory forecasting (Referenzzinssatz) | ⚪ Planned | #TBD |
| Rent vs buy calculator (Swiss-specific) | 💡 Idea | #TBD |
| Budget optimization view | 💡 Idea | #TBD |

---

### Layer 7: Legal Intelligence 🟡

| Component | Status | Issue |
|-----------|--------|-------|
| Referenzzinssatz auto-tracking | 🟢 Done — history table + `/legal/reference-rate`, per-listing analysis (OR 269a step table), badge in listing cards | #17 |
| Pre-drafted Herabsetzungsbegehren | 🟢 Done — API + one-tap letter dialog (copy/download) in listing cards | #17 |
| Initial rent challenge analysis (OR Art. 270) | 🟢 Backend done — Quartierüblichkeit comparables, `GET /legal/listings/{id}/initial-rent-check` | — |
| Rent increase verification | ⚪ Planned | #TBD |
| Mängelrüge templates | 💡 Idea | #TBD |
| Kündigungstermin reminders | 💡 Idea | #TBD |
| Schlichtungsbehörde navigator | 💡 Idea | #TBD |
| Regulatory feed (legal changes in plain language) | 💡 Idea | #TBD |

---

## Listing Ingestion

| Component | Status | Issue |
|-----------|--------|-------|
| Flatfox connector (API) | 🟢 Done | — |
| Flatfox full pagination (4,209 listings) | 🟢 Done | — |
| Flatfox photo download | 🟢 Done | — |
| Flatfox floor plan download | 🟢 Done | — |
| Address matching engine (93% match) | 🟢 Done | — |
| Cross-source deduplication | 🟢 Done (untested — only one source active) | — |
| Listing history / change tracking | 🟢 Done (schema ready, populates on re-runs) | — |
| Listing media → Supabase Storage (permanent archival) | 🟢 Done | — |
| Homegate connector (scraping) | 🟡 Built but blocked by DataDome | #TBD |
| Immoscout24 connector | ⚪ Planned | #TBD |
| WG-Zimmer connector | 💡 Idea | #TBD |
| PLZ filter fix (exclude Thurgau/SG) | 🟢 Done — shared border PLZs (8212/8500) disambiguated by city | — |

---

## UX & Interface

| Component | Status | Issue |
|-----------|--------|-------|
| Full-screen MapLibre map | 🟢 Done | — |
| Building era coloring + clustering | 🟢 Done | — |
| Listing layer (red dots) | 🟢 Done | — |
| Building popup (info + listings + photos) | 🟢 Done | — |
| Legend / layer toggle panel | 🟢 Done | — |
| Quartier choropleth | 🟢 Done | — |
| Noise overlay | 🟢 Done | — |
| Quartier profile panel | 🟢 Done | — |
| Design system (palette, typography) | 🟢 Done — glass panels, Inter + IBM Plex Mono, functional color | — |
| Dark/muted map style | 🟡 Implemented | — |
| Comparison mode | 🟢 Done | — |
| 3D city model (Stadt Zürich) | 💡 Idea — bookmarked for later | #TBD |
| Explore / Watch / Act modes | ⚪ Planned | #TBD |
| Onboarding flow | ⚪ Planned | #TBD |
| Mobile responsive | ⚪ Planned (Phase 5) | #TBD |

---

## Infrastructure

| Component | Status | Issue |
|-----------|--------|-------|
| Monorepo (Next.js + FastAPI) | 🟢 Done | — |
| SQLite local DB | 🟢 Done | — |
| Alembic migrations | 🟢 Done | — |
| everything-claude-code harness | 🟢 Done | — |
| CI/CD (GitHub Actions — lint + test on PR) | 🟢 Done | — |
| Deploy frontend (Vercel) | 🟢 Done | — |
| Deploy backend (Railway) | 🟢 Done | — |
| PostgreSQL (Supabase, prod) | 🟢 Done | — |
| Pipeline trigger endpoints (`/admin/pipeline/run`, `/run-listings`) | 🟢 Done | — |
| Daily pipeline scheduler (GitHub Actions cron) | 🟢 Done — daily Stadt+listings, quarterly Kanton | — |

---

## Data Sources Index

All currently used or identified open data sources for Strata.

| Source | Type | Scope | Refresh | Status |
|--------|------|-------|---------|--------|
| Stadt Zürich GWR (GWZ) | WFS GeoJSON | City | Daily | 🟢 Ingested |
| Kanton Zürich GWR | CSV | Canton | Quarterly | 🟢 Ingested |
| Flatfox API | JSON API | National | On demand | 🟢 Ingested |
| Homegate | HTML scraping | National | On demand | 🟡 Blocked by DataDome |
| Strassenlärmkataster | WFS GeoJSON | City | Periodic | 🟢 Ingested |
| Statistik Stadt Zürich demographics | CSV | City | Annual | 🟢 Ingested |
| Statistische Quartiere boundaries | WFS GeoJSON | City | Stable | 🟢 Ingested |
| Stadt Zürich 3D-Stadtmodell | CityGML/OBJ | City | Periodic | 💡 Bookmarked |
| UGZ Luftqualität (air quality) | CSV/JSON OGD | City | Hourly | 🟢 Ingested |
| ZVV/SBB timetable | GTFS / API | Canton | Periodic | ⚪ Identified |
| OSM Overpass (amenities + green) | API | Global | On demand | 🟢 Ingested |
| Baugesuche Stadt Zürich | Open Data | City | Periodic | ⚪ Identified |
| BAFU sonBASE (national noise) | WMS | National | Periodic | ⚪ Identified |
| Referenzzinssatz (SNB) | Web page | National | Quarterly | ⚪ Identified |
| Gemeinde tax rates | Published tables | Canton | Annual | ⚪ Identified |

---

## Timeline (Original → Actual)

| Phase | Original Timeline | Actual Status |
|-------|-------------------|---------------|
| Phase 0: Foundation | Apr–May 2026 | 🟢 Complete (done in 1 day) |
| Phase 1: Core Product | Jun–Aug 2026 | 🟡 In progress (map + layers + commute + deploy done, missing amenities/comparison) |
| Phase 2: Demand Side | Sep–Dec 2026 | 🟡 Partially started (listing ingestion done, auth/profiles/watchlists not started) |
| Phase 3: Marketplace | Jan–Mar 2027 | ⚪ Not started |
| Phase 4: Intelligence | Apr–Jun 2027 | ⚪ Not started |
| Phase 5: Scale | Jul–Sep 2027 | ⚪ Not started |

---

## Next Actions

_Update this section at the start of each work session._

1. **Restore deployment + Supabase project** — unblocks live auth (set SUPABASE_JWT_SECRET +
   NEXT_PUBLIC_SUPABASE_* and run `alembic upgrade head` for the watches table)
2. **Per-building Baugesuche** — cantonal Amtsblatt API (quartier-level done via OGD)
3. **Wire email notifications into the daily cron** once deployment is restored (SMTP env + trigger after pipeline runs)