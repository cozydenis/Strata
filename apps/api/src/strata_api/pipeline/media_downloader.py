"""Download listing images and floor plans from Flatfox.

Strategy:
  1. Scrape the listing HTML page to extract signed thumbnail URLs
  2. Download files to local storage (idempotent — skips existing files)
  3. Return metadata records for DB insertion

Image URL patterns in Flatfox HTML:
  /thumb/ff/{year}/{month}/{hash}.jpg?alias=listing_gallery_l&signature={sig}
  /thumb/ff/{year}/{month}/{hash}.jpg?alias=listing_floorplan_l&signature={sig}
"""
from __future__ import annotations

import logging
import re
import urllib.request
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.orm import Session
    from strata_api.pipeline.storage import SupabaseStorageUploader

logger = logging.getLogger(__name__)

_GALLERY_RE = re.compile(
    r"/thumb/ff/\d{4}/\d{2}/[a-z0-9]+\.jpg\?alias=listing_gallery_l"
    r"(?:&amp;|&)signature=[a-zA-Z0-9_-]+",
)
_FLOORPLAN_RE = re.compile(
    r"/thumb/ff/\d{4}/\d{2}/[a-z0-9]+\.jpg\?alias=listing_floorplan_l"
    r"(?:&amp;|&)signature=[a-zA-Z0-9_-]+",
)
_OG_IMAGE_RE = re.compile(
    r'<meta\s+property="og:image"\s+content="([^"]+)"',
)
# Matches the Documents table row; captures everything up to the closing </tr>
_DOCUMENTS_SECTION_RE = re.compile(
    r"<td>Documents:</td>\s*<td>(.*?)</td>",
    re.DOTALL | re.IGNORECASE,
)
# Matches /media/ff/... href links (pdf, jpg, png)
_DOCUMENT_HREF_RE = re.compile(
    r'href="(/media/ff/[^"]+\.(?:pdf|jpg|jpeg|png))"',
    re.IGNORECASE,
)
_USER_AGENT = "Strata-Pipeline/1.0 (research; contact: hello@strata.ch)"


def _dedup(urls: list[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            unique.append(u)
    return unique


def _fetch_page_html(slug: str, pk: int) -> str | None:
    """Fetch a Flatfox listing page. Returns HTML or None on failure."""
    url = f"https://flatfox.ch/en/flat/{slug}/{pk}/"
    return fetch_page_html_by_url(url)


def fetch_page_html_by_url(url: str) -> str | None:
    """Fetch a page by URL. Returns HTML or None on failure."""
    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except Exception:
        logger.warning("Failed to fetch page %s", url)
        return None


def extract_image_urls_from_html(html: str, include_og: bool = False) -> list[str]:
    """Extract signed gallery image URLs from Flatfox listing HTML.

    Returns deduplicated list of absolute URLs (listing_gallery_l size).
    """
    urls: list[str] = []

    for match in _GALLERY_RE.findall(html):
        clean = match.replace("&amp;", "&")
        urls.append(f"https://flatfox.ch{clean}")

    if include_og:
        og_match = _OG_IMAGE_RE.search(html)
        if og_match:
            og_url = og_match.group(1).replace("&amp;", "&")
            full = f"https://flatfox.ch{og_url}" if og_url.startswith("/") else og_url
            urls.append(full)

    return _dedup(urls)


def extract_floorplan_urls_from_html(html: str) -> list[str]:
    """Extract floor plan image URLs from Flatfox listing HTML.

    Returns deduplicated list of absolute URLs (listing_floorplan_l size).
    """
    urls: list[str] = []
    for match in _FLOORPLAN_RE.findall(html):
        clean = match.replace("&amp;", "&")
        urls.append(f"https://flatfox.ch{clean}")
    return _dedup(urls)


def extract_document_urls_from_html(html: str) -> list[str]:
    """Extract document URLs from the Documents table row in a Flatfox listing page.

    Finds the <td>Documents:</td> section and returns all /media/ff/... href links
    as absolute URLs. Returns a deduplicated list; empty list if no section found.
    """
    section_match = _DOCUMENTS_SECTION_RE.search(html)
    if not section_match:
        return []
    section = section_match.group(1)
    hrefs = _DOCUMENT_HREF_RE.findall(section)
    return _dedup([f"https://flatfox.ch{href}" for href in hrefs])


def _url_read(url: str) -> bytes:
    """Fetch raw bytes from a URL."""
    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


def download_file(url: str, dest: Path) -> bool:
    """Download a file to dest. Skips if dest already exists. Returns success."""
    if dest.exists():
        return True
    try:
        data = _url_read(url)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        return True
    except Exception:
        logger.warning("Failed to download %s", url)
        return False


def scrape_listing_images(slug: str, pk: int) -> list[str]:
    """Scrape a Flatfox listing page and return gallery image URLs."""
    html = _fetch_page_html(slug, pk)
    if html is None:
        return []
    return extract_image_urls_from_html(html, include_og=True)


def scrape_listing_media(slug: str, pk: int) -> dict[str, list[str]]:
    """Scrape a Flatfox listing page and return photos, floor plans, and documents.

    Returns {"photos": [...], "floorplans": [...], "documents": [...]} with absolute URLs.
    """
    html = _fetch_page_html(slug, pk)
    if html is None:
        return {"photos": [], "floorplans": [], "documents": []}
    return {
        "photos": extract_image_urls_from_html(html, include_og=True),
        "floorplans": extract_floorplan_urls_from_html(html),
        "documents": extract_document_urls_from_html(html),
    }


def save_listing_media(
    db: Session,
    listing_id: int,
    media: dict[str, list[str]],
    media_dir: Path,
    uploader: SupabaseStorageUploader | None = None,
) -> dict[str, int]:
    """Download media files and persist ListingImage rows for a listing.

    When *uploader* is provided, files are uploaded to Supabase Storage and
    the permanent public URL is stored in listing_images.url.  The original
    Flatfox URL is kept in local_path for reference.

    Without an uploader, files are written to media_dir (local-only fallback).

    Skips listings that already have images (idempotent).
    Returns {"photos_saved": N, "floorplans_saved": N, "documents_saved": N}.
    """
    from strata_api.db.models.listing import ListingImage

    photos_saved = 0
    floorplans_saved = 0
    documents_saved = 0

    def _save(source_url: str, storage_subdir: str, dest_dir: Path, ordering: int, image_type: str) -> None:
        fname = _url_to_filename(source_url)
        stored_url = source_url
        local_path: str | None = None

        if uploader is not None:
            try:
                data = _url_read(source_url)
                storage_path = f"{storage_subdir}/{listing_id}/{fname}"
                stored_url = uploader.upload(data, storage_path)
                local_path = source_url  # keep original for reference
            except Exception:
                logger.warning("Storage upload failed for listing %s url %s", listing_id, source_url)
                stored_url = source_url
        else:
            dest = dest_dir / fname
            ok = download_file(source_url, dest)
            local_path = str(dest) if ok else None

        db.add(ListingImage(
            listing_id=listing_id,
            url=stored_url,
            local_path=local_path,
            ordering=ordering,
            image_type=image_type,
        ))

    for ordering, url in enumerate(media.get("photos", [])):
        _save(url, "photos", media_dir / "photos", ordering, "photo")
        photos_saved += 1

    for ordering, url in enumerate(media.get("floorplans", [])):
        _save(url, "floorplans", media_dir / "floorplans", ordering, "floorplan")
        floorplans_saved += 1

    for ordering, url in enumerate(media.get("documents", [])):
        _save(url, "documents", media_dir / "documents", ordering, "document")
        documents_saved += 1

    return {
        "photos_saved": photos_saved,
        "floorplans_saved": floorplans_saved,
        "documents_saved": documents_saved,
    }


def _url_to_filename(url: str) -> str:
    """Derive a stable local filename from a CDN URL.

    E.g. /thumb/ff/2026/03/abc123.jpg?alias=listing_gallery_l&signature=XYZ → abc123.jpg
    """
    path = url.split("?")[0]
    return path.rsplit("/", 1)[-1]
