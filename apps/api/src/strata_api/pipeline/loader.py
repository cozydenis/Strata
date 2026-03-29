"""Bulk-upsert GWR records into the database.

Uses dialect-aware INSERT … ON CONFLICT DO UPDATE so it works with both
SQLite (tests) and PostgreSQL (production).

PostgreSQL path batches rows (BATCH_SIZE per statement) for performance.
SQLite path falls back to session.merge row-by-row.
"""
from __future__ import annotations

import datetime
from typing import Any

from sqlalchemy import Engine
from sqlalchemy.orm import Session

from strata_api.pipeline.schemas import BuildingRecord, EntranceRecord, UnitRecord

BATCH_SIZE = 1_000


def upsert_buildings(engine: Engine, records: list[BuildingRecord]) -> int:
    """Upsert building records; returns the number of rows processed."""
    if not records:
        return 0
    rows = [{"egid": r.egid, **_building_row(r)} for r in records]
    _upsert_batch(engine, "gwr_buildings", ["egid"], rows)
    return len(records)


def upsert_entrances(engine: Engine, records: list[EntranceRecord]) -> int:
    """Upsert entrance records; returns the number of rows processed."""
    if not records:
        return 0
    rows = [{"egid": r.egid, "edid": r.edid, **_entrance_row(r)} for r in records]
    _upsert_batch(engine, "gwr_entrances", ["egid", "edid"], rows)
    return len(records)


def upsert_units(engine: Engine, records: list[UnitRecord]) -> int:
    """Upsert unit records; returns the number of rows processed."""
    if not records:
        return 0
    rows = [{"egid": r.egid, "ewid": r.ewid, **_unit_row(r)} for r in records]
    _upsert_batch(engine, "gwr_units", ["egid", "ewid"], rows)
    return len(records)


# ── batch helpers ───────────────────────────────────────────────────────────────

def _upsert_batch(engine: Engine, table_name: str, pk_cols: list[str], rows: list[dict[str, Any]]) -> None:
    """Dispatch to dialect-specific batch upsert and commit once."""
    with Session(engine) as session:
        if engine.dialect.name == "postgresql":
            for i in range(0, len(rows), BATCH_SIZE):
                _pg_batch(session, table_name, pk_cols, rows[i : i + BATCH_SIZE])
        else:
            for row in rows:
                pk = {k: row[k] for k in pk_cols}
                _merge_row(session, table_name, pk, row)
        session.commit()


def _pg_batch(session: Session, table_name: str, pk_cols: list[str], rows: list[dict[str, Any]]) -> None:
    """Single INSERT … ON CONFLICT DO UPDATE for a batch of rows (PostgreSQL only)."""
    from sqlalchemy import column
    from sqlalchemy import table as sa_table
    from sqlalchemy.dialects.postgresql import insert as pg_insert

    all_cols = list(rows[0].keys())
    update_cols = [c for c in all_cols if c not in pk_cols]

    tbl = sa_table(table_name, *(column(c) for c in all_cols))
    stmt = pg_insert(tbl).values(rows)
    stmt = stmt.on_conflict_do_update(
        index_elements=pk_cols,
        set_={c: getattr(stmt.excluded, c) for c in update_cols},
    )
    session.execute(stmt)


def _merge_row(session: Session, table: str, pk: dict[str, Any], full_row: dict[str, Any]) -> None:
    """Fallback for SQLite: load existing row and update, or create new."""
    from strata_api.db.models.building import Building
    from strata_api.db.models.entrance import Entrance
    from strata_api.db.models.unit import Unit

    model_map = {
        "gwr_buildings": Building,
        "gwr_entrances": Entrance,
        "gwr_units": Unit,
    }
    model_cls = model_map[table]
    obj = session.get(model_cls, pk if len(pk) > 1 else list(pk.values())[0])
    if obj is None:
        obj = model_cls(**full_row)
        session.add(obj)
    else:
        for k, v in full_row.items():
            if k not in pk:
                setattr(obj, k, v)


# ── row builders ────────────────────────────────────────────────────────────────

def _building_row(r: BuildingRecord) -> dict[str, Any]:
    now = datetime.datetime.utcnow()
    return {
        "gstat": r.gstat, "gkat": r.gkat, "gklas": r.gklas,
        "gbauj": r.gbauj, "gabbj": r.gabbj, "garea": r.garea,
        "gastw": r.gastw, "ganzwhg": r.ganzwhg,
        "lat": r.lat, "lon": r.lon,
        "municipality": r.municipality,
        "municipality_code": r.municipality_code,
        "canton": r.canton,
        "data_source": r.data_source,
        "created_at": now, "updated_at": now,
    }


def _entrance_row(r: EntranceRecord) -> dict[str, Any]:
    now = datetime.datetime.utcnow()
    return {
        "strname": r.strname, "deinr": r.deinr, "dplz4": r.dplz4,
        "dplzname": r.dplzname, "doffadr": r.doffadr,
        "lat": r.lat, "lon": r.lon,
        "data_source": r.data_source,
        "created_at": now, "updated_at": now,
    }


def _unit_row(r: UnitRecord) -> dict[str, Any]:
    now = datetime.datetime.utcnow()
    return {
        "edid": r.edid, "wstwk": r.wstwk, "wstwklang": r.wstwklang,
        "wazim": r.wazim, "warea": r.warea, "wkche": r.wkche,
        "wstat": r.wstat, "wbauj": r.wbauj, "wabbj": r.wabbj,
        "dplz4": r.dplz4, "dplzname": r.dplzname,
        "strname": r.strname, "deinr": r.deinr,
        "lat": r.lat, "lon": r.lon,
        "data_source": r.data_source,
        "created_at": now, "updated_at": now,
    }
