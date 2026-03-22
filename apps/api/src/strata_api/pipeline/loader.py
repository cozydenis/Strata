"""Bulk-upsert GWR records into the database.

Uses dialect-aware INSERT … ON CONFLICT DO UPDATE so it works with both
SQLite (tests) and PostgreSQL (production).
"""
from __future__ import annotations

import datetime
from typing import Any

from sqlalchemy import Engine, text
from sqlalchemy.orm import Session

from strata_api.pipeline.schemas import BuildingRecord, EntranceRecord, UnitRecord


def upsert_buildings(engine: Engine, records: list[BuildingRecord]) -> int:
    """Upsert building records; returns the number of rows processed."""
    if not records:
        return 0
    with Session(engine) as session:
        for r in records:
            _upsert_row(session, "gwr_buildings", {"egid": r.egid}, _building_row(r))
        session.commit()
    return len(records)


def upsert_entrances(engine: Engine, records: list[EntranceRecord]) -> int:
    """Upsert entrance records; returns the number of rows processed."""
    if not records:
        return 0
    with Session(engine) as session:
        for r in records:
            _upsert_row(session, "gwr_entrances", {"egid": r.egid, "edid": r.edid}, _entrance_row(r))
        session.commit()
    return len(records)


def upsert_units(engine: Engine, records: list[UnitRecord]) -> int:
    """Upsert unit records; returns the number of rows processed."""
    if not records:
        return 0
    with Session(engine) as session:
        for r in records:
            _upsert_row(session, "gwr_units", {"egid": r.egid, "ewid": r.ewid}, _unit_row(r))
        session.commit()
    return len(records)


# ── helpers ────────────────────────────────────────────────────────────────────

def _upsert_row(session: Session, table: str, pk: dict[str, Any], row: dict[str, Any]) -> None:
    """Dialect-agnostic single-row upsert."""
    dialect = session.bind.dialect.name  # type: ignore[union-attr]
    full_row = {**pk, **row}

    if dialect == "postgresql":
        from sqlalchemy.dialects.postgresql import insert as pg_insert
        from sqlalchemy import table as sa_table, column

        stmt = pg_insert(sa_table(table, *(column(k) for k in full_row))).values(**full_row)
        stmt = stmt.on_conflict_do_update(index_elements=list(pk), set_=row)
        session.execute(stmt)
    else:
        # SQLite and others — use session.merge via a mapped class lookup
        mapper = session.get_bind().dialect  # type: ignore[assignment]
        _merge_row(session, table, pk, full_row)


def _merge_row(session: Session, table: str, pk: dict[str, Any], full_row: dict[str, Any]) -> None:
    """Fallback: load existing row and update, or create new."""
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
