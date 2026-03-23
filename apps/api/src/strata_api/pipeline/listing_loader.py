"""Listing loader — upserts rental listings from connectors into the database.

Responsibilities:
  - Insert new listings (first_seen = last_seen = now)
  - Update existing listings (last_seen = now, detect field changes)
  - Log field changes to listing_history
  - Deactivate listings no longer seen from a given source
"""
from __future__ import annotations

import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from strata_api.db.models.listing import Listing, ListingHistory

# Fields tracked for change detection (logged to listing_history)
_TRACKED_FIELDS = (
    "rent_net",
    "rent_gross",
    "rent_charges",
    "rooms",
    "area_m2",
    "status",
    "offer_type",
    "street",
    "house_number",
    "plz",
    "city",
    "lat",
    "lng",
    "source_url",
    # is_active is managed by the loader (deactivate_missing), not tracked here
)


def _listing_to_dict(listing_obj: Any) -> dict:
    """Convert a Pydantic listing model to a flat dict of DB columns."""
    # Both FlatfoxListing and HomogateListing have these fields
    return {
        "source": listing_obj.source,
        "source_id": listing_obj.source_id,
        "rent_net": listing_obj.rent_net,
        "rent_gross": listing_obj.rent_gross,
        "rent_charges": listing_obj.rent_charges,
        "rooms": listing_obj.rooms,
        "area_m2": listing_obj.area_m2,
        "address_raw": listing_obj.address_raw,
        "street": listing_obj.street,
        "house_number": listing_obj.house_number,
        "plz": listing_obj.plz,
        "city": listing_obj.city,
        "lat": listing_obj.lat,
        "lng": listing_obj.lng,
        "object_type": listing_obj.object_type,
        "offer_type": listing_obj.offer_type,
        "status": listing_obj.status,
        "source_url": listing_obj.source_url,
        "description": getattr(listing_obj, "description", None),
    }


def _detect_changes(
    existing: Listing,
    new_data: dict,
    now: datetime.datetime,
) -> list[ListingHistory]:
    """Return ListingHistory rows for any changed tracked fields."""
    changes: list[ListingHistory] = []
    for field in _TRACKED_FIELDS:
        old_val = getattr(existing, field, None)
        new_val = new_data.get(field)
        if old_val != new_val:
            changes.append(
                ListingHistory(
                    listing_id=existing.id,
                    field_changed=field,
                    old_value=str(old_val) if old_val is not None else None,
                    new_value=str(new_val) if new_val is not None else None,
                    changed_at=now,
                )
            )
    return changes


def upsert_listings(
    db: Session,
    listings: list[Any],
) -> dict[str, int]:
    """Upsert a list of Pydantic listing objects into the database.

    Returns stats: {inserted, updated, unchanged}
    """
    stats = {"inserted": 0, "updated": 0, "unchanged": 0}
    now = datetime.datetime.utcnow()

    for listing_obj in listings:
        data = _listing_to_dict(listing_obj)
        source = data["source"]
        source_id = data["source_id"]

        existing = db.execute(
            select(Listing).where(
                Listing.source == source,
                Listing.source_id == source_id,
            )
        ).scalar_one_or_none()

        if existing is None:
            # Insert new listing
            db_row = Listing(
                **{k: v for k, v in data.items()},
                first_seen=now,
                last_seen=now,
                is_active=True,
            )
            db.add(db_row)
            db.flush()  # get id assigned
            stats["inserted"] += 1
        else:
            # Detect changes
            changes = _detect_changes(existing, data, now)

            # Update tracking fields regardless
            existing.last_seen = now

            if changes:
                # Apply new field values
                for field in _TRACKED_FIELDS:
                    if field in data:
                        setattr(existing, field, data[field])
                # Also update non-tracked fields that might have changed
                for field in ("address_raw", "object_type"):
                    if field in data:
                        setattr(existing, field, data[field])
                db.add_all(changes)
                stats["updated"] += 1
            else:
                # Update all fields to latest values (e.g. lat/lng might have refreshed)
                for field in ("address_raw", "lat", "lng", "object_type", "source_url"):
                    if field in data:
                        setattr(existing, field, data[field])
                stats["unchanged"] += 1

    return stats


def deactivate_missing(
    db: Session,
    source: str,
    seen_source_ids: set[str],
) -> int:
    """Mark as inactive all listings from *source* not in *seen_source_ids*.

    Returns count of deactivated listings.
    """
    stmt = select(Listing).where(
        Listing.source == source,
        Listing.is_active.is_(True),
    )
    active_listings = db.execute(stmt).scalars().all()

    deactivated = 0
    now = datetime.datetime.utcnow()
    for listing in active_listings:
        if listing.source_id not in seen_source_ids:
            listing.is_active = False
            deactivated += 1

    return deactivated
