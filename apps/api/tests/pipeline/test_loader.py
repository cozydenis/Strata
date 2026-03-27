"""Tests for pipeline/loader.py — bulk upsert into the database."""
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from strata_api.pipeline.schemas import BuildingRecord, EntranceRecord, UnitRecord


@pytest.fixture(scope="module")
def engine():
    from strata_api.db import models  # noqa: F401
    from strata_api.db.base import Base

    eng = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)


def test_upsert_buildings_inserts_new_rows(engine):
    from strata_api.db.models.building import Building
    from strata_api.pipeline.loader import upsert_buildings

    records = [
        BuildingRecord(egid=1001, data_source="stadt", gstat=1004, lat=47.37, lon=8.54),
        BuildingRecord(egid=1002, data_source="stadt", gstat=1004, lat=47.38, lon=8.55),
    ]
    count = upsert_buildings(engine, records)
    assert count == 2

    with Session(engine) as s:
        rows = s.scalars(select(Building).where(Building.egid.in_([1001, 1002]))).all()
        assert len(rows) == 2


def test_upsert_buildings_updates_existing_row(engine):
    from strata_api.db.models.building import Building
    from strata_api.pipeline.loader import upsert_buildings

    # Insert initial
    upsert_buildings(engine, [BuildingRecord(egid=2001, data_source="kanton", gbauj=1950)])
    # Update with new value
    upsert_buildings(engine, [BuildingRecord(egid=2001, data_source="stadt", gbauj=1980)])

    with Session(engine) as s:
        row = s.get(Building, 2001)
        assert row.gbauj == 1980
        assert row.data_source == "stadt"


def test_upsert_buildings_returns_count(engine):
    from strata_api.pipeline.loader import upsert_buildings

    records = [BuildingRecord(egid=3001 + i, data_source="kanton") for i in range(5)]
    count = upsert_buildings(engine, records)
    assert count == 5


def test_upsert_buildings_empty_list(engine):
    from strata_api.pipeline.loader import upsert_buildings

    count = upsert_buildings(engine, [])
    assert count == 0


def test_upsert_entrances_inserts_new_rows(engine):
    from strata_api.db.models.entrance import Entrance
    from strata_api.pipeline.loader import upsert_entrances

    records = [
        EntranceRecord(egid=1001, edid=0, data_source="stadt", strname="Testgasse", dplz4=8001),
    ]
    count = upsert_entrances(engine, records)
    assert count == 1

    with Session(engine) as s:
        row = s.get(Entrance, {"egid": 1001, "edid": 0})
        assert row is not None
        assert row.strname == "Testgasse"


def test_upsert_entrances_updates_existing_row(engine):
    from strata_api.db.models.entrance import Entrance
    from strata_api.pipeline.loader import upsert_entrances

    upsert_entrances(engine, [EntranceRecord(egid=4001, edid=0, data_source="kanton", dplz4=8400)])
    upsert_entrances(engine, [EntranceRecord(egid=4001, edid=0, data_source="stadt", dplz4=8001)])

    with Session(engine) as s:
        row = s.get(Entrance, {"egid": 4001, "edid": 0})
        assert row.dplz4 == 8001


def test_upsert_units_inserts_new_rows(engine):
    from strata_api.db.models.unit import Unit
    from strata_api.pipeline.loader import upsert_units

    records = [
        UnitRecord(egid=1001, ewid=1, data_source="stadt", wazim=3, warea=75),
        UnitRecord(egid=1001, ewid=2, data_source="stadt", wazim=2, warea=55),
    ]
    count = upsert_units(engine, records)
    assert count == 2

    with Session(engine) as s:
        row = s.get(Unit, {"egid": 1001, "ewid": 1})
        assert row.wazim == 3


def test_upsert_units_updates_existing_row(engine):
    from strata_api.db.models.unit import Unit
    from strata_api.pipeline.loader import upsert_units

    upsert_units(engine, [UnitRecord(egid=5001, ewid=1, data_source="kanton", warea=80)])
    upsert_units(engine, [UnitRecord(egid=5001, ewid=1, data_source="stadt", warea=95)])

    with Session(engine) as s:
        row = s.get(Unit, {"egid": 5001, "ewid": 1})
        assert row.warea == 95
