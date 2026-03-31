"""Listing pipeline runner — orchestrates fetch, upsert, deactivation, and media download.

Usage:
    python -m strata_api.pipeline.listing_runner
"""
from __future__ import annotations

from pathlib import Path

from sqlalchemy import exists, select
from sqlalchemy.orm import Session

from strata_api.config import settings
from strata_api.db.models.listing import Listing, ListingImage, ListingUnitMatch
from strata_api.pipeline.address_matcher import match_listing
from strata_api.pipeline.connectors.flatfox import FlatfoxConnector, FlatfoxListing
from strata_api.pipeline.listing_loader import deactivate_missing, upsert_listings
from strata_api.pipeline.media_downloader import save_listing_media, scrape_listing_media
from strata_api.pipeline.storage import SupabaseStorageUploader

# Default local storage for downloaded media
_DEFAULT_MEDIA_DIR = Path(__file__).parent.parent.parent.parent / "data" / "images"


def _make_uploader() -> SupabaseStorageUploader | None:
    """Return a Supabase Storage uploader if credentials are configured."""
    if settings.supabase_url and settings.supabase_service_key:
        return SupabaseStorageUploader(settings.supabase_url, settings.supabase_service_key)
    return None


async def run_listing_pipeline(
    db: Session,
    media_dir: Path = _DEFAULT_MEDIA_DIR,
) -> dict[str, dict[str, int]]:
    """Run the full listing ingestion pipeline for all sources.

    Returns stats per source: {source: {inserted, updated, unchanged, deactivated,
                                         photos_saved, floorplans_saved, documents_saved}}
    """
    stats: dict[str, dict[str, int]] = {}

    # ── Flatfox ───────────────────────────────────────────────────────────────
    connector = FlatfoxConnector()
    listings = await connector.fetch_all_zurich()

    source_stats = upsert_listings(db, listings)
    seen_ids = {lst.source_id for lst in listings}
    deactivated = deactivate_missing(db, source="flatfox", seen_source_ids=seen_ids)
    source_stats["deactivated"] = deactivated

    # ── Address matching (listings → GWR buildings/units) ────────────────────
    match_stats = _match_unmatched_listings(db)
    source_stats["matched"] = match_stats["matched"]
    source_stats["unmatched"] = match_stats["unmatched"]

    # ── Media (photos + floor plans) ─────────────────────────────────────────
    uploader = _make_uploader()
    media_stats = _download_media_for_new_listings(db, listings, media_dir, uploader)
    source_stats["photos_saved"] = media_stats["photos_saved"]
    source_stats["floorplans_saved"] = media_stats["floorplans_saved"]
    source_stats["documents_saved"] = media_stats["documents_saved"]

    stats["flatfox"] = source_stats

    return stats


def _match_unmatched_listings(db: Session) -> dict[str, int]:
    """Run address matching for active listings that have no GWR match yet.

    Returns {matched, unmatched} counts.
    """
    unmatched_rows = db.execute(
        select(Listing).where(
            Listing.is_active.is_(True),
            ~exists().where(ListingUnitMatch.listing_id == Listing.id),
        )
    ).scalars().all()

    matched = 0
    unmatched = 0
    for listing in unmatched_rows:
        results = match_listing(
            db,
            street=listing.street,
            house_number=listing.house_number,
            plz=listing.plz,
            rooms=listing.rooms,
            area_m2=listing.area_m2,
            lat=listing.lat,
            lng=listing.lng,
        )
        if results:
            for result in results:
                db.add(ListingUnitMatch(
                    listing_id=listing.id,
                    egid=result.egid,
                    ewid=result.ewid,
                    match_confidence=result.confidence,
                    matched_egid=result.egid,
                ))
            matched += 1
        else:
            unmatched += 1

    return {"matched": matched, "unmatched": unmatched}


def _download_media_for_new_listings(
    db: Session,
    listings: list[FlatfoxListing],
    media_dir: Path,
    uploader: SupabaseStorageUploader | None = None,
) -> dict[str, int]:
    """Download photos and floor plans for listings that have no images yet."""
    # Find DB listings (from this batch) that have no images yet
    source_ids_in_batch = [lst.source_id for lst in listings]
    rows_without_media = db.execute(
        select(Listing.source_id, Listing.id).where(
            Listing.source == "flatfox",
            Listing.source_id.in_(source_ids_in_batch),
            ~exists().where(ListingImage.listing_id == Listing.id),
        )
    ).all()

    needs_media = {row.source_id: row.id for row in rows_without_media}
    if not needs_media:
        return {"photos_saved": 0, "floorplans_saved": 0, "documents_saved": 0}

    # Build lookup: source_id → FlatfoxListing (for slug)
    listing_by_source_id = {lst.source_id: lst for lst in listings}

    totals = {"photos_saved": 0, "floorplans_saved": 0, "documents_saved": 0}
    for source_id, listing_id in needs_media.items():
        ff = listing_by_source_id.get(source_id)
        if ff is None or not ff.slug:
            continue
        try:
            pk = int(ff.source_id)
        except ValueError:
            continue
        media = scrape_listing_media(ff.slug, pk)
        counts = save_listing_media(db, listing_id, media, media_dir, uploader)
        totals["photos_saved"] += counts["photos_saved"]
        totals["floorplans_saved"] += counts["floorplans_saved"]
        totals["documents_saved"] += counts["documents_saved"]

    return totals


if __name__ == "__main__":
    import asyncio
    import sys

    from strata_api.db.session import get_session

    async def _main() -> int:
        with get_session() as db:
            stats = await run_listing_pipeline(db)
        for source, counts in stats.items():
            print(f"[listing] {source}: {counts}")
        return 0

    sys.exit(asyncio.run(_main()))
