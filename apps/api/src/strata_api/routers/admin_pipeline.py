"""Admin endpoints for triggering GWR data pipeline runs."""
from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, HTTPException

from strata_api.db.session import get_engine
from strata_api.pipeline.runner import PipelineResult, run_kanton_pipeline, run_stadt_pipeline

router = APIRouter(prefix="/admin/pipeline", tags=["admin"])

_SOURCES = {"stadt", "kanton"}


@router.post("/run/{source}")
def trigger_pipeline(source: str) -> dict:
    """Trigger a pipeline run for the given source (stadt or kanton)."""
    if source not in _SOURCES:
        raise HTTPException(status_code=404, detail=f"Unknown source '{source}'. Use 'stadt' or 'kanton'.")

    engine = get_engine()
    if source == "stadt":
        result: PipelineResult = run_stadt_pipeline(engine)
    else:
        result = run_kanton_pipeline(engine)

    return asdict(result)
