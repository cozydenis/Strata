"""TDD tests for the email digest renderer — written BEFORE implementation (RED).

`render_digest` is pure: it turns the watch-event dicts (exactly the shape the
watchlist router produces) into a subject line + plain-text body, or None when
there is nothing worth sending.
"""
from __future__ import annotations

from strata_api.notifications.digest import Digest, render_digest


def _event(**overrides) -> dict:
    base = {
        "type": "new_listing",
        "ts": "2026-06-30T12:00:00",
        "listing_id": 1,
        "egid": 10001,
        "street": "Langstrasse",
        "house_number": "42",
        "plz": 8004,
        "city": "Zürich",
        "rent_gross": 2000,
        "rooms": 3.5,
        "area_m2": 80.0,
        "source_url": "https://flatfox.ch/x/1",
        "old_value": None,
        "new_value": None,
    }
    base.update(overrides)
    return base


def test_zero_events_returns_none():
    assert render_digest([]) is None


def test_single_new_listing_subject_and_body():
    digest = render_digest([_event()])
    assert isinstance(digest, Digest)
    # subject: singular, Strata-branded
    assert "Strata" in digest.subject
    assert "1 update" in digest.subject
    # body carries the building address as a group header
    assert "Langstrasse 42, 8004 Zürich" in digest.body
    # the listing line: German domain terms (Zimmer, /Monat), CHF price
    assert "New listing" in digest.body
    assert "3.5 Zimmer" in digest.body
    assert "CHF 2000/Monat" in digest.body
    assert "https://flatfox.ch/x/1" in digest.body
    # footer references managing watches on the site / reply
    assert "reply" in digest.body.lower()


def test_price_change_line_shows_old_and_new():
    ev = _event(type="price_change", old_value="2200", new_value="2400", listing_id=2)
    digest = render_digest([ev])
    assert digest is not None
    assert "Price change" in digest.body
    assert "CHF 2200" in digest.body
    assert "CHF 2400" in digest.body


def test_listing_gone_line():
    ev = _event(type="listing_gone", listing_id=3)
    digest = render_digest([ev])
    assert digest is not None
    assert "removed" in digest.body.lower()


def test_multiple_events_plural_subject_and_grouping():
    events = [
        _event(listing_id=1, street="Langstrasse", house_number="42",
               source_url="https://flatfox.ch/x/1"),
        _event(listing_id=2, type="price_change", old_value="2200", new_value="2400",
               street="Langstrasse", house_number="42", source_url="https://flatfox.ch/x/2"),
        _event(listing_id=3, street="Baslerstrasse", house_number="7", plz=8048, city="Zürich",
               source_url="https://flatfox.ch/x/3"),
    ]
    digest = render_digest(events)
    assert digest is not None
    assert "3 updates" in digest.subject
    # two distinct building groups, each header appearing exactly once
    assert digest.body.count("Langstrasse 42, 8004 Zürich") == 1
    assert digest.body.count("Baslerstrasse 7, 8048 Zürich") == 1
    # the two Langstrasse events are grouped under a single header — the
    # Baslerstrasse header comes after both Langstrasse listing lines
    lang_idx = digest.body.index("Langstrasse 42")
    bas_idx = digest.body.index("Baslerstrasse 7")
    assert digest.body.index("https://flatfox.ch/x/2") < bas_idx
    assert lang_idx < bas_idx


def test_missing_address_falls_back_to_building_egid():
    ev = _event(street=None, house_number=None, plz=None, city=None, egid=99999)
    digest = render_digest([ev])
    assert digest is not None
    assert "99999" in digest.body


def test_missing_numbers_do_not_crash():
    ev = _event(rooms=None, area_m2=None, rent_gross=None)
    digest = render_digest([ev])
    assert digest is not None
    assert "New listing" in digest.body
