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
from strata_api.db.models.unit import Unit
from strata_api.db.models.watch import Watch
from strata_api.db.session import get_engine
from strata_api.watch_events import address_for as _address_for
from strata_api.watch_events import derive_events

router = APIRouter(prefix="/watchlist", tags=["watchlist"])


class WatchCreate(BaseModel):
    egid: int
    ewid: int | None = None


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
        events = derive_events(s, watched_egids, cutoff)

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
