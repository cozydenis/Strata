"""Tests for GET /registry/buildings/{egid}/summary endpoint."""
import datetime
from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from strata_api.db import models  # noqa: F401
from strata_api.db.base import Base
from strata_api.db.models.building import Building
from strata_api.db.models.entrance import Entrance


@pytest.fixture(scope="module")
def summary_engine():
    eng = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(eng)

    now = datetime.datetime.utcnow()
    with Session(eng) as s:
        s.add(Building(
            egid=20001, gstat=1004, gkat=1021, gklas=1110,
            gbauj=1975, gabbj=None, garea=250, gastw=4, ganzwhg=8,
            lat=47.376, lon=8.541,
            municipality="Zürich", municipality_code=261, canton="ZH",
            data_source="stadt", created_at=now, updated_at=now,
        ))
        # building with no entrance
        s.add(Building(
            egid=20002, gstat=1004, gkat=1025, gklas=1110,
            gbauj=None, gabbj=None, garea=120, gastw=2, ganzwhg=2,
            lat=47.380, lon=8.545,
            municipality="Zürich", municipality_code=261, canton="ZH",
            data_source="kanton", created_at=now, updated_at=now,
        ))
        # building with null coordinates
        s.add(Building(
            egid=20003, gstat=1004, gkat=1030, gklas=1110,
            gbauj=2010, gabbj=None, garea=80, gastw=3, ganzwhg=3,
            lat=None, lon=None,
            municipality="Zürich", municipality_code=261, canton="ZH",
            data_source="kanton", created_at=now, updated_at=now,
        ))
        s.add(Entrance(
            egid=20001, edid=1,
            strname="Langstrasse", deinr="12a",
            dplz4=8004, dplzname="Zürich",
            doffadr=1, lat=47.376, lon=8.541,
            data_source="stadt", created_at=now, updated_at=now,
        ))
        # second entrance for 20001 — summary should return the first one
        s.add(Entrance(
            egid=20001, edid=2,
            strname="Langstrasse", deinr="12b",
            dplz4=8004, dplzname="Zürich",
            doffadr=1, lat=47.376, lon=8.541,
            data_source="stadt", created_at=now, updated_at=now,
        ))
        s.commit()
    yield eng
    Base.metadata.drop_all(eng)


@pytest.mark.asyncio
async def test_building_summary_returns_core_fields(summary_engine):
    from strata_api.main import app

    with patch("strata_api.routers.registry.get_engine", return_value=summary_engine):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            r = await c.get("/registry/buildings/20001/summary")

    assert r.status_code == 200
    data = r.json()
    assert data["egid"] == 20001
    assert data["gbauj"] == 1975
    assert data["gkat"] == 1021
    assert data["gastw"] == 4
    assert data["ganzwhg"] == 8
    assert data["lat"] == pytest.approx(47.376, abs=1e-3)
    assert data["lon"] == pytest.approx(8.541, abs=1e-3)


@pytest.mark.asyncio
async def test_building_summary_includes_address(summary_engine):
    from strata_api.main import app

    with patch("strata_api.routers.registry.get_engine", return_value=summary_engine):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            r = await c.get("/registry/buildings/20001/summary")

    assert r.status_code == 200
    data = r.json()
    assert data["strname"] == "Langstrasse"
    assert data["deinr"] == "12a"
    assert data["dplz4"] == 8004
    assert data["dplzname"] == "Zürich"


@pytest.mark.asyncio
async def test_building_summary_no_entrance(summary_engine):
    """Building with no entrances should still return building fields, address fields null."""
    from strata_api.main import app

    with patch("strata_api.routers.registry.get_engine", return_value=summary_engine):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            r = await c.get("/registry/buildings/20002/summary")

    assert r.status_code == 200
    data = r.json()
    assert data["egid"] == 20002
    assert data["gbauj"] is None
    assert data["strname"] is None
    assert data["deinr"] is None
    assert data["dplz4"] is None


@pytest.mark.asyncio
async def test_building_summary_not_found(summary_engine):
    from strata_api.main import app

    with patch("strata_api.routers.registry.get_engine", return_value=summary_engine):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            r = await c.get("/registry/buildings/99999/summary")

    assert r.status_code == 404
