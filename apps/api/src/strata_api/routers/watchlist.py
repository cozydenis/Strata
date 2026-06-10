"""Watchlist endpoints — authenticated users watch buildings or specific units.

The wedge feature of Layer 2: "I want this one. Watch it. Tell me when it
moves." All endpoints require a Supabase JWT (see strata_api.auth).
"""
from __future__ import annotations

import datetime

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from strata_api.auth import get_current_user
from strata_api.db.models.building import Building
from strata_api.db.models.entrance import Entrance
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
