"""Export all geolocated buildings to a GeoJSON FeatureCollection.

Each Feature carries only the 5 properties needed by the map renderer:
  egid, gbauj, gkat, gastw, ganzwhg

Buildings with null lat or lon are excluded.

Usage:
    python -m strata_api.scripts.export_buildings_geojson > buildings.geojson
    DATABASE_URL=sqlite:///./local.db python -m strata_api.scripts.export_buildings_geojson
"""
from __future__ import annotations

import json
import sys
from typing import Any

from sqlalchemy import Engine, select

from strata_api.db.models.building import Building
from strata_api.db.session import get_engine


def export_buildings_geojson(engine: Engine) -> dict[str, Any]:
    """Return a GeoJSON FeatureCollection of all geolocated buildings."""
    from sqlalchemy.orm import Session

    with Session(engine) as s:
        rows = s.execute(
            select(Building).where(
                Building.lat.is_not(None),
                Building.lon.is_not(None),
            )
        ).scalars().all()

    features = [
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                # 5 decimal places ≈ 1 m precision — sufficient for building level
                "coordinates": [round(row.lon, 5), round(row.lat, 5)],
            },
            "properties": {
                "egid": row.egid,
                "gbauj": row.gbauj,
                "gkat": row.gkat,
                "gastw": row.gastw,
                "ganzwhg": row.ganzwhg,
            },
        }
        for row in rows
    ]

    return {"type": "FeatureCollection", "features": features}


def main() -> None:
    engine = get_engine()
    collection = export_buildings_geojson(engine)
    json.dump(collection, sys.stdout, separators=(",", ":"))
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
