"""Tests for the watches.last_notified_at column added for email notifications."""
from __future__ import annotations

import datetime

import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session

from strata_api.db import models  # noqa: F401 — register all models
from strata_api.db.base import Base
from strata_api.db.models.watch import Watch

_NOW = datetime.datetime(2026, 7, 1, 12, 0, 0)


@pytest.fixture()
def engine():
    eng = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)


def test_watches_has_last_notified_at_column(engine):
    col_names = {c["name"] for c in inspect(engine).get_columns("watches")}
    assert "last_notified_at" in col_names


def test_last_notified_at_defaults_to_none(engine):
    with Session(engine) as s:
        w = Watch(user_id="u1", egid=10001, ewid=None, created_at=_NOW)
        s.add(w)
        s.commit()
        s.refresh(w)
        assert w.last_notified_at is None


def test_last_notified_at_roundtrip(engine):
    stamp = datetime.datetime(2026, 6, 25, 9, 30, 0)
    with Session(engine) as s:
        s.add(Watch(user_id="u1", egid=10001, ewid=None, created_at=_NOW, last_notified_at=stamp))
        s.commit()
    with Session(engine) as s:
        fetched = s.query(Watch).filter_by(user_id="u1").one()
        assert fetched.last_notified_at == stamp
