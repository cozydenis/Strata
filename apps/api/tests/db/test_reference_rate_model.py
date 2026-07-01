"""Tests for the ReferenceRate model and the listings.base_reference_rate column."""
import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from strata_api.db import models  # noqa: F401
from strata_api.db.base import Base
from strata_api.db.models.listing import Listing
from strata_api.db.models.reference_rate import ReferenceRate


@pytest.fixture
def engine():
    eng = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(eng)
    return eng


def test_reference_rate_roundtrips(engine):
    with Session(engine) as s:
        s.add(ReferenceRate(valid_from=datetime.date(2025, 9, 1), rate_percent=1.25, source="bwo"))
        s.commit()
        row = s.query(ReferenceRate).one()
        assert row.rate_percent == 1.25
        assert row.source == "bwo"


def test_reference_rate_valid_from_is_unique(engine):
    with Session(engine) as s:
        s.add(ReferenceRate(valid_from=datetime.date(2025, 9, 1), rate_percent=1.25))
        s.add(ReferenceRate(valid_from=datetime.date(2025, 9, 1), rate_percent=1.50))
        with pytest.raises(IntegrityError):
            s.commit()


def test_listing_base_reference_rate_defaults_none_and_roundtrips(engine):
    now = datetime.datetime.utcnow()
    with Session(engine) as s:
        s.add(Listing(source="flatfox", source_id="A", first_seen=now, last_seen=now))
        s.add(Listing(source="flatfox", source_id="B", base_reference_rate=1.75, first_seen=now, last_seen=now))
        s.commit()
        a = s.query(Listing).filter_by(source_id="A").one()
        b = s.query(Listing).filter_by(source_id="B").one()
        assert a.base_reference_rate is None
        assert b.base_reference_rate == 1.75
