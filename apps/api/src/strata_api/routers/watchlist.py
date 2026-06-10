"""Watchlist endpoints — authenticated users watch buildings or specific units.

The wedge feature of Layer 2: "I want this one. Watch it. Tell me when it
moves." All endpoints require a Supabase JWT (see strata_api.auth).
"""
from __future__ import annotations

import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from strata_api.auth import get_current_user
from strata_api.db.models.building import Building
from strata_api.db.models.entrance import Entrance
from strata_api.db.models.listing import Listing, ListingHistory, ListingUnitMatch
from strata_api.db.models.unit import Unit
from strata_api.db.models.watch import Watch
from strata_api.db.session import get_engine

router = APIRouter(prefix="/watchlist", tags=["watchlist"])


class WatchCreate(BaseModel):
    egid: int
    ewid: int | None = None


def _address_for(s: Session, egid: int, ewid: int | None) -> dict:
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


def _watch_dict(s: Session, w: Watch) -> dict:
    return {
        "id": w.id,
        "egid": w.egid,
        "ewid": w.ewid,
        "created_at": w.created_at.isoformat(),
        **_address_for(s, w.egid, w.ewid),
    }


@router.get("")
def list_watches(user_id: str = Depends(get_current_user)) -> dict:
    """All watches of the current user, newest first, with address summaries."""
    engine = get_engine()
    with Session(engine) as s:
        rows = (
            s.execute(
                select(Watch).where(Watch.user_id == user_id).order_by(Watch.created_at.desc(), Watch.id.desc())
            )
            .scalars()
            .all()
        )
        items = [_watch_dict(s, w) for w in rows]
    return {"total": len(items), "items": items}


@router.post("", status_code=201)
def create_watch(
    payload: WatchCreate,
    response: Response,
    user_id: str = Depends(get_current_user),
) -> dict:
    """Watch a building (no ewid) or a specific unit. Idempotent: re-watching returns 200."""
    engine = get_engine()
    with Session(engine) as s:
        if s.get(Building, payload.egid) is None:
            raise HTTPException(status_code=404, detail=f"Building {payload.egid} not found.")
        if payload.ewid is not None and s.get(Unit, {"egid": payload.egid, "ewid": payload.ewid}) is None:
            raise HTTPException(status_code=404, detail=f"Unit ({payload.egid}, {payload.ewid}) not found.")

        existing = s.execute(
            select(Watch).where(
                Watch.user_id == user_id,
                Watch.egid == payload.egid,
                Watch.ewid.is_(None) if payload.ewid is None else Watch.ewid == payload.ewid,
            )
        ).scalar_one_or_none()
        if existing is not None:
            response.status_code = 200
            return _watch_dict(s, existing)

        watch = Watch(
            user_id=user_id,
            egid=payload.egid,
            ewid=payload.ewid,
            created_at=datetime.datetime.now(datetime.UTC).replace(tzinfo=None),
        )
        s.add(watch)
        s.commit()
        s.refresh(watch)
        return _watch_dict(s, watch)


_EVENT_LIMIT = 50
_PRICE_FIELDS = ("rent_gross", "rent_net")


def _event_base(
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


@router.get("/events")
def list_events(
    days: int = Query(default=90, ge=1, le=365),
    user_id: str = Depends(get_current_user),
) -> dict:
    """Activity feed for the user's watched buildings, newest first.

    Derived events: new_listing (first_seen), price_change (listing_history
    rent fields), listing_gone (deactivation).
    """
    cutoff = datetime.datetime.utcnow() - datetime.timedelta(days=days)
    engine = get_engine()
    with Session(engine) as s:
        watched_egids = set(
            s.execute(select(Watch.egid).where(Watch.user_id == user_id)).scalars().all()
        )
        if not watched_egids:
            return {"total": 0, "items": []}

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
                addr_cache[egid] = _address_for(s, egid, None)
            return addr_cache[egid]

        events: list[dict] = []
        listing_egid: dict[int, int] = {}
        for listing, egid in rows:
            if listing.id in listing_egid:
                continue  # multiple matches to watched buildings — count once
            listing_egid[listing.id] = egid
            fallback = _fallback(egid) if listing.street is None else None

            if listing.first_seen >= cutoff:
                events.append(_event_base("new_listing", listing.first_seen, listing, egid, fallback))
            if not listing.is_active and listing.last_seen >= cutoff:
                events.append(_event_base("listing_gone", listing.last_seen, listing, egid, fallback))

        if listing_egid:
            history_rows = s.execute(
                select(ListingHistory, Listing)
                .join(Listing, Listing.id == ListingHistory.listing_id)
                .where(
                    ListingHistory.listing_id.in_(listing_egid),
                    ListingHistory.field_changed.in_(_PRICE_FIELDS),
                    ListingHistory.changed_at >= cutoff,
                )
            ).all()
            for change, listing in history_rows:
                egid = listing_egid[listing.id]
                fallback = _fallback(egid) if listing.street is None else None
                event = _event_base("price_change", change.changed_at, listing, egid, fallback)
                event["old_value"] = change.old_value
                event["new_value"] = change.new_value
                events.append(event)

    events.sort(key=lambda e: e["ts"], reverse=True)
    events = events[:_EVENT_LIMIT]
    return {"total": len(events), "items": events}


@router.delete("/{watch_id}", status_code=204)
def delete_watch(watch_id: int, user_id: str = Depends(get_current_user)) -> Response:
    """Remove a watch. 404 for unknown ids and for other users' watches."""
    engine = get_engine()
    with Session(engine) as s:
        watch = s.get(Watch, watch_id)
        if watch is None or watch.user_id != user_id:
            raise HTTPException(status_code=404, detail=f"Watch {watch_id} not found.")
        s.delete(watch)
        s.commit()
    return Response(status_code=204)
