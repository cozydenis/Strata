"""Admin endpoints for triggering GWR data pipeline runs."""
from __future__ import annotations

import asyncio
import logging
from dataclasses import asdict

from fastapi import APIRouter, Depends, HTTPException, Security
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session

from strata_api.config import settings
from strata_api.db.session import get_engine
from strata_api.pipeline.runner import PipelineResult, run_kanton_pipeline, run_stadt_pipeline

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/pipeline", tags=["admin"])

_SOURCES = {"stadt", "kanton"}
_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=True)


def _require_api_key(key: str = Security(_api_key_header)) -> None:
    """Reject requests whose API key doesn't match settings.pipeline_api_key."""
    if not settings.pipeline_api_key or key != settings.pipeline_api_key:
        raise HTTPException(status_code=401, detail="Invalid or missing API key.")


@router.post("/run/{source}", dependencies=[Depends(_require_api_key)])
def trigger_pipeline(source: str) -> dict:
    """Trigger a pipeline run for the given source (stadt or kanton)."""
    if source not in _SOURCES:
        raise HTTPException(status_code=404, detail=f"Unknown source '{source}'. Use 'stadt' or 'kanton'.")

    engine = get_engine()
    try:
        if source == "stadt":
            result: PipelineResult = run_stadt_pipeline(engine)
        else:
            result = run_kanton_pipeline(engine)
    except Exception as err:
        logger.exception("Pipeline run failed for source=%s", source)
        raise HTTPException(status_code=500, detail="Pipeline run failed — check server logs.") from err

    return asdict(result)


@router.post("/run-listings", dependencies=[Depends(_require_api_key)])
def trigger_listing_pipeline() -> dict:
    """Trigger the listing ingestion pipeline (fetch + upsert + media download)."""
    from strata_api.pipeline.listing_runner import run_listing_pipeline

    engine = get_engine()
    try:
        with Session(engine) as db:
            stats = asyncio.run(run_listing_pipeline(db))
    except Exception as err:
        logger.exception("Listing pipeline run failed")
        raise HTTPException(status_code=500, detail="Listing pipeline failed — check server logs.") from err

    return stats
