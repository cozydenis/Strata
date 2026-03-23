"""Listing endpoints — active rental listings matched to GWR buildings."""
from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from strata_api.db.models.listing import Listing, ListingUnitMatch
from strata_api.db.session import get_engine

router = APIRouter(prefix="/registry", tags=["listings"])


def _listing_dict(l: Listing) -> dict:
    return {
        "id": l.id,
        "source": l.source,
        "source_id": l.source_id,
        "rent_net": l.rent_net,
        "rent_gross": l.rent_gross,
        "rooms": l.rooms,
        "area_m2": l.area_m2,
        "street": l.street,
        "house_number": l.house_number,
        "plz": l.plz,
        "city": l.city,
        "source_url": l.source_url,
        "first_seen": l.first_seen.isoformat() if l.first_seen else None,
        "last_seen": l.last_seen.isoformat() if l.last_seen else None,
        "description": l.description,
        "images": [
            {
                "id": img.id,
                "url": img.url,
                "caption": img.caption,
                "ordering": img.ordering,
                "image_type": img.image_type,
            }
            for img in sorted(l.images, key=lambda x: x.ordering)
        ],
        "documents": [
            {
                "id": doc.id,
                "url": doc.url,
                "caption": doc.caption,
                "doc_type": doc.doc_type,
            }
            for doc in l.documents
        ],
    }


@router.get("/buildings/{egid}/listings")
def get_building_listings(egid: int) -> dict:
    """Return active listings matched to a building by EGID."""
    engine = get_engine()
    with Session(engine) as s:
        stmt = (
            select(Listing)
            .join(ListingUnitMatch, ListingUnitMatch.listing_id == Listing.id)
            .where(ListingUnitMatch.egid == egid, Listing.is_active.is_(True))
            .options(selectinload(Listing.images), selectinload(Listing.documents))
            .distinct()
        )
        listings = s.execute(stmt).scalars().all()
    return {"egid": egid, "listings": [_listing_dict(l) for l in listings]}
