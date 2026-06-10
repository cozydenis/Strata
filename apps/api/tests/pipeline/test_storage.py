"""Tests for Supabase Storage uploader and save_listing_media uploader integration."""
from __future__ import annotations

import datetime
import io
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from strata_api.db.base import Base
from strata_api.db.models.listing import Listing, ListingImage
from strata_api.pipeline.storage import SupabaseStorageUploader, _content_type
from strata_api.pipeline.media_downloader import save_listing_media


# ── fixtures ─────────────────────────────────────────────────────────────────


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
    row = Listing(
        source="flatfox",
        source_id="test-storage-99",
        first_seen=datetime.datetime.utcnow(),
        last_seen=datetime.datetime.utcnow(),
        is_active=True,
    )
    db.add(row)
    db.flush()
    return row.id


@pytest.fixture
def uploader():
    return SupabaseStorageUploader(
        supabase_url="https://abcdef.supabase.co",
        service_key="test-service-key",
    )


# ── _content_type ─────────────────────────────────────────────────────────────


class TestContentType:
    def test_jpg_returns_image_jpeg(self):
        assert _content_type("photo.jpg") == "image/jpeg"

    def test_jpeg_returns_image_jpeg(self):
        assert _content_type("photo.jpeg") == "image/jpeg"

    def test_png_returns_image_png(self):
        assert _content_type("screenshot.png") == "image/png"

    def test_webp_returns_image_webp(self):
        assert _content_type("image.webp") == "image/webp"

    def test_pdf_returns_application_pdf(self):
        assert _content_type("document.pdf") == "application/pdf"

    def test_unknown_extension_returns_octet_stream(self):
        assert _content_type("file.xyz") == "application/octet-stream"

    def test_no_extension_returns_octet_stream(self):
        assert _content_type("noextension") == "application/octet-stream"

    def test_case_insensitive_JPG(self):
        assert _content_type("photo.JPG") == "image/jpeg"

    def test_case_insensitive_PDF(self):
        assert _content_type("plan.PDF") == "application/pdf"

    def test_path_with_subdirs_uses_last_segment(self):
        assert _content_type("photos/listing/42/img.jpg") == "image/jpeg"


# ── SupabaseStorageUploader.public_url ───────────────────────────────────────


class TestPublicUrl:
    def test_returns_correct_url_format(self, uploader):
        url = uploader.public_url("photos/42/img.jpg")
        assert url == (
            "https://abcdef.supabase.co/storage/v1/object/public/listing-media/photos/42/img.jpg"
        )

    def test_bucket_name_is_listing_media(self, uploader):
        url = uploader.public_url("anything/file.jpg")
        assert "/listing-media/" in url

    def test_trailing_slash_stripped_from_base_url(self):
        u = SupabaseStorageUploader(
            supabase_url="https://abcdef.supabase.co/",
            service_key="key",
        )
        url = u.public_url("photos/img.jpg")
        # Must not produce double slash between base and storage path
        assert "supabase.co//storage" not in url
        assert url == (
            "https://abcdef.supabase.co/storage/v1/object/public/listing-media/photos/img.jpg"
        )

    def test_storage_path_is_preserved_verbatim(self, uploader):
        path = "documents/999/plan with spaces.pdf"
        url = uploader.public_url(path)
        assert url.endswith(path)


# ── SupabaseStorageUploader.upload — success path ────────────────────────────


class TestUploadSuccess:
    def test_returns_public_url_on_success(self, uploader):
        mock_response = MagicMock()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_response.read.return_value = b'{"Key":"listing-media/photos/42/img.jpg"}'

        with patch("urllib.request.urlopen", return_value=mock_response):
            result = uploader.upload(b"\xff\xd8\xff\xe0" + b"\x00" * 10, "photos/42/img.jpg")

        expected = uploader.public_url("photos/42/img.jpg")
        assert result == expected

    def test_posts_to_correct_storage_endpoint(self, uploader):
        mock_response = MagicMock()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_response.read.return_value = b"{}"

        captured_requests: list = []

        def capture_urlopen(req, timeout=None):
            captured_requests.append(req)
            return mock_response

        with patch("urllib.request.urlopen", side_effect=capture_urlopen):
            uploader.upload(b"data", "photos/42/img.jpg")

        assert len(captured_requests) == 1
        req = captured_requests[0]
        assert req.full_url == (
            "https://abcdef.supabase.co/storage/v1/object/listing-media/photos/42/img.jpg"
        )

    def test_request_uses_post_method(self, uploader):
        mock_response = MagicMock()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_response.read.return_value = b"{}"

        captured_requests: list = []

        def capture_urlopen(req, timeout=None):
            captured_requests.append(req)
            return mock_response

        with patch("urllib.request.urlopen", side_effect=capture_urlopen):
            uploader.upload(b"data", "photos/42/img.jpg")

        assert captured_requests[0].get_method() == "POST"

    def test_authorization_header_is_set(self, uploader):
        mock_response = MagicMock()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_response.read.return_value = b"{}"

        captured_requests: list = []

        def capture_urlopen(req, timeout=None):
            captured_requests.append(req)
            return mock_response

        with patch("urllib.request.urlopen", side_effect=capture_urlopen):
            uploader.upload(b"data", "photos/42/img.jpg")

        auth_header = captured_requests[0].get_header("Authorization")
        assert auth_header == "Bearer test-service-key"

    def test_content_type_header_matches_file_extension(self, uploader):
        mock_response = MagicMock()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_response.read.return_value = b"{}"

        captured_requests: list = []

        def capture_urlopen(req, timeout=None):
            captured_requests.append(req)
            return mock_response

        with patch("urllib.request.urlopen", side_effect=capture_urlopen):
            uploader.upload(b"%PDF-1.4", "documents/42/plan.pdf")

        content_type_header = captured_requests[0].get_header("Content-type")
        assert content_type_header == "application/pdf"

    def test_upsert_header_is_set_to_true(self, uploader):
        mock_response = MagicMock()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_response.read.return_value = b"{}"

        captured_requests: list = []

        def capture_urlopen(req, timeout=None):
            captured_requests.append(req)
            return mock_response

        with patch("urllib.request.urlopen", side_effect=capture_urlopen):
            uploader.upload(b"data", "photos/42/img.jpg")

        # urllib.request.Request capitalises the first letter of header names
        upsert_header = captured_requests[0].get_header("X-upsert")
        assert upsert_header == "true"


# ── SupabaseStorageUploader.upload — failure path ────────────────────────────


class TestUploadFailure:
    def test_network_error_raises_runtime_error(self, uploader):
        with patch("urllib.request.urlopen", side_effect=OSError("connection refused")):
            with pytest.raises(RuntimeError, match="Storage upload failed"):
                uploader.upload(b"data", "photos/42/img.jpg")

    def test_runtime_error_message_contains_storage_path(self, uploader):
        with patch("urllib.request.urlopen", side_effect=OSError("timeout")):
            with pytest.raises(RuntimeError, match="photos/42/img.jpg"):
                uploader.upload(b"data", "photos/42/img.jpg")

    def test_original_exception_is_chained(self, uploader):
        original = OSError("connection refused")
        with patch("urllib.request.urlopen", side_effect=original):
            with pytest.raises(RuntimeError) as exc_info:
                uploader.upload(b"data", "photos/42/img.jpg")
        assert exc_info.value.__cause__ is original

    def test_generic_exception_also_raises_runtime_error(self, uploader):
        with patch("urllib.request.urlopen", side_effect=Exception("unexpected")):
            with pytest.raises(RuntimeError):
                uploader.upload(b"data", "photos/42/img.jpg")


# ── save_listing_media with uploader — success path ──────────────────────────


class TestSaveListingMediaWithUploader:
    def _make_uploader(self) -> SupabaseStorageUploader:
        return SupabaseStorageUploader(
            supabase_url="https://abcdef.supabase.co",
            service_key="test-key",
        )

    def test_supabase_public_url_stored_in_listing_images_url(self, db, listing_id, tmp_path):
        media = {
            "photos": [
                "https://flatfox.ch/thumb/ff/2026/03/img1.jpg?alias=listing_gallery_l&signature=A",
            ],
            "floorplans": [],
            "documents": [],
        }
        fake_bytes = b"\xff\xd8\xff\xe0" + b"\x00" * 20
        supabase_public_url = (
            "https://abcdef.supabase.co/storage/v1/object/public/listing-media/"
            f"photos/{listing_id}/img1.jpg"
        )
        mock_uploader = self._make_uploader()

        with (
            patch("strata_api.pipeline.media_downloader._url_read", return_value=fake_bytes),
            patch.object(mock_uploader, "upload", return_value=supabase_public_url),
        ):
            save_listing_media(db, listing_id, media, tmp_path, uploader=mock_uploader)

        rows = db.execute(
            select(ListingImage).where(ListingImage.listing_id == listing_id)
        ).scalars().all()
        assert len(rows) == 1
        assert rows[0].url == supabase_public_url

    def test_original_flatfox_url_stored_in_local_path(self, db, listing_id, tmp_path):
        original_url = (
            "https://flatfox.ch/thumb/ff/2026/03/img2.jpg?alias=listing_gallery_l&signature=B"
        )
        media = {
            "photos": [original_url],
            "floorplans": [],
            "documents": [],
        }
        fake_bytes = b"\xff\xd8" + b"\x00" * 10
        supabase_public_url = (
            "https://abcdef.supabase.co/storage/v1/object/public/listing-media/"
            f"photos/{listing_id}/img2.jpg"
        )
        mock_uploader = self._make_uploader()

        with (
            patch("strata_api.pipeline.media_downloader._url_read", return_value=fake_bytes),
            patch.object(mock_uploader, "upload", return_value=supabase_public_url),
        ):
            save_listing_media(db, listing_id, media, tmp_path, uploader=mock_uploader)

        rows = db.execute(
            select(ListingImage).where(ListingImage.listing_id == listing_id)
        ).scalars().all()
        assert len(rows) == 1
        assert rows[0].local_path == original_url

    def test_uploader_called_with_downloaded_bytes_and_storage_path(
        self, db, listing_id, tmp_path
    ):
        original_url = (
            "https://flatfox.ch/thumb/ff/2026/03/img3.jpg?alias=listing_gallery_l&signature=C"
        )
        media = {
            "photos": [original_url],
            "floorplans": [],
            "documents": [],
        }
        fake_bytes = b"\xff\xd8\xff" + b"\x00" * 30
        mock_uploader = self._make_uploader()
        upload_calls: list = []

        def capture_upload(data: bytes, storage_path: str) -> str:
            upload_calls.append((data, storage_path))
            return mock_uploader.public_url(storage_path)

        with (
            patch("strata_api.pipeline.media_downloader._url_read", return_value=fake_bytes),
            patch.object(mock_uploader, "upload", side_effect=capture_upload),
        ):
            save_listing_media(db, listing_id, media, tmp_path, uploader=mock_uploader)

        assert len(upload_calls) == 1
        data_sent, path_sent = upload_calls[0]
        assert data_sent == fake_bytes
        assert f"photos/{listing_id}/img3.jpg" == path_sent

    def test_no_disk_file_written_when_uploader_provided(self, db, listing_id, tmp_path):
        media = {
            "photos": [
                "https://flatfox.ch/thumb/ff/2026/03/img4.jpg?alias=listing_gallery_l&signature=D",
            ],
            "floorplans": [],
            "documents": [],
        }
        mock_uploader = self._make_uploader()

        with (
            patch("strata_api.pipeline.media_downloader._url_read", return_value=b"\xff\xd8"),
            patch.object(
                mock_uploader,
                "upload",
                return_value=mock_uploader.public_url(f"photos/{listing_id}/img4.jpg"),
            ),
        ):
            save_listing_media(db, listing_id, media, tmp_path, uploader=mock_uploader)

        # No file should have been written to the photos subdir
        photos_dir = tmp_path / "photos"
        assert not photos_dir.exists() or not any(photos_dir.iterdir())

    def test_returns_correct_counts_with_uploader(self, db, listing_id, tmp_path):
        media = {
            "photos": [
                "https://flatfox.ch/thumb/ff/2026/03/p1.jpg?alias=listing_gallery_l&signature=A",
                "https://flatfox.ch/thumb/ff/2026/03/p2.jpg?alias=listing_gallery_l&signature=B",
            ],
            "floorplans": [
                "https://flatfox.ch/thumb/ff/2026/03/fp1.jpg?alias=listing_floorplan_l&signature=C",
            ],
            "documents": [],
        }
        mock_uploader = self._make_uploader()

        def fake_upload(data: bytes, storage_path: str) -> str:
            return mock_uploader.public_url(storage_path)

        with (
            patch("strata_api.pipeline.media_downloader._url_read", return_value=b"\xff\xd8"),
            patch.object(mock_uploader, "upload", side_effect=fake_upload),
        ):
            counts = save_listing_media(db, listing_id, media, tmp_path, uploader=mock_uploader)

        assert counts["photos_saved"] == 2
        assert counts["floorplans_saved"] == 1
        assert counts["documents_saved"] == 0


# ── save_listing_media with uploader — upload failure fallback ────────────────


class TestSaveListingMediaUploaderFailure:
    def _make_uploader(self) -> SupabaseStorageUploader:
        return SupabaseStorageUploader(
            supabase_url="https://abcdef.supabase.co",
            service_key="test-key",
        )

    def test_falls_back_to_original_url_on_upload_failure(self, db, listing_id, tmp_path):
        original_url = (
            "https://flatfox.ch/thumb/ff/2026/03/bad.jpg?alias=listing_gallery_l&signature=X"
        )
        media = {
            "photos": [original_url],
            "floorplans": [],
            "documents": [],
        }
        mock_uploader = self._make_uploader()

        with (
            patch(
                "strata_api.pipeline.media_downloader._url_read",
                side_effect=RuntimeError("Storage upload failed for photos/42/bad.jpg: timeout"),
            ),
        ):
            save_listing_media(db, listing_id, media, tmp_path, uploader=mock_uploader)

        rows = db.execute(
            select(ListingImage).where(ListingImage.listing_id == listing_id)
        ).scalars().all()
        assert len(rows) == 1
        # On failure the original Flatfox URL must be used as fallback
        assert rows[0].url == original_url

    def test_upload_failure_does_not_raise(self, db, listing_id, tmp_path):
        """A failed upload must be swallowed — the pipeline should keep running."""
        media = {
            "photos": [
                "https://flatfox.ch/thumb/ff/2026/03/err.jpg?alias=listing_gallery_l&signature=Y",
            ],
            "floorplans": [],
            "documents": [],
        }
        mock_uploader = self._make_uploader()

        with (
            patch("strata_api.pipeline.media_downloader._url_read", return_value=b"\xff\xd8"),
            patch.object(
                mock_uploader, "upload", side_effect=RuntimeError("Storage upload failed")
            ),
        ):
            # Must not raise — failures are caught and logged
            counts = save_listing_media(db, listing_id, media, tmp_path, uploader=mock_uploader)

        assert counts["photos_saved"] == 1

    def test_upload_failure_stores_original_url_not_supabase_url(self, db, listing_id, tmp_path):
        original_url = (
            "https://flatfox.ch/thumb/ff/2026/03/fail.jpg?alias=listing_gallery_l&signature=Z"
        )
        media = {
            "photos": [original_url],
            "floorplans": [],
            "documents": [],
        }
        mock_uploader = self._make_uploader()

        with (
            patch("strata_api.pipeline.media_downloader._url_read", return_value=b"\xff\xd8"),
            patch.object(
                mock_uploader, "upload", side_effect=RuntimeError("Storage upload failed")
            ),
        ):
            save_listing_media(db, listing_id, media, tmp_path, uploader=mock_uploader)

        rows = db.execute(
            select(ListingImage).where(ListingImage.listing_id == listing_id)
        ).scalars().all()
        assert len(rows) == 1
        stored_url = rows[0].url
        assert "supabase" not in stored_url
        assert stored_url == original_url
