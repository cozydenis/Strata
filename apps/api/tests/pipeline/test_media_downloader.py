"""Tests for the listing media downloader."""
from pathlib import Path
from unittest.mock import patch

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from strata_api.db.base import Base
from strata_api.db.models.listing import Listing, ListingImage
from strata_api.pipeline.media_downloader import (
    _url_to_filename,
    download_file,
    extract_document_urls_from_html,
    extract_floorplan_urls_from_html,
    extract_image_urls_from_html,
    save_listing_media,
    scrape_listing_images,
    scrape_listing_media,
)


@pytest.fixture(scope="module")
def engine():
    eng = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(eng)
    yield eng
    eng.dispose()


@pytest.fixture
def db(engine):
    with Session(engine) as session:
        yield session
        session.rollback()


@pytest.fixture
def listing_id(db):
    """Insert a minimal Listing row and return its id."""
    import datetime
    row = Listing(
        source="flatfox",
        source_id="test-media-99",
        first_seen=datetime.datetime.utcnow(),
        last_seen=datetime.datetime.utcnow(),
        is_active=True,
    )
    db.add(row)
    db.flush()
    return row.id


# ── extract_image_urls_from_html ─────────────────────────────────────────────


class TestExtractImageUrls:
    def test_extracts_gallery_large_urls(self):
        html = '''
        <img src="/thumb/ff/2026/02/abc123.jpg?alias=listing_gallery_l&amp;signature=XYZ"/>
        <img src="/thumb/ff/2026/02/def456.jpg?alias=listing_gallery_l&amp;signature=ABC"/>
        '''
        urls = extract_image_urls_from_html(html)
        assert len(urls) == 2
        assert all("listing_gallery_l" in u for u in urls)

    def test_deduplicates_urls(self):
        html = '''
        <img src="/thumb/ff/2026/02/abc123.jpg?alias=listing_gallery_l&amp;signature=XYZ"/>
        <img src="/thumb/ff/2026/02/abc123.jpg?alias=listing_gallery_l&amp;signature=XYZ"/>
        '''
        urls = extract_image_urls_from_html(html)
        assert len(urls) == 1

    def test_returns_absolute_urls(self):
        html = '<img src="/thumb/ff/2026/02/abc.jpg?alias=listing_gallery_l&amp;signature=X"/>'
        urls = extract_image_urls_from_html(html)
        assert all(u.startswith("https://flatfox.ch/") for u in urls)

    def test_returns_empty_for_no_images(self):
        urls = extract_image_urls_from_html("<html><body>No images</body></html>")
        assert urls == []

    def test_cleans_html_entities(self):
        html = '<img src="/thumb/ff/2026/02/abc.jpg?alias=listing_gallery_l&amp;signature=X"/>'
        urls = extract_image_urls_from_html(html)
        assert all("&amp;" not in u for u in urls)

    def test_extracts_og_image_as_cover(self):
        html = (
            '<meta property="og:image"'
            ' content="/thumb/ff/2026/02/cover.jpg?alias=facebook_l&amp;signature=Y"/>'
        )
        urls = extract_image_urls_from_html(html, include_og=True)
        assert any("cover" in u for u in urls)


# ── download_file ────────────────────────────────────────────────────────────


class TestDownloadFile:
    def test_downloads_to_path(self, tmp_path):
        dest = tmp_path / "test.jpg"
        mock_data = b"\xff\xd8\xff\xe0" + b"\x00" * 100  # fake JPEG header

        with patch("strata_api.pipeline.media_downloader._url_read") as mock_read:
            mock_read.return_value = mock_data
            ok = download_file("https://example.com/img.jpg", dest)

        assert ok is True
        assert dest.exists()
        assert dest.read_bytes() == mock_data

    def test_skips_existing_file(self, tmp_path):
        dest = tmp_path / "existing.jpg"
        dest.write_bytes(b"already here")

        with patch("strata_api.pipeline.media_downloader._url_read") as mock_read:
            ok = download_file("https://example.com/img.jpg", dest)

        assert ok is True
        mock_read.assert_not_called()

    def test_returns_false_on_error(self, tmp_path):
        dest = tmp_path / "fail.jpg"

        with patch("strata_api.pipeline.media_downloader._url_read") as mock_read:
            mock_read.side_effect = Exception("network error")
            ok = download_file("https://example.com/img.jpg", dest)

        assert ok is False
        assert not dest.exists()

    def test_creates_parent_directories(self, tmp_path):
        dest = tmp_path / "sub" / "dir" / "img.jpg"

        with patch("strata_api.pipeline.media_downloader._url_read") as mock_read:
            mock_read.return_value = b"\xff\xd8" + b"\x00" * 50
            download_file("https://example.com/img.jpg", dest)

        assert dest.exists()


# ── scrape_listing_images ────────────────────────────────────────────────────


class TestScrapeListingImages:
    def test_returns_image_urls_from_listing_page(self):
        html = (
            '<meta property="og:image"'
            ' content="/thumb/ff/2026/03/cover.jpg?alias=facebook_l&amp;signature=A"/>'
            '\n<img src="/thumb/ff/2026/03/img1.jpg?alias=listing_gallery_l&amp;signature=B"/>'
            '\n<img src="/thumb/ff/2026/03/img2.jpg?alias=listing_gallery_l&amp;signature=C"/>'
        )
        with patch("strata_api.pipeline.media_downloader._fetch_page_html") as mock_fetch:
            mock_fetch.return_value = html
            urls = scrape_listing_images("test-slug", 12345)

        assert len(urls) >= 2

    def test_returns_empty_on_fetch_failure(self):
        with patch("strata_api.pipeline.media_downloader._fetch_page_html") as mock_fetch:
            mock_fetch.return_value = None
            urls = scrape_listing_images("test-slug", 12345)

        assert urls == []


# ── extract_floorplan_urls_from_html ─────────────────────────────────────────


class TestExtractFloorplanUrls:
    def test_extracts_floorplan_urls(self):
        html = '''
        <img src="/thumb/ff/2026/03/fp1.jpg?alias=listing_floorplan_l&amp;signature=SIG1"/>
        <img src="/thumb/ff/2026/03/fp2.jpg?alias=listing_floorplan_l&amp;signature=SIG2"/>
        '''
        urls = extract_floorplan_urls_from_html(html)
        assert len(urls) == 2
        assert all("listing_floorplan_l" in u for u in urls)

    def test_returns_absolute_urls(self):
        html = '<img src="/thumb/ff/2026/03/fp.jpg?alias=listing_floorplan_l&amp;signature=X"/>'
        urls = extract_floorplan_urls_from_html(html)
        assert all(u.startswith("https://flatfox.ch/") for u in urls)

    def test_deduplicates_floorplan_urls(self):
        html = '''
        <img src="/thumb/ff/2026/03/fp1.jpg?alias=listing_floorplan_l&amp;signature=S"/>
        <img src="/thumb/ff/2026/03/fp1.jpg?alias=listing_floorplan_l&amp;signature=S"/>
        '''
        urls = extract_floorplan_urls_from_html(html)
        assert len(urls) == 1

    def test_cleans_html_entities(self):
        html = '<img src="/thumb/ff/2026/03/fp.jpg?alias=listing_floorplan_l&amp;signature=X"/>'
        urls = extract_floorplan_urls_from_html(html)
        assert all("&amp;" not in u for u in urls)

    def test_does_not_capture_gallery_urls(self):
        html = '<img src="/thumb/ff/2026/03/g.jpg?alias=listing_gallery_l&amp;signature=X"/>'
        urls = extract_floorplan_urls_from_html(html)
        assert urls == []

    def test_returns_empty_for_no_floorplans(self):
        urls = extract_floorplan_urls_from_html("<html><body>No floor plans</body></html>")
        assert urls == []


# ── scrape_listing_media ──────────────────────────────────────────────────────


class TestScrapeListingMedia:
    def test_returns_both_photos_and_floorplans(self):
        html = '''
        <img src="/thumb/ff/2026/03/img1.jpg?alias=listing_gallery_l&amp;signature=A"/>
        <img src="/thumb/ff/2026/03/fp1.jpg?alias=listing_floorplan_l&amp;signature=B"/>
        '''
        with patch("strata_api.pipeline.media_downloader._fetch_page_html") as mock_fetch:
            mock_fetch.return_value = html
            result = scrape_listing_media("test-slug", 99999)

        assert "photos" in result
        assert "floorplans" in result
        assert len(result["photos"]) == 1
        assert len(result["floorplans"]) == 1

    def test_returns_empty_dicts_on_fetch_failure(self):
        with patch("strata_api.pipeline.media_downloader._fetch_page_html") as mock_fetch:
            mock_fetch.return_value = None
            result = scrape_listing_media("test-slug", 99999)

        assert result == {"photos": [], "floorplans": [], "documents": []}

    def test_photos_and_floorplans_are_independent(self):
        """Photos list should not include floorplan URLs and vice versa."""
        html = '''
        <img src="/thumb/ff/2026/03/img1.jpg?alias=listing_gallery_l&amp;signature=A"/>
        <img src="/thumb/ff/2026/03/img2.jpg?alias=listing_gallery_l&amp;signature=B"/>
        <img src="/thumb/ff/2026/03/fp1.jpg?alias=listing_floorplan_l&amp;signature=C"/>
        '''
        with patch("strata_api.pipeline.media_downloader._fetch_page_html") as mock_fetch:
            mock_fetch.return_value = html
            result = scrape_listing_media("slug", 1)

        assert all("listing_gallery_l" in u for u in result["photos"])
        assert all("listing_floorplan_l" in u for u in result["floorplans"])

    def test_empty_photos_when_no_gallery_images(self):
        html = '<img src="/thumb/ff/2026/03/fp1.jpg?alias=listing_floorplan_l&amp;signature=C"/>'
        with patch("strata_api.pipeline.media_downloader._fetch_page_html") as mock_fetch:
            mock_fetch.return_value = html
            result = scrape_listing_media("slug", 1)

        assert result["photos"] == []
        assert len(result["floorplans"]) == 1


# ── _url_to_filename ──────────────────────────────────────────────────────────


class TestUrlToFilename:
    def test_extracts_filename_from_gallery_url(self):
        url = "https://flatfox.ch/thumb/ff/2026/03/abc123.jpg?alias=listing_gallery_l&signature=XYZ"
        assert _url_to_filename(url) == "abc123.jpg"

    def test_extracts_filename_from_floorplan_url(self):
        url = "https://flatfox.ch/thumb/ff/2026/03/fp9999.jpg?alias=listing_floorplan_l&signature=ABC"
        assert _url_to_filename(url) == "fp9999.jpg"

    def test_works_without_query_string(self):
        url = "https://example.com/images/photo.jpg"
        assert _url_to_filename(url) == "photo.jpg"


# ── save_listing_media ────────────────────────────────────────────────────────


class TestSaveListingMedia:
    def test_creates_photo_rows_in_db(self, db, listing_id, tmp_path):
        media = {
            "photos": [
                "https://flatfox.ch/thumb/ff/2026/03/img1.jpg?alias=listing_gallery_l&signature=A",
                "https://flatfox.ch/thumb/ff/2026/03/img2.jpg?alias=listing_gallery_l&signature=B",
            ],
            "floorplans": [],
        }
        with patch("strata_api.pipeline.media_downloader.download_file", return_value=True):
            counts = save_listing_media(db, listing_id, media, tmp_path)

        assert counts["photos_saved"] == 2
        assert counts["floorplans_saved"] == 0

        rows = db.execute(
            select(ListingImage).where(ListingImage.listing_id == listing_id)
        ).scalars().all()
        assert len(rows) == 2
        assert all(r.image_type == "photo" for r in rows)

    def test_creates_floorplan_rows_in_db(self, db, listing_id, tmp_path):
        media = {
            "photos": [],
            "floorplans": [
                "https://flatfox.ch/thumb/ff/2026/03/fp1.jpg?alias=listing_floorplan_l&signature=C",
            ],
        }
        with patch("strata_api.pipeline.media_downloader.download_file", return_value=True):
            counts = save_listing_media(db, listing_id, media, tmp_path)

        assert counts["floorplans_saved"] == 1

        rows = db.execute(
            select(ListingImage).where(
                ListingImage.listing_id == listing_id,
                ListingImage.image_type == "floorplan",
            )
        ).scalars().all()
        assert len(rows) == 1
        assert rows[0].image_type == "floorplan"

    def test_local_path_is_none_on_download_failure(self, db, listing_id, tmp_path):
        media = {
            "photos": [
                "https://flatfox.ch/thumb/ff/2026/03/bad.jpg?alias=listing_gallery_l&signature=X",
            ],
            "floorplans": [],
        }
        with patch("strata_api.pipeline.media_downloader.download_file", return_value=False):
            save_listing_media(db, listing_id, media, tmp_path)

        rows = db.execute(
            select(ListingImage).where(ListingImage.listing_id == listing_id)
        ).scalars().all()
        assert any(r.local_path is None for r in rows)

    def test_ordering_is_set_correctly(self, db, listing_id, tmp_path):
        media = {
            "photos": [
                "https://flatfox.ch/thumb/ff/2026/03/a.jpg?alias=listing_gallery_l&signature=A",
                "https://flatfox.ch/thumb/ff/2026/03/b.jpg?alias=listing_gallery_l&signature=B",
                "https://flatfox.ch/thumb/ff/2026/03/c.jpg?alias=listing_gallery_l&signature=C",
            ],
            "floorplans": [],
        }
        with patch("strata_api.pipeline.media_downloader.download_file", return_value=True):
            save_listing_media(db, listing_id, media, tmp_path)

        rows = db.execute(
            select(ListingImage)
            .where(ListingImage.listing_id == listing_id, ListingImage.image_type == "photo")
            .order_by(ListingImage.ordering)
        ).scalars().all()
        assert [r.ordering for r in rows] == [0, 1, 2]

    def test_returns_zero_counts_for_empty_media(self, db, listing_id, tmp_path):
        counts = save_listing_media(
            db, listing_id, {"photos": [], "floorplans": [], "documents": []}, tmp_path
        )
        assert counts == {"photos_saved": 0, "floorplans_saved": 0, "documents_saved": 0}

    def test_photo_stored_in_photos_subdir(self, db, listing_id, tmp_path):
        media = {
            "photos": [
                "https://flatfox.ch/thumb/ff/2026/03/x.jpg?alias=listing_gallery_l&signature=Z",
            ],
            "floorplans": [],
        }
        captured_paths: list[Path] = []

        def capture_download(url: str, dest: Path) -> bool:
            captured_paths.append(dest)
            return True

        with patch(
            "strata_api.pipeline.media_downloader.download_file",
            side_effect=capture_download,
        ):
            save_listing_media(db, listing_id, media, tmp_path)

        assert all("photos" in str(p) for p in captured_paths)

    def test_floorplan_stored_in_floorplans_subdir(self, db, listing_id, tmp_path):
        media = {
            "photos": [],
            "floorplans": [
                "https://flatfox.ch/thumb/ff/2026/03/fp.jpg?alias=listing_floorplan_l&signature=Z",
            ],
        }
        captured_paths: list[Path] = []

        def capture_download(url: str, dest: Path) -> bool:
            captured_paths.append(dest)
            return True

        with patch(
            "strata_api.pipeline.media_downloader.download_file",
            side_effect=capture_download,
        ):
            save_listing_media(db, listing_id, media, tmp_path)

        assert all("floorplans" in str(p) for p in captured_paths)


# ── extract_document_urls_from_html ──────────────────────────────────────────


_DOCUMENTS_HTML = """
<table>
  <tr>
    <td>Photos:</td>
    <td>
      <img src="/thumb/ff/2026/03/photo.jpg?alias=listing_gallery_l&amp;signature=P"/>
    </td>
  </tr>
  <tr>
    <td>Documents:</td>
    <td>
      <a href="/media/ff/2025/07/abc123/muel-whg-12.pdf"
         target="_blank" rel="nofollow">Grundriss</a><br />
      <a href="/media/ff/2024/07/xyz456/waffenplatz_typ1.jpg"
         target="_blank" rel="nofollow">Download</a><br />
    </td>
  </tr>
</table>
"""

_NO_DOCUMENTS_HTML = """
<table>
  <tr>
    <td>Photos:</td>
    <td>
      <img src="/thumb/ff/2026/03/photo.jpg?alias=listing_gallery_l&amp;signature=P"/>
    </td>
  </tr>
</table>
"""

_EMPTY_DOCUMENTS_HTML = """
<table>
  <tr>
    <td>Documents:</td>
    <td></td>
  </tr>
</table>
"""


class TestExtractDocumentUrls:
    def test_extracts_pdf_links_from_documents_section(self):
        urls = extract_document_urls_from_html(_DOCUMENTS_HTML)
        assert any(u.endswith(".pdf") for u in urls)

    def test_extracts_image_links_from_documents_section(self):
        urls = extract_document_urls_from_html(_DOCUMENTS_HTML)
        assert any(u.endswith(".jpg") for u in urls)

    def test_returns_absolute_urls_with_flatfox_prefix(self):
        urls = extract_document_urls_from_html(_DOCUMENTS_HTML)
        assert all(u.startswith("https://flatfox.ch/media/ff/") for u in urls)

    def test_returns_both_links_from_section(self):
        urls = extract_document_urls_from_html(_DOCUMENTS_HTML)
        assert len(urls) == 2

    def test_deduplicates_urls(self):
        html = """
        <tr>
          <td>Documents:</td>
          <td>
            <a href="/media/ff/2025/07/abc/plan.pdf" target="_blank">Grundriss</a><br />
            <a href="/media/ff/2025/07/abc/plan.pdf" target="_blank">Grundriss</a><br />
          </td>
        </tr>
        """
        urls = extract_document_urls_from_html(html)
        assert len(urls) == 1

    def test_returns_empty_list_when_no_documents_section(self):
        urls = extract_document_urls_from_html(_NO_DOCUMENTS_HTML)
        assert urls == []

    def test_returns_empty_list_when_documents_section_is_empty(self):
        urls = extract_document_urls_from_html(_EMPTY_DOCUMENTS_HTML)
        assert urls == []

    def test_does_not_capture_links_from_other_sections(self):
        html = """
        <tr>
          <td>Photos:</td>
          <td>
            <a href="/media/ff/2025/07/other/photo.jpg" target="_blank">Photo</a>
          </td>
        </tr>
        <tr>
          <td>Documents:</td>
          <td>
            <a href="/media/ff/2025/07/abc/plan.pdf" target="_blank">Grundriss</a>
          </td>
        </tr>
        """
        urls = extract_document_urls_from_html(html)
        assert len(urls) == 1
        assert urls[0].endswith("plan.pdf")

    def test_handles_html_with_no_media_links_at_all(self):
        urls = extract_document_urls_from_html("<html><body>No content</body></html>")
        assert urls == []

    def test_handles_png_links(self):
        html = """
        <tr>
          <td>Documents:</td>
          <td>
            <a href="/media/ff/2025/07/abc/floorplan.png" target="_blank">Plan</a>
          </td>
        </tr>
        """
        urls = extract_document_urls_from_html(html)
        assert len(urls) == 1
        assert urls[0].endswith(".png")


# ── scrape_listing_media (documents) ─────────────────────────────────────────


class TestScrapeListingMediaDocuments:
    def test_result_includes_documents_key(self):
        html = """
        <img src="/thumb/ff/2026/03/img1.jpg?alias=listing_gallery_l&amp;signature=A"/>
        <tr>
          <td>Documents:</td>
          <td>
            <a href="/media/ff/2025/07/abc/plan.pdf" target="_blank">Grundriss</a>
          </td>
        </tr>
        """
        with patch("strata_api.pipeline.media_downloader._fetch_page_html") as mock_fetch:
            mock_fetch.return_value = html
            result = scrape_listing_media("slug", 1)

        assert "documents" in result

    def test_documents_populated_from_documents_section(self):
        html = """
        <tr>
          <td>Documents:</td>
          <td>
            <a href="/media/ff/2025/07/abc/plan.pdf" target="_blank">Grundriss</a>
            <a href="/media/ff/2025/07/xyz/img.jpg" target="_blank">Download</a>
          </td>
        </tr>
        """
        with patch("strata_api.pipeline.media_downloader._fetch_page_html") as mock_fetch:
            mock_fetch.return_value = html
            result = scrape_listing_media("slug", 1)

        assert len(result["documents"]) == 2
        assert all(u.startswith("https://flatfox.ch/media/ff/") for u in result["documents"])

    def test_documents_empty_when_no_documents_section(self):
        html = '<img src="/thumb/ff/2026/03/img1.jpg?alias=listing_gallery_l&amp;signature=A"/>'
        with patch("strata_api.pipeline.media_downloader._fetch_page_html") as mock_fetch:
            mock_fetch.return_value = html
            result = scrape_listing_media("slug", 1)

        assert result["documents"] == []


# ── save_listing_media (documents) ───────────────────────────────────────────


class TestSaveListingMediaDocuments:
    def test_creates_document_rows_with_correct_image_type(self, db, listing_id, tmp_path):
        media = {
            "photos": [],
            "floorplans": [],
            "documents": [
                "https://flatfox.ch/media/ff/2025/07/abc/plan.pdf",
                "https://flatfox.ch/media/ff/2025/07/xyz/img.jpg",
            ],
        }
        with patch("strata_api.pipeline.media_downloader.download_file", return_value=True):
            counts = save_listing_media(db, listing_id, media, tmp_path)

        assert counts["documents_saved"] == 2

        rows = db.execute(
            select(ListingImage).where(
                ListingImage.listing_id == listing_id,
                ListingImage.image_type == "document",
            )
        ).scalars().all()
        assert len(rows) == 2
        assert all(r.image_type == "document" for r in rows)

    def test_documents_saved_count_in_return_value(self, db, listing_id, tmp_path):
        media = {
            "photos": [],
            "floorplans": [],
            "documents": [
                "https://flatfox.ch/media/ff/2025/07/abc/plan.pdf",
            ],
        }
        with patch("strata_api.pipeline.media_downloader.download_file", return_value=True):
            counts = save_listing_media(db, listing_id, media, tmp_path)

        assert "documents_saved" in counts
        assert counts["documents_saved"] == 1

    def test_document_stored_in_documents_subdir(self, db, listing_id, tmp_path):
        media = {
            "photos": [],
            "floorplans": [],
            "documents": [
                "https://flatfox.ch/media/ff/2025/07/abc/plan.pdf",
            ],
        }
        captured_paths: list[Path] = []

        def capture_download(url: str, dest: Path) -> bool:
            captured_paths.append(dest)
            return True

        with patch(
            "strata_api.pipeline.media_downloader.download_file",
            side_effect=capture_download,
        ):
            save_listing_media(db, listing_id, media, tmp_path)

        assert all("documents" in str(p) for p in captured_paths)

    def test_document_local_path_none_on_download_failure(self, db, listing_id, tmp_path):
        media = {
            "photos": [],
            "floorplans": [],
            "documents": [
                "https://flatfox.ch/media/ff/2025/07/abc/plan.pdf",
            ],
        }
        with patch("strata_api.pipeline.media_downloader.download_file", return_value=False):
            save_listing_media(db, listing_id, media, tmp_path)

        rows = db.execute(
            select(ListingImage).where(
                ListingImage.listing_id == listing_id,
                ListingImage.image_type == "document",
            )
        ).scalars().all()
        assert any(r.local_path is None for r in rows)

    def test_zero_documents_saved_when_no_documents(self, db, listing_id, tmp_path):
        media = {"photos": [], "floorplans": [], "documents": []}
        counts = save_listing_media(db, listing_id, media, tmp_path)
        assert counts["documents_saved"] == 0
