"""Pipeline runner — orchestrates download → parse → dedup → load for each source."""
from __future__ import annotations

import datetime
from dataclasses import dataclass

from sqlalchemy import Engine, select
from sqlalchemy.orm import Session

from strata_api.db.models.building import Building
from strata_api.db.models.pipeline_run import PipelineRun
from strata_api.pipeline.dedup import (
    filter_kanton_buildings,
    filter_kanton_entrances,
    filter_kanton_units,
)
from strata_api.pipeline.downloader import (
    KANTON_EINGAENGE_URL,
    KANTON_GEBAEUDE_URL,
    KANTON_WOHNUNGEN_URL,
    STADT_EINGAENGE_URL,
    STADT_GEBAEUDE_URL,
    STADT_WOHNUNGEN_URL,
    download_csv_stream,
    download_geojson,
)
from strata_api.pipeline.loader import upsert_buildings, upsert_entrances, upsert_units
from strata_api.pipeline.parsers.kanton_parser import (
    parse_buildings_csv,
    parse_entrances_csv,
    parse_units_csv,
)
from strata_api.pipeline.parsers.stadt_parser import (
    parse_buildings as parse_stadt_buildings,
)
from strata_api.pipeline.parsers.stadt_parser import (
    parse_entrances as parse_stadt_entrances,
)
from strata_api.pipeline.parsers.stadt_parser import (
    parse_units as parse_stadt_units,
)


@dataclass
class PipelineResult:
    """Summary of a completed pipeline run."""

    run_id: int
    run_type: str
    status: str
    buildings_upserted: int = 0
    entrances_upserted: int = 0
    units_upserted: int = 0
    error_message: str | None = None


def run_stadt_pipeline(engine: Engine) -> PipelineResult:
    """Download Stadt Zürich GWR data, parse, and load into the database."""
    run = _start_run(engine, "stadt")
    try:
        gebaeude_gj = download_geojson(STADT_GEBAEUDE_URL)
        eingaenge_gj = download_geojson(STADT_EINGAENGE_URL)
        wohnungen_gj = download_geojson(STADT_WOHNUNGEN_URL)

        buildings = parse_stadt_buildings(gebaeude_gj)
        entrances = parse_stadt_entrances(eingaenge_gj)
        units = parse_stadt_units(wohnungen_gj)

        b_count = upsert_buildings(engine, buildings)
        e_count = upsert_entrances(engine, entrances)
        u_count = upsert_units(engine, units)

        return _finish_run(engine, run, b_count, e_count, u_count)
    except Exception as exc:
        return _fail_run(engine, run, str(exc))


def run_kanton_pipeline(engine: Engine) -> PipelineResult:
    """Download Kanton Zürich GWR CSV data, deduplicate, and load."""
    run = _start_run(engine, "kanton")
    try:
        # Collect all Stadt EGIDs currently in the DB so we can skip them
        with Session(engine) as session:
            stad_egids = frozenset(
                row for (row,) in session.execute(
                    select(Building.egid).where(Building.data_source == "stadt")
                )
            )

        buildings = list(parse_buildings_csv(download_csv_stream(KANTON_GEBAEUDE_URL)))
        entrances = list(parse_entrances_csv(download_csv_stream(KANTON_EINGAENGE_URL)))
        units = list(parse_units_csv(download_csv_stream(KANTON_WOHNUNGEN_URL)))

        buildings = filter_kanton_buildings(buildings, stad_egids)
        entrances = filter_kanton_entrances(entrances, stad_egids)
        units = filter_kanton_units(units, stad_egids)

        b_count = upsert_buildings(engine, buildings)
        e_count = upsert_entrances(engine, entrances)
        u_count = upsert_units(engine, units)

        return _finish_run(engine, run, b_count, e_count, u_count)
    except Exception as exc:
        return _fail_run(engine, run, str(exc))


# ── internal helpers ──────────────────────────────────────────────────────────

def _start_run(engine: Engine, run_type: str) -> PipelineRun:
    with Session(engine) as session:
        run = PipelineRun(
            run_type=run_type,
            status="started",
            started_at=datetime.datetime.utcnow(),
        )
        session.add(run)
        session.commit()
        session.refresh(run)
        return run


def _finish_run(
    engine: Engine,
    run: PipelineRun,
    b_count: int,
    e_count: int,
    u_count: int,
) -> PipelineResult:
    with Session(engine) as session:
        db_run = session.get(PipelineRun, run.id)
        assert db_run is not None
        db_run.status = "completed"
        db_run.buildings_upserted = b_count
        db_run.entrances_upserted = e_count
        db_run.units_upserted = u_count
        db_run.finished_at = datetime.datetime.utcnow()
        session.commit()

    return PipelineResult(
        run_id=run.id,
        run_type=run.run_type,
        status="completed",
        buildings_upserted=b_count,
        entrances_upserted=e_count,
        units_upserted=u_count,
    )


def _fail_run(engine: Engine, run: PipelineRun, error: str) -> PipelineResult:
    with Session(engine) as session:
        db_run = session.get(PipelineRun, run.id)
        assert db_run is not None
        db_run.status = "failed"
        db_run.error_message = error
        db_run.finished_at = datetime.datetime.utcnow()
        session.commit()

    return PipelineResult(
        run_id=run.id,
        run_type=run.run_type,
        status="failed",
        error_message=error,
    )
