"""Export buildings with active listings to a GeoJSON FeatureCollection.

Each Feature carries: egid, listing_count, cheapest_rent.
Only buildings with at least one active listing and valid coordinates are included.

Usage:
    python -m strata_api.scripts.export_listings_geojson > listings.geojson
"""
from __future__ import annotations

import json
import sys
from typing import Any

from sqlalchemy import Engine, func, select
from sqlalchemy.orm import Session

from strata_api.db.models.building import Building
from strata_api.db.models.listing import Listing, ListingUnitMatch


def export_listings_geojson(engine: Engine) -> dict[str, Any]:
    """Return a GeoJSON FeatureCollection of buildings with active listings."""
    with Session(engine) as s:
        # Aggregate active listings per building
        stmt = (
            select(
                ListingUnitMatch.egid,
                func.count(Listing.id.distinct()).label("listing_count"),
                func.min(
                    func.coalesce(Listing.rent_gross, Listing.rent_net)
                ).label("cheapest_rent"),
            )
            .join(Listing, Listing.id == ListingUnitMatch.listing_id)
            .where(Listing.is_active.is_(True))
            .group_by(ListingUnitMatch.egid)
        )
        rows = s.execute(stmt).all()

        # Build lookup: egid → (listing_count, cheapest_rent)
        listing_data = {row.egid: (row.listing_count, row.cheapest_rent) for row in rows}

        if not listing_data:
            return {"type": "FeatureCollection", "features": []}

        # Fetch building coordinates for matched EGIDs
        buildings = s.execute(
            select(Building).where(
                Building.egid.in_(listing_data.keys()),
                Building.lat.is_not(None),
                Building.lon.is_not(None),
            )
        ).scalars().all()

    features = [
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [round(b.lon, 5), round(b.lat, 5)],
            },
            "properties": {
                "egid": b.egid,
                "listing_count": listing_data[b.egid][0],
                "cheapest_rent": listing_data[b.egid][1],
            },
        }
        for b in buildings
    ]

    return {"type": "FeatureCollection", "features": features}


def main() -> None:
    from strata_api.db.session import get_engine

    engine = get_engine()
    collection = export_listings_geojson(engine)
    json.dump(collection, sys.stdout, separators=(",", ":"))
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
