"""Tests for the unit registry read endpoints."""
from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from strata_api.db import models  # noqa: F401
from strata_api.db.base import Base
from strata_api.db.models.building import Building
from strata_api.db.models.unit import Unit


@pytest.fixture(scope="module")
def registry_engine():
    eng = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(eng)

    import datetime

    with Session(eng) as s:
        now = datetime.datetime.utcnow()
        s.add(Building(
            egid=10001, gstat=1004, gkat=1020, gklas=1122,
            gbauj=1990, gabbj=None, garea=200, gastw=5, ganzwhg=10,
            lat=47.38, lon=8.54,
            municipality="Zürich", municipality_code=261, canton="ZH",
            data_source="stadt", created_at=now, updated_at=now,
        ))
        s.add(Building(
            egid=10002, gstat=1004, gkat=1020, gklas=1110,
            gbauj=2005, gabbj=None, garea=300, gastw=3, ganzwhg=6,
            lat=47.39, lon=8.55,
            municipality="Wallisellen", municipality_code=191, canton="ZH",
            data_source="kanton", created_at=now, updated_at=now,
        ))
        s.add(Unit(
            egid=10001, ewid=1, edid=0, wstwk=3100, wstwklang="Parterre",
            wazim=3, warea=70, wkche=1, wstat=3004, wbauj=1990, wabbj=None,
            dplz4=8001, dplzname="Zürich", strname="Testgasse", deinr="1",
            lat=47.38, lon=8.54, data_source="stadt", created_at=now, updated_at=now,
        ))
        s.add(Unit(
            egid=10001, ewid=2, edid=0, wstwk=3101, wstwklang="1. Stock",
            wazim=4, warea=90, wkche=1, wstat=3004, wbauj=1990, wabbj=None,
            dplz4=8001, dplzname="Zürich", strname="Testgasse", deinr="1",
            lat=47.38, lon=8.54, data_source="stadt", created_at=now, updated_at=now,
        ))
        s.commit()
    yield eng
    Base.metadata.drop_all(eng)


@pytest.mark.asyncio
async def test_list_buildings_returns_all(registry_engine):
    from strata_api.main import app

    with patch(
        "strata_api.routers.registry.get_engine", return_value=registry_engine
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/registry/buildings")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2


@pytest.mark.asyncio
async def test_list_buildings_filter_by_data_source(registry_engine):
    from strata_api.main import app

    with patch(
        "strata_api.routers.registry.get_engine", return_value=registry_engine
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/registry/buildings?data_source=kanton")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["egid"] == 10002


@pytest.mark.asyncio
async def test_get_building_by_egid(registry_engine):
    from strata_api.main import app

    with patch(
        "strata_api.routers.registry.get_engine", return_value=registry_engine
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/registry/buildings/10001")

    assert response.status_code == 200
    data = response.json()
    assert data["egid"] == 10001
    assert data["municipality"] == "Zürich"
    assert data["data_source"] == "stadt"


@pytest.mark.asyncio
async def test_get_building_not_found(registry_engine):
    from strata_api.main import app

    with patch(
        "strata_api.routers.registry.get_engine", return_value=registry_engine
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/registry/buildings/99999")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_units_for_building(registry_engine):
    from strata_api.main import app

    with patch(
        "strata_api.routers.registry.get_engine", return_value=registry_engine
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/registry/buildings/10001/units")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert all(u["egid"] == 10001 for u in data["items"])


@pytest.mark.asyncio
async def test_get_unit_by_egid_ewid(registry_engine):
    from strata_api.main import app

    with patch(
        "strata_api.routers.registry.get_engine", return_value=registry_engine
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/registry/buildings/10001/units/1")

    assert response.status_code == 200
    data = response.json()
    assert data["egid"] == 10001
    assert data["ewid"] == 1
    assert data["wazim"] == 3


@pytest.mark.asyncio
async def test_get_unit_not_found(registry_engine):
    from strata_api.main import app

    with patch(
        "strata_api.routers.registry.get_engine", return_value=registry_engine
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/registry/buildings/10001/units/999")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_buildings_pagination(registry_engine):
    from strata_api.main import app

    with patch(
        "strata_api.routers.registry.get_engine", return_value=registry_engine
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/registry/buildings?limit=1&offset=0")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 1
