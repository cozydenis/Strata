"""TDD tests for the watchlist endpoints — written BEFORE implementation (RED phase).

Auth: Supabase-style HS256 JWTs verified against settings.supabase_jwt_secret.
"""
from __future__ import annotations

import datetime
from unittest.mock import patch

import jwt
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from strata_api.db import models  # noqa: F401
from strata_api.db.base import Base
from strata_api.db.models.building import Building
from strata_api.db.models.unit import Unit

_TEST_SECRET = "test-jwt-secret"
_USER_A = "11111111-1111-1111-1111-111111111111"
_USER_B = "22222222-2222-2222-2222-222222222222"


def _token(sub: str, *, secret: str = _TEST_SECRET, aud: str = "authenticated", expired: bool = False) -> str:
    now = datetime.datetime.now(datetime.UTC)
    exp = now - datetime.timedelta(hours=1) if expired else now + datetime.timedelta(hours=1)
    return jwt.encode({"sub": sub, "aud": aud, "exp": exp}, secret, algorithm="HS256")


def _auth(sub: str = _USER_A, **kwargs) -> dict:
    return {"Authorization": f"Bearer {_token(sub, **kwargs)}"}


@pytest.fixture(autouse=True)
def patch_jwt_secret(monkeypatch):
    from strata_api.config import settings

    monkeypatch.setattr(settings, "supabase_jwt_secret", _TEST_SECRET)


@pytest.fixture
def watch_engine():
    eng = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(eng)
    now = datetime.datetime.utcnow()
    with Session(eng) as s:
        s.add(Building(
            egid=10001, gstat=1004, gkat=1020, gklas=1122,
            gbauj=1990, gabbj=None, garea=200, gastw=5, ganzwhg=10,
            lat=47.38, lon=8.54,
            municipality="Zürich", municipality_code=261, canton="ZH",
            data_source="stadt", created_at=now, updated_at=now,
        ))
        s.add(Unit(
            egid=10001, ewid=1, edid=0, wstwk=3100, wstwklang="Parterre",
            wazim=3, warea=70, wkche=1, wstat=3004, wbauj=1990, wabbj=None,
            dplz4=8001, dplzname="Zürich", strname="Testgasse", deinr="1",
            lat=47.38, lon=8.54, data_source="stadt", created_at=now, updated_at=now,
        ))
        s.commit()
    yield eng
    eng.dispose()


@pytest.fixture
def client(watch_engine):
    from strata_api.main import app

    with patch("strata_api.routers.watchlist.get_engine", return_value=watch_engine):
        transport = ASGITransport(app=app)
        yield AsyncClient(transport=transport, base_url="http://test")


# ── auth ──────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_missing_token_returns_401(client):
    async with client as c:
        resp = await c.get("/watchlist")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_invalid_token_returns_401(client):
    async with client as c:
        resp = await c.get("/watchlist", headers={"Authorization": "Bearer not-a-jwt"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_wrong_secret_returns_401(client):
    async with client as c:
        resp = await c.get("/watchlist", headers=_auth(secret="wrong-secret"))
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_expired_token_returns_401(client):
    async with client as c:
        resp = await c.get("/watchlist", headers=_auth(expired=True))
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_wrong_audience_returns_401(client):
    async with client as c:
        resp = await c.get("/watchlist", headers=_auth(aud="anon"))
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_unconfigured_auth_returns_503(client, monkeypatch):
    from strata_api.config import settings

    monkeypatch.setattr(settings, "supabase_jwt_secret", "")
    async with client as c:
        resp = await c.get("/watchlist", headers=_auth())
    assert resp.status_code == 503


# ── CRUD ──────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_empty_watchlist(client):
    async with client as c:
        resp = await c.get("/watchlist", headers=_auth())
    assert resp.status_code == 200
    assert resp.json() == {"total": 0, "items": []}


@pytest.mark.asyncio
async def test_watch_building_then_listed(client):
    async with client as c:
        created = await c.post("/watchlist", json={"egid": 10001}, headers=_auth())
        listed = await c.get("/watchlist", headers=_auth())

    assert created.status_code == 201
    body = created.json()
    assert body["egid"] == 10001
    assert body["ewid"] is None
    assert body["id"] > 0

    data = listed.json()
    assert data["total"] == 1
    assert data["items"][0]["egid"] == 10001


@pytest.mark.asyncio
async def test_watch_specific_unit(client):
    async with client as c:
        resp = await c.post("/watchlist", json={"egid": 10001, "ewid": 1}, headers=_auth())
    assert resp.status_code == 201
    assert resp.json()["ewid"] == 1


@pytest.mark.asyncio
async def test_watch_unknown_building_returns_404(client):
    async with client as c:
        resp = await c.post("/watchlist", json={"egid": 99999}, headers=_auth())
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_watch_unknown_unit_returns_404(client):
    async with client as c:
        resp = await c.post("/watchlist", json={"egid": 10001, "ewid": 99}, headers=_auth())
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_duplicate_watch_is_idempotent(client):
    async with client as c:
        first = await c.post("/watchlist", json={"egid": 10001}, headers=_auth())
        second = await c.post("/watchlist", json={"egid": 10001}, headers=_auth())
        listed = await c.get("/watchlist", headers=_auth())

    assert first.status_code == 201
    assert second.status_code == 200
    assert second.json()["id"] == first.json()["id"]
    assert listed.json()["total"] == 1


@pytest.mark.asyncio
async def test_unit_and_building_watch_coexist(client):
    async with client as c:
        b = await c.post("/watchlist", json={"egid": 10001}, headers=_auth())
        u = await c.post("/watchlist", json={"egid": 10001, "ewid": 1}, headers=_auth())
        listed = await c.get("/watchlist", headers=_auth())
    assert b.status_code == 201
    assert u.status_code == 201
    assert listed.json()["total"] == 2


@pytest.mark.asyncio
async def test_delete_watch(client):
    async with client as c:
        created = await c.post("/watchlist", json={"egid": 10001}, headers=_auth())
        deleted = await c.delete(f"/watchlist/{created.json()['id']}", headers=_auth())
        listed = await c.get("/watchlist", headers=_auth())
    assert deleted.status_code == 204
    assert listed.json()["total"] == 0


@pytest.mark.asyncio
async def test_delete_unknown_watch_returns_404(client):
    async with client as c:
        resp = await c.delete("/watchlist/12345", headers=_auth())
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_users_cannot_see_or_delete_each_others_watches(client):
    async with client as c:
        created = await c.post("/watchlist", json={"egid": 10001}, headers=_auth(_USER_A))
        other_list = await c.get("/watchlist", headers=_auth(_USER_B))
        other_delete = await c.delete(f"/watchlist/{created.json()['id']}", headers=_auth(_USER_B))
        own_list = await c.get("/watchlist", headers=_auth(_USER_A))

    assert other_list.json()["total"] == 0
    assert other_delete.status_code == 404
    assert own_list.json()["total"] == 1


@pytest.mark.asyncio
async def test_watch_includes_address_summary(client):
    """Watches carry the building address so the panel needs no extra requests."""
    async with client as c:
        await c.post("/watchlist", json={"egid": 10001}, headers=_auth())
        listed = await c.get("/watchlist", headers=_auth())
    item = listed.json()["items"][0]
    assert item["strname"] == "Testgasse"
    assert item["deinr"] == "1"
    assert item["dplz4"] == 8001
