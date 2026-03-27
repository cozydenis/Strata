"""Tests for SQLAlchemy ORM models — GWR buildings, entrances, units, pipeline_runs."""
import datetime

import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session


@pytest.fixture(scope="module")
def engine():
    from strata_api.db import models  # noqa: F401 — register all models
    from strata_api.db.base import Base

    eng = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)


# ── Building ──────────────────────────────────────────────────────────────────

def test_building_table_exists(engine):
    assert "gwr_buildings" in inspect(engine).get_table_names()


def test_building_primary_key_is_egid(engine):
    cols = {c["name"]: c for c in inspect(engine).get_columns("gwr_buildings")}
    pk_cols = inspect(engine).get_pk_constraint("gwr_buildings")["constrained_columns"]
    assert "egid" in pk_cols
    assert "egid" in cols


def test_building_has_required_columns(engine):
    col_names = {c["name"] for c in inspect(engine).get_columns("gwr_buildings")}
    required = {"egid", "gstat", "gkat", "gklas", "gbauj", "gabbj", "garea", "gastw",
                "ganzwhg", "lat", "lon", "municipality", "municipality_code", "canton",
                "data_source", "created_at", "updated_at"}
    assert required <= col_names


def test_building_insert_and_retrieve(engine):
    from strata_api.db.models.building import Building

    with Session(engine) as session:
        b = Building(
            egid=123456,
            gstat=1004,
            gkat=1020,
            gklas=1122,
            gbauj=1980,
            gabbj=None,
            garea=150,
            gastw=3,
            ganzwhg=4,
            lat=47.376,
            lon=8.541,
            municipality="Zürich",
            municipality_code=261,
            canton="ZH",
            data_source="stadt",
        )
        session.add(b)
        session.commit()

        fetched = session.get(Building, 123456)
        assert fetched is not None
        assert fetched.egid == 123456
        assert fetched.municipality == "Zürich"
        assert fetched.data_source == "stadt"
        assert fetched.lat == pytest.approx(47.376)


def test_building_data_source_defaults_to_unknown(engine):
    from strata_api.db.models.building import Building

    with Session(engine) as session:
        b = Building(egid=999001, lat=47.0, lon=8.0, data_source="kanton")
        session.add(b)
        session.commit()
        fetched = session.get(Building, 999001)
        assert fetched.data_source == "kanton"


# ── Entrance ──────────────────────────────────────────────────────────────────

def test_entrance_table_exists(engine):
    assert "gwr_entrances" in inspect(engine).get_table_names()


def test_entrance_composite_pk(engine):
    pk_cols = inspect(engine).get_pk_constraint("gwr_entrances")["constrained_columns"]
    assert set(pk_cols) == {"egid", "edid"}


def test_entrance_has_required_columns(engine):
    col_names = {c["name"] for c in inspect(engine).get_columns("gwr_entrances")}
    required = {"egid", "edid", "strname", "deinr", "dplz4", "dplzname",
                "lat", "lon", "data_source", "created_at", "updated_at"}
    assert required <= col_names


def test_entrance_insert_and_retrieve(engine):
    from strata_api.db.models.entrance import Entrance

    with Session(engine) as session:
        e = Entrance(
            egid=123456,
            edid=0,
            strname="Quellenstrasse",
            deinr="17",
            dplz4=8005,
            dplzname="Zürich",
            lat=47.376,
            lon=8.541,
            data_source="stadt",
        )
        session.add(e)
        session.commit()

        fetched = session.get(Entrance, {"egid": 123456, "edid": 0})
        assert fetched is not None
        assert fetched.strname == "Quellenstrasse"


# ── Unit ──────────────────────────────────────────────────────────────────────

def test_unit_table_exists(engine):
    assert "gwr_units" in inspect(engine).get_table_names()


def test_unit_composite_pk(engine):
    pk_cols = inspect(engine).get_pk_constraint("gwr_units")["constrained_columns"]
    assert set(pk_cols) == {"egid", "ewid"}


def test_unit_has_required_columns(engine):
    col_names = {c["name"] for c in inspect(engine).get_columns("gwr_units")}
    required = {"egid", "ewid", "edid", "wstwk", "wstwklang", "wazim", "warea",
                "wkche", "wstat", "wbauj", "wabbj", "dplz4", "dplzname",
                "strname", "deinr", "lat", "lon", "data_source",
                "created_at", "updated_at"}
    assert required <= col_names


def test_unit_insert_and_retrieve(engine):
    from strata_api.db.models.unit import Unit

    with Session(engine) as session:
        u = Unit(
            egid=123456,
            ewid=1,
            edid=0,
            wstwk=3100,
            wstwklang="Parterre",
            wazim=3,
            warea=75,
            wkche=1,
            wstat=3004,
            wbauj=1990,
            wabbj=None,
            dplz4=8005,
            dplzname="Zürich",
            strname="Quellenstrasse",
            deinr="17",
            lat=47.376,
            lon=8.541,
            data_source="stadt",
        )
        session.add(u)
        session.commit()

        fetched = session.get(Unit, {"egid": 123456, "ewid": 1})
        assert fetched is not None
        assert fetched.wazim == 3
        assert fetched.warea == 75


# ── PipelineRun ───────────────────────────────────────────────────────────────

def test_pipeline_run_table_exists(engine):
    assert "pipeline_runs" in inspect(engine).get_table_names()


def test_pipeline_run_has_required_columns(engine):
    col_names = {c["name"] for c in inspect(engine).get_columns("pipeline_runs")}
    required = {"id", "run_type", "status", "buildings_upserted",
                "entrances_upserted", "units_upserted",
                "error_message", "started_at", "finished_at"}
    assert required <= col_names


def test_pipeline_run_insert_and_retrieve(engine):
    from strata_api.db.models.pipeline_run import PipelineRun

    with Session(engine) as session:
        run = PipelineRun(
            run_type="stadt",
            status="completed",
            buildings_upserted=100,
            entrances_upserted=120,
            units_upserted=350,
            started_at=datetime.datetime.utcnow(),
            finished_at=datetime.datetime.utcnow(),
        )
        session.add(run)
        session.commit()

        fetched = session.get(PipelineRun, run.id)
        assert fetched is not None
        assert fetched.run_type == "stadt"
        assert fetched.status == "completed"
        assert fetched.buildings_upserted == 100
