---
name: gwr-pipeline
description: GWR data pipeline for the Strata unit registry
---

# GWR Pipeline Skill

## Data Source
The Gebaude- und Wohnungsregister (GWR) is downloadable from housing-stat.ch.
Zurich canton extract contains EGID (building) and EWID (dwelling) records.

## Pipeline Steps
1. Download GWR extract for Kanton Zurich
2. Parse XML/CSV records into structured Python objects
3. Validate and clean (handle missing fields, Swiss-German encoding)
4. Geocode buildings using swisstopo coordinates (already in GWR)
5. Load into PostgreSQL via SQLAlchemy models
6. Cross-reference with Baugesuch data from Stadt Zurich Open Data

## Key Fields
- EGID: building identifier
- EWID: dwelling identifier within building
- GKAT: building category
- GBAUJ: construction year
- WAREA: dwelling area in m2
- WAZIM: number of rooms
- GKODE/GKODN: Swiss LV95 coordinates (convert to WGS84 for MapLibre)

## Testing
Every parser function must be test-covered. Use pytest fixtures with
sample GWR records. Test encoding edge cases (umlauts, special chars).
