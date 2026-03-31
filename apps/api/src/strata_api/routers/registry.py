"""Read endpoints for the GWR unit registry."""
from __future__ import annotations

import json
from typing import Iterator

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from strata_api.db.models.building import Building
from strata_api.db.models.entrance import Entrance
from strata_api.db.models.unit import Unit
from strata_api.db.session import get_engine

router = APIRouter(prefix="/registry", tags=["registry"])


def _building_dict(b: Building) -> dict:
    return {
        "egid": b.egid, "gstat": b.gstat, "gkat": b.gkat, "gklas": b.gklas,
        "gbauj": b.gbauj, "gabbj": b.gabbj, "garea": b.garea,
        "gastw": b.gastw, "ganzwhg": b.ganzwhg,
        "lat": b.lat, "lon": b.lon,
        "municipality": b.municipality, "municipality_code": b.municipality_code,
        "canton": b.canton, "data_source": b.data_source,
    }


def _unit_dict(u: Unit) -> dict:
    return {
        "egid": u.egid, "ewid": u.ewid, "edid": u.edid,
        "wstwk": u.wstwk, "wstwklang": u.wstwklang,
        "wazim": u.wazim, "warea": u.warea, "wkche": u.wkche,
        "wstat": u.wstat, "wbauj": u.wbauj, "wabbj": u.wabbj,
        "dplz4": u.dplz4, "dplzname": u.dplzname,
        "strname": u.strname, "deinr": u.deinr,
        "lat": u.lat, "lon": u.lon, "data_source": u.data_source,
    }


@router.get("/buildings/geojson")
def buildings_geojson() -> StreamingResponse:
    """Stream all geolocated buildings as a GeoJSON FeatureCollection.

    Cached for 1 hour — suitable as a MapLibre GeoJSON source.
    """
    engine = get_engine()

    def _generate() -> Iterator[str]:
        yield '{"type":"FeatureCollection","features":['
        with Session(engine) as s:
            rows = s.execute(
                select(Building).where(
                    Building.lat.is_not(None),
                    Building.lon.is_not(None),
                )
            ).scalars().all()
        first = True
        for row in rows:
            feature = json.dumps(
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [round(row.lon, 5), round(row.lat, 5)]},
                    "properties": {
                        "egid": row.egid,
                        "gbauj": row.gbauj,
                        "gkat": row.gkat,
                        "gastw": row.gastw,
                        "ganzwhg": row.ganzwhg,
                    },
                },
                separators=(",", ":"),
            )
            if not first:
                yield ","
            yield feature
            first = False
        yield "]}"

    return StreamingResponse(
        _generate(),
        media_type="application/geo+json",
        headers={"Cache-Control": "public, max-age=3600"},
    )


@router.get("/buildings")
def list_buildings(
    data_source: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
) -> dict:
    engine = get_engine()
    with Session(engine) as s:
        q = select(Building)
        count_q = select(func.count()).select_from(Building)
        if data_source:
            q = q.where(Building.data_source == data_source)
            count_q = count_q.where(Building.data_source == data_source)
        total = s.execute(count_q).scalar_one()
        items = s.execute(q.offset(offset).limit(limit)).scalars().all()
    return {"total": total, "items": [_building_dict(b) for b in items]}


@router.get("/buildings/{egid}")
def get_building(egid: int) -> dict:
    engine = get_engine()
    with Session(engine) as s:
        b = s.get(Building, egid)
    if b is None:
        raise HTTPException(status_code=404, detail=f"Building {egid} not found.")
    return _building_dict(b)


@router.get("/buildings/{egid}/summary")
def get_building_summary(egid: int) -> dict:
    """Return building fields + first entrance address — used by map popups."""
    engine = get_engine()
    with Session(engine) as s:
        b = s.get(Building, egid)
        if b is None:
            raise HTTPException(status_code=404, detail=f"Building {egid} not found.")
        entrance = s.execute(
            select(Entrance)
            .where(Entrance.egid == egid)
            .order_by(Entrance.edid)
            .limit(1)
        ).scalar_one_or_none()
    return {
        "egid": b.egid,
        "gbauj": b.gbauj,
        "gkat": b.gkat,
        "gastw": b.gastw,
        "ganzwhg": b.ganzwhg,
        "lat": b.lat,
        "lon": b.lon,
        "strname": entrance.strname if entrance else None,
        "deinr": entrance.deinr if entrance else None,
        "dplz4": entrance.dplz4 if entrance else None,
        "dplzname": entrance.dplzname if entrance else None,
    }


@router.get("/buildings/{egid}/units")
def list_units_for_building(
    egid: int,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
) -> dict:
    engine = get_engine()
    with Session(engine) as s:
        q = select(Unit).where(Unit.egid == egid)
        total = s.execute(select(func.count()).select_from(Unit).where(Unit.egid == egid)).scalar_one()
        items = s.execute(q.offset(offset).limit(limit)).scalars().all()
    return {"total": total, "items": [_unit_dict(u) for u in items]}


@router.get("/buildings/{egid}/units/{ewid}")
def get_unit(egid: int, ewid: int) -> dict:
    engine = get_engine()
    with Session(engine) as s:
        u = s.get(Unit, {"egid": egid, "ewid": ewid})
    if u is None:
        raise HTTPException(status_code=404, detail=f"Unit ({egid}, {ewid}) not found.")
    return _unit_dict(u)
