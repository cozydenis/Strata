"""Listing endpoints — active rental listings matched to GWR buildings."""
from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from strata_api.db.models.listing import Listing, ListingUnitMatch
from strata_api.db.session import get_engine

router = APIRouter(prefix="/registry", tags=["listings"])


def _listing_dict(listing: Listing) -> dict:
    return {
        "id": listing.id,
        "source": listing.source,
        "source_id": listing.source_id,
        "rent_net": listing.rent_net,
        "rent_gross": listing.rent_gross,
        "rooms": listing.rooms,
        "area_m2": listing.area_m2,
        "street": listing.street,
        "house_number": listing.house_number,
        "plz": listing.plz,
        "city": listing.city,
        "source_url": listing.source_url,
        "first_seen": listing.first_seen.isoformat() if listing.first_seen else None,
        "last_seen": listing.last_seen.isoformat() if listing.last_seen else None,
        "description": listing.description,
        "images": [
            {
                "id": img.id,
                "url": img.url,
                "caption": img.caption,
                "ordering": img.ordering,
                "image_type": img.image_type,
            }
            for img in sorted(listing.images, key=lambda x: x.ordering)
        ],
        "documents": [
            {
                "id": doc.id,
                "url": doc.url,
                "caption": doc.caption,
                "doc_type": doc.doc_type,
            }
            for doc in listing.documents
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
    return {"egid": egid, "listings": [_listing_dict(listing) for listing in listings]}
