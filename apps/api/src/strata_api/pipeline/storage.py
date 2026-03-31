"""Supabase Storage uploader for listing media."""
from __future__ import annotations

import logging
import urllib.request

logger = logging.getLogger(__name__)

_USER_AGENT = "Strata-Pipeline/1.0 (research; contact: hello@strata.ch)"

_EXT_CONTENT_TYPE = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".pdf": "application/pdf",
}


def _content_type(filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower()
    return _EXT_CONTENT_TYPE.get(f".{ext}", "application/octet-stream")


class SupabaseStorageUploader:
    """Upload files to a public Supabase Storage bucket and return permanent public URLs."""

    BUCKET = "listing-media"

    def __init__(self, supabase_url: str, service_key: str) -> None:
        self._base = supabase_url.rstrip("/")
        self._key = service_key

    def upload(self, data: bytes, storage_path: str) -> str:
        """Upload raw bytes to storage_path in the bucket. Returns the public URL.

        Raises RuntimeError if the upload fails.
        """
        url = f"{self._base}/storage/v1/object/{self.BUCKET}/{storage_path}"
        req = urllib.request.Request(
            url,
            data=data,
            method="POST",
            headers={
                "Authorization": f"Bearer {self._key}",
                "Content-Type": _content_type(storage_path),
                "Cache-Control": "public, max-age=31536000",
                "x-upsert": "true",
                "User-Agent": _USER_AGENT,
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                resp.read()
        except Exception as exc:
            raise RuntimeError(f"Storage upload failed for {storage_path}: {exc}") from exc
        return self.public_url(storage_path)

    def public_url(self, storage_path: str) -> str:
        return f"{self._base}/storage/v1/object/public/{self.BUCKET}/{storage_path}"
