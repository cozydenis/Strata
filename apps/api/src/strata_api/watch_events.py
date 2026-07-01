"""Derive watch events from listings matched to watched buildings.

This is the single source of truth for the event-derivation logic shared by the
`/watchlist/events` feed and the email-digest runner. An "event" is a plain
dict describing something that moved on a watched building:

- new_listing:   a listing first seen within the window
- price_change:  a listing_history rent change within the window
- listing_gone:  a listing deactivated within the window
"""
from __future__ import annotations

import datetime
from collections.abc import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from strata_api.db.models.entrance import Entrance
from strata_api.db.models.listing import Listing, ListingHistory, ListingUnitMatch
from strata_api.db.models.unit import Unit

PRICE_FIELDS = ("rent_gross", "rent_net")


def address_for(s: Session, egid: int, ewid: int | None) -> dict:
    """Address fields for a watch — the unit's own address, else first entrance, else first unit."""
    if ewid is not None:
        unit = s.get(Unit, {"egid": egid, "ewid": ewid})
        if unit is not None and unit.strname:
            return {"strname": unit.strname, "deinr": unit.deinr, "dplz4": unit.dplz4, "dplzname": unit.dplzname}
    entrance = s.execute(
        select(Entrance).where(Entrance.egid == egid).order_by(Entrance.edid).limit(1)
    ).scalar_one_or_none()
    if entrance is not None:
        return {
            "strname": entrance.strname,
            "deinr": entrance.deinr,
            "dplz4": entrance.dplz4,
            "dplzname": entrance.dplzname,
        }
    unit = s.execute(select(Unit).where(Unit.egid == egid).order_by(Unit.ewid).limit(1)).scalar_one_or_none()
    if unit is not None:
        return {"strname": unit.strname, "deinr": unit.deinr, "dplz4": unit.dplz4, "dplzname": unit.dplzname}
    return {"strname": None, "deinr": None, "dplz4": None, "dplzname": None}


def event_base(
    event_type: str,
    ts: datetime.datetime,
    listing: Listing,
    egid: int,
    fallback_addr: dict | None = None,
) -> dict:
    # Geo-fallback matches often carry no address — use the building's GWR address
    addr = fallback_addr if listing.street is None and fallback_addr is not None else None
    return {
        "type": event_type,
        "ts": ts.isoformat(),
        "listing_id": listing.id,
        "egid": egid,
        "street": addr["strname"] if addr else listing.street,
        "house_number": addr["deinr"] if addr else listing.house_number,
        "plz": addr["dplz4"] if addr else listing.plz,
        "city": addr["dplzname"] if addr else listing.city,
        "rent_gross": listing.rent_gross,
        "rooms": listing.rooms,
        "area_m2": listing.area_m2,
        "source_url": listing.source_url,
        "old_value": None,
        "new_value": None,
    }


def derive_events(
    s: Session,
    watched_egids: Iterable[int],
    cutoff: datetime.datetime,
) -> list[dict]:
    """All events on the given watched buildings since `cutoff` (unsorted).

    Callers decide how to sort/limit. Returns [] when there are no watched
    buildings or nothing matched within the window.
    """
    watched_egids = set(watched_egids)
    if not watched_egids:
        return []

    # All listings matched to watched buildings, with their matched egid
    rows = s.execute(
        select(Listing, ListingUnitMatch.egid)
        .join(ListingUnitMatch, ListingUnitMatch.listing_id == Listing.id)
        .where(ListingUnitMatch.egid.in_(watched_egids))
    ).all()

    # Building addresses for listings that carry none (geo-fallback matches)
    addr_cache: dict[int, dict] = {}

    def _fallback(egid: int) -> dict:
        if egid not in addr_cache:
            addr_cache[egid] = address_for(s, egid, None)
        return addr_cache[egid]

    events: list[dict] = []
    listing_egid: dict[int, int] = {}
    for listing, egid in rows:
        if listing.id in listing_egid:
            continue  # multiple matches to watched buildings — count once
        listing_egid[listing.id] = egid
        fallback = _fallback(egid) if listing.street is None else None

        if listing.first_seen >= cutoff:
            events.append(event_base("new_listing", listing.first_seen, listing, egid, fallback))
        if not listing.is_active and listing.last_seen >= cutoff:
            events.append(event_base("listing_gone", listing.last_seen, listing, egid, fallback))

    if listing_egid:
        history_rows = s.execute(
            select(ListingHistory, Listing)
            .join(Listing, Listing.id == ListingHistory.listing_id)
            .where(
                ListingHistory.listing_id.in_(listing_egid),
                ListingHistory.field_changed.in_(PRICE_FIELDS),
                ListingHistory.changed_at >= cutoff,
            )
        ).all()
        for change, listing in history_rows:
            egid = listing_egid[listing.id]
            fallback = _fallback(egid) if listing.street is None else None
            event = event_base("price_change", change.changed_at, listing, egid, fallback)
            event["old_value"] = change.old_value
            event["new_value"] = change.new_value
            events.append(event)

    return events
