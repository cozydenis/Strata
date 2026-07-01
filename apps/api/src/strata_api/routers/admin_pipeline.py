"""Admin endpoints for triggering GWR data pipeline runs."""

from __future__ import annotations

import asyncio
import logging
import threading
from dataclasses import asdict

from fastapi import APIRouter, Depends, HTTPException, Response, Security
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session

from strata_api.config import settings
from strata_api.db.session import get_engine
from strata_api.notifications.emailer import build_sender
from strata_api.notifications.runner import run_notifications
from strata_api.notifications.user_emails import build_email_resolver
from strata_api.pipeline.runner import PipelineResult, run_kanton_pipeline, run_stadt_pipeline

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/pipeline", tags=["admin"])

_SOURCES = {"stadt", "kanton"}
_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=True)


def _require_api_key(key: str = Security(_api_key_header)) -> None:
    """Reject requests whose API key doesn't match settings.pipeline_api_key."""
    if not settings.pipeline_api_key or key != settings.pipeline_api_key:
        raise HTTPException(status_code=401, detail="Invalid or missing API key.")


@router.post("/run/{source}", status_code=202, dependencies=[Depends(_require_api_key)])
def trigger_pipeline(source: str) -> dict:
    """Trigger a GWR pipeline run in the background and return 202 immediately.

    Runs take minutes — well past the platform's HTTP timeout — so the work
    happens in a background thread, same as /run-listings.
    """
    if source not in _SOURCES:
        raise HTTPException(status_code=404, detail=f"Unknown source '{source}'. Use 'stadt' or 'kanton'.")

    def _run() -> None:
        engine = get_engine()
        try:
            if source == "stadt":
                result: PipelineResult = run_stadt_pipeline(engine)
            else:
                result = run_kanton_pipeline(engine)
            logger.info("GWR pipeline completed for source=%s: %s", source, asdict(result))
        except Exception:
            logger.exception("GWR pipeline run failed for source=%s", source)

    threading.Thread(target=_run, daemon=True).start()
    return {
        "status": "accepted",
        "source": source,
        "message": "GWR pipeline started in background. Check server logs for progress.",
    }


@router.post("/run-listings", status_code=202, dependencies=[Depends(_require_api_key)])
def trigger_listing_pipeline(response: Response) -> dict:
    """Trigger the listing ingestion pipeline in the background and return 202 immediately."""
    from strata_api.pipeline.listing_runner import run_listing_pipeline

    def _run() -> None:
        engine = get_engine()
        try:
            with Session(engine) as db:
                stats = asyncio.run(run_listing_pipeline(db))
            logger.info("Listing pipeline completed: %s", stats)
        except Exception:
            logger.exception("Listing pipeline run failed")

    threading.Thread(target=_run, daemon=True).start()
    return {"status": "accepted", "message": "Listing pipeline started in background. Check server logs for progress."}


@router.post("/run-notifications", status_code=200, dependencies=[Depends(_require_api_key)])
def trigger_notifications() -> dict:
    """Send watch-event email digests to every user with fresh events.

    Runs synchronously and returns the summary counts. The email sender and
    user-email resolver are built from settings (ConsoleSender + Supabase Admin
    API by default); both are module-level so tests can inject fakes.
    """
    engine = get_engine()
    sender = build_sender(settings)
    resolve_email = build_email_resolver(settings)
    summary = run_notifications(engine, sender=sender, resolve_email=resolve_email)
    logger.info("Notification run completed: %s", asdict(summary))
    return {"status": "completed", **asdict(summary)}
