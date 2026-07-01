"""TDD tests for the notification runner — written BEFORE implementation (RED).

The runner walks every distinct user with watches, derives events since that
user's last_notified_at (capped to a 7-day lookback), resolves an email, sends a
digest, and stamps last_notified_at on success only. Failures are isolated per
user and reflected in the returned summary counts.
"""
from __future__ import annotations

import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from strata_api.db import models  # noqa: F401 — register all models
from strata_api.db.base import Base
from strata_api.db.models.building import Building
from strata_api.db.models.entrance import Entrance
from strata_api.db.models.listing import Listing, ListingUnitMatch
from strata_api.db.models.watch import Watch
from strata_api.notifications.runner import NotificationSummary, run_notifications

NOW = datetime.datetime(2026, 7, 1, 12, 0, 0)


class FakeSender:
    """Records every send; optionally raises for specific recipients."""

    def __init__(self, fail_for: set[str] | None = None):
        self.sent: list[tuple[str, str, str]] = []
        self._fail_for = fail_for or set()

    def send(self, to: str, subject: str, body: str) -> None:
        if to in self._fail_for:
            raise RuntimeError("smtp exploded")
        self.sent.append((to, subject, body))


def _resolver(mapping: dict[str, str]):
    def _resolve(user_id: str) -> str | None:
        return mapping.get(user_id)

    return _resolve


_LISTING_ID = [0]


def _next_listing_id() -> int:
    _LISTING_ID[0] += 1
    return _LISTING_ID[0]


def _engine():
    eng = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(eng)
    return eng


def _add_building(s: Session, egid: int) -> None:
    s.add(Building(
        egid=egid, gstat=1004, gkat=1020, gklas=1122,
        gbauj=1990, gabbj=None, garea=200, gastw=5, ganzwhg=10,
        lat=47.38, lon=8.54, municipality="Zürich", municipality_code=261,
        canton="ZH", data_source="stadt", created_at=NOW, updated_at=NOW,
    ))
    s.add(Entrance(
        egid=egid, edid=0, strname="Registergasse", deinr="7",
        dplz4=8001, dplzname="Zürich", lat=47.38, lon=8.54,
        data_source="stadt", created_at=NOW, updated_at=NOW,
    ))


def _add_watch_with_new_listing(
    s: Session, user_id: str, egid: int, *, first_seen_days_ago: int, last_notified=None
) -> None:
    """A user watching `egid`, which has a listing first seen N days ago."""
    _add_building(s, egid)
    s.add(Watch(user_id=user_id, egid=egid, ewid=None, created_at=NOW, last_notified_at=last_notified))
    lid = _next_listing_id()
    s.add(Listing(
        id=lid, source="flatfox", source_id=f"src-{lid}",
        rent_gross=2000, rooms=3.5, area_m2=80.0,
        street="Langstrasse", house_number="42", plz=8004, city="Zürich",
        source_url=f"https://flatfox.ch/x/{lid}",
        first_seen=NOW - datetime.timedelta(days=first_seen_days_ago),
        last_seen=NOW, is_active=True, created_at=NOW, updated_at=NOW,
    ))
    s.add(ListingUnitMatch(listing_id=lid, egid=egid, ewid=None,
                           match_confidence="exact", matched_egid=egid))


def test_sends_digest_and_stamps_last_notified_on_success():
    eng = _engine()
    with Session(eng) as s:
        _add_watch_with_new_listing(s, "userA", 20001, first_seen_days_ago=2)
        s.commit()

    sender = FakeSender()
    summary = run_notifications(
        eng, sender=sender, resolve_email=_resolver({"userA": "a@example.com"}), now=NOW
    )

    assert isinstance(summary, NotificationSummary)
    assert summary.users == 1
    assert summary.sent == 1
    assert len(sender.sent) == 1
    assert sender.sent[0][0] == "a@example.com"

    with Session(eng) as s:
        w = s.query(Watch).filter_by(user_id="userA").one()
        assert w.last_notified_at == NOW


def test_no_events_skips_and_does_not_stamp():
    eng = _engine()
    with Session(eng) as s:
        # listing first seen 400 days ago → outside the 7-day lookback
        _add_watch_with_new_listing(s, "userB", 20002, first_seen_days_ago=400)
        s.commit()

    sender = FakeSender()
    summary = run_notifications(
        eng, sender=sender, resolve_email=_resolver({"userB": "b@example.com"}), now=NOW
    )
    assert summary.sent == 0
    assert summary.skipped_no_events == 1
    assert sender.sent == []
    with Session(eng) as s:
        assert s.query(Watch).filter_by(user_id="userB").one().last_notified_at is None


def test_no_email_skips_and_does_not_stamp():
    eng = _engine()
    with Session(eng) as s:
        _add_watch_with_new_listing(s, "userC", 20003, first_seen_days_ago=2)
        s.commit()

    sender = FakeSender()
    summary = run_notifications(eng, sender=sender, resolve_email=_resolver({}), now=NOW)
    assert summary.skipped_no_email == 1
    assert summary.sent == 0
    assert sender.sent == []
    with Session(eng) as s:
        assert s.query(Watch).filter_by(user_id="userC").one().last_notified_at is None


def test_last_notified_cutoff_excludes_already_notified_events():
    eng = _engine()
    with Session(eng) as s:
        # event 3 days ago, but user was notified 2 days ago → nothing new
        _add_watch_with_new_listing(
            s, "userE", 20005, first_seen_days_ago=3,
            last_notified=NOW - datetime.timedelta(days=2),
        )
        s.commit()

    sender = FakeSender()
    summary = run_notifications(
        eng, sender=sender, resolve_email=_resolver({"userE": "e@example.com"}), now=NOW
    )
    assert summary.skipped_no_events == 1
    assert summary.sent == 0


def test_last_notified_cutoff_includes_events_after_stamp():
    eng = _engine()
    with Session(eng) as s:
        # event 3 days ago, user last notified 5 days ago → event is fresh
        _add_watch_with_new_listing(
            s, "userF", 20006, first_seen_days_ago=3,
            last_notified=NOW - datetime.timedelta(days=5),
        )
        s.commit()

    sender = FakeSender()
    summary = run_notifications(
        eng, sender=sender, resolve_email=_resolver({"userF": "f@example.com"}), now=NOW
    )
    assert summary.sent == 1


def test_per_user_failure_is_isolated():
    eng = _engine()
    with Session(eng) as s:
        _add_watch_with_new_listing(s, "userGood", 20007, first_seen_days_ago=1)
        _add_watch_with_new_listing(s, "userBad", 20008, first_seen_days_ago=1)
        s.commit()

    sender = FakeSender(fail_for={"bad@example.com"})
    summary = run_notifications(
        eng, sender=sender,
        resolve_email=_resolver({"userGood": "good@example.com", "userBad": "bad@example.com"}),
        now=NOW,
    )
    assert summary.users == 2
    assert summary.sent == 1
    assert summary.failed == 1
    # good user was stamped; bad user was not
    with Session(eng) as s:
        assert s.query(Watch).filter_by(user_id="userGood").one().last_notified_at == NOW
        assert s.query(Watch).filter_by(user_id="userBad").one().last_notified_at is None


def test_summary_counts_across_mixed_population():
    eng = _engine()
    with Session(eng) as s:
        _add_watch_with_new_listing(s, "u_sent", 30001, first_seen_days_ago=1)
        _add_watch_with_new_listing(s, "u_noevents", 30002, first_seen_days_ago=400)
        _add_watch_with_new_listing(s, "u_noemail", 30003, first_seen_days_ago=1)
        _add_watch_with_new_listing(s, "u_fail", 30004, first_seen_days_ago=1)
        s.commit()

    sender = FakeSender(fail_for={"fail@example.com"})
    summary = run_notifications(
        eng, sender=sender,
        resolve_email=_resolver({
            "u_sent": "sent@example.com",
            "u_noevents": "ne@example.com",
            "u_fail": "fail@example.com",
        }),
        now=NOW,
    )
    assert summary == NotificationSummary(
        users=4, sent=1, skipped_no_events=1, skipped_no_email=1, failed=1
    )


def test_stamps_all_watches_of_a_user():
    eng = _engine()
    with Session(eng) as s:
        _add_watch_with_new_listing(s, "multi", 40001, first_seen_days_ago=1)
        # second watch for the same user, no fresh events of its own
        _add_building(s, 40002)
        s.add(Watch(user_id="multi", egid=40002, ewid=None, created_at=NOW))
        s.commit()

    sender = FakeSender()
    summary = run_notifications(
        eng, sender=sender, resolve_email=_resolver({"multi": "m@example.com"}), now=NOW
    )
    assert summary.sent == 1
    with Session(eng) as s:
        stamps = [w.last_notified_at for w in s.query(Watch).filter_by(user_id="multi").all()]
        assert stamps == [NOW, NOW]


@pytest.fixture(autouse=True)
def _reset_listing_ids():
    _LISTING_ID[0] = 0
    yield
