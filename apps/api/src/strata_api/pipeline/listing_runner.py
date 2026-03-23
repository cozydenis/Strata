"""Listing pipeline runner — orchestrates fetch, upsert, deactivation, and media download."""
from __future__ import annotations

from pathlib import Path

from sqlalchemy import exists, select
from sqlalchemy.orm import Session

from strata_api.db.models.listing import Listing, ListingImage
from strata_api.pipeline.connectors.flatfox import FlatfoxConnector, FlatfoxListing
from strata_api.pipeline.listing_loader import deactivate_missing, upsert_listings
from strata_api.pipeline.media_downloader import save_listing_media, scrape_listing_media

# Default local storage for downloaded media
_DEFAULT_MEDIA_DIR = Path(__file__).parent.parent.parent.parent / "data" / "images"


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

    # ── Media (photos + floor plans) ─────────────────────────────────────────
    media_stats = _download_media_for_new_listings(db, listings, media_dir)
    source_stats["photos_saved"] = media_stats["photos_saved"]
    source_stats["floorplans_saved"] = media_stats["floorplans_saved"]
    source_stats["documents_saved"] = media_stats["documents_saved"]

    stats["flatfox"] = source_stats

    return stats


def _download_media_for_new_listings(
    db: Session,
    listings: list[FlatfoxListing],
    media_dir: Path,
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
        counts = save_listing_media(db, listing_id, media, media_dir)
        totals["photos_saved"] += counts["photos_saved"]
        totals["floorplans_saved"] += counts["floorplans_saved"]
        totals["documents_saved"] += counts["documents_saved"]

    return totals
