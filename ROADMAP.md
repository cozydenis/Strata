# STRATA — Roadmap

> Last updated: March 2026
> Status: Phase 0 complete, Phase 1 in progress

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
| Backend tests | 283+ |
| Frontend tests | 31+ |

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
| **Air quality** | ⚪ Planned | Stadt Zürich UGZ live sensors (NO₂, O₃, PM10, PM2.5) | #TBD |
| **Green space** | 💡 Idea | OSM parks + Stadt Zürich Grünflächenkataster | #TBD |

#### Social & Cultural Dimension

| Component | Status | Data Source | Issue |
|-----------|--------|-------------|-------|
| **Demographics** (age, origin, gender) | 🟢 Done | Statistik Stadt Zürich CSV | — |
| **Population density** | 🟢 Done | Derived from demographics + Quartier area | — |
| **Venue typology** (cafés, nightlife, culture) | ⚪ Planned | OSM Overpass API or Google Places | #TBD |
| **Vibe / character profiles** | 💡 Idea | Derived from venue mix + demographics + rent level | #TBD |

#### Practical Dimension

| Component | Status | Data Source | Issue |
|-----------|--------|-------------|-------|
| **Commute isochrones** | ⚪ Planned | ZVV/SBB API or OpenTripPlanner | #TBD |
| **Amenities & walkability** | ⚪ Planned | OSM (groceries, pharmacies, schools, gyms) | #TBD |
| **Parking** | 💡 Idea | Stadt Zürich Parkleitsystem | #TBD |
| **School proximity + quality** | 💡 Idea | Volksschulamt data | #TBD |

#### Trajectory Dimension

| Component | Status | Data Source | Issue |
|-----------|--------|-------------|-------|
| **Population growth/decline** | 🟢 Done | YoY from demographics CSV (back to 1993) | — |
| **Construction activity** | 🟢 Done | GWR construction year distribution per Quartier | — |
| **Rent trends per Quartier** | 🟡 Partial | From listing data (need historical depth) | #TBD |
| **Commercial activity** (new venues opening) | 💡 Idea | Handelsregister or OSM changeset history | #TBD |
| **Baugesuch pipeline** (upcoming construction) | ⚪ Planned | Stadt Zürich Open Data | #TBD |

#### Neighborhood Features

| Component | Status | Issue |
|-----------|--------|-------|
| Quartier boundary polygons | 🟢 Done | — |
| Choropleth with metric selector | 🟢 Done | — |
| Quartier profile panel (slide-out) | 🟢 Done | — |
| Layer toggle panel | 🟢 Done | — |
| **Comparison mode** (two Quartiere side by side) | ⚪ Planned | #TBD |
| **Personalized match scoring** ("your match: 87%") | 💡 Idea (needs user profiles) | #TBD |

---

### Layer 2: Tenant & Demand Side ⚪

| Component | Status | Issue |
|-----------|--------|-------|
| Authentication (Supabase Auth or Clerk) | ⚪ Planned | #TBD |
| Profile vault (personal info, documents) | ⚪ Planned | #TBD |
| Wishlist — broad search alerts | ⚪ Planned | #TBD |
| Wishlist — building typology matching | ⚪ Planned | #TBD |
| Wishlist — specific unit pin ("I want this unit") | ⚪ Planned | #TBD |
| Watch Mode UI (personal feed of events) | ⚪ Planned | #TBD |
| Notification system (email-first) | ⚪ Planned | #TBD |

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

### Layer 7: Legal Intelligence ⚪

| Component | Status | Issue |
|-----------|--------|-------|
| Referenzzinssatz auto-tracking | ⚪ Planned | #TBD |
| Pre-drafted Herabsetzungsbegehren | ⚪ Planned | #TBD |
| Initial rent challenge analysis (OR Art. 270) | ⚪ Planned | #TBD |
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
| Homegate connector (scraping) | 🟡 Built but blocked by DataDome | #TBD |
| Immoscout24 connector | ⚪ Planned | #TBD |
| WG-Zimmer connector | 💡 Idea | #TBD |
| PLZ filter fix (exclude Thurgau/SG) | ⚪ Planned | #TBD |

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
| Design system (palette, typography) | 🟡 First pass done | #TBD |
| Dark/muted map style | 🟡 Implemented | — |
| Comparison mode | ⚪ Planned | #TBD |
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
| CI/CD (GitHub Actions) | ⚪ Planned | #TBD |
| Deploy frontend (Vercel) | ⚪ Planned | #TBD |
| Deploy backend (Railway / Supabase) | ⚪ Planned | #TBD |
| PostgreSQL (replace SQLite for prod) | ⚪ Planned | #TBD |
| Daily pipeline scheduler (cron) | ⚪ Planned | #TBD |

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
| UGZ Luftqualität (air quality) | Live API | City | Real-time | ⚪ Identified |
| ZVV/SBB timetable | GTFS / API | Canton | Periodic | ⚪ Identified |
| OSM Overpass (amenities) | API | Global | Real-time | ⚪ Identified |
| Baugesuche Stadt Zürich | Open Data | City | Periodic | ⚪ Identified |
| BAFU sonBASE (national noise) | WMS | National | Periodic | ⚪ Identified |
| Referenzzinssatz (SNB) | Web page | National | Quarterly | ⚪ Identified |
| Gemeinde tax rates | Published tables | Canton | Annual | ⚪ Identified |

---

## Timeline (Original → Actual)

| Phase | Original Timeline | Actual Status |
|-------|-------------------|---------------|
| Phase 0: Foundation | Apr–May 2026 | 🟢 Complete (done in 1 day) |
| Phase 1: Core Product | Jun–Aug 2026 | 🟡 In progress (map + layers done, missing commute/amenities/comparison/deploy) |
| Phase 2: Demand Side | Sep–Dec 2026 | 🟡 Partially started (listing ingestion done, auth/profiles/watchlists not started) |
| Phase 3: Marketplace | Jan–Mar 2027 | ⚪ Not started |
| Phase 4: Intelligence | Apr–Jun 2027 | ⚪ Not started |
| Phase 5: Scale | Jul–Sep 2027 | ⚪ Not started |

---

## Next Actions

_Update this section at the start of each work session._

1. **Commute isochrones** — highest-impact missing layer for "where should I live?"
2. **Amenities & walkability** — groceries, cafés, schools nearby per Quartier
3. **Comparison mode** — once the data is rich enough to be worth comparing
4. **Deploy** — get a live URL
5. **PLZ filter fix** — exclude non-Zürich listings