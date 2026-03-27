from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from strata_api.config import settings
from strata_api.routers import admin_pipeline, listings, neighborhoods, registry

app = FastAPI(title="Strata API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization", "X-API-Key"],
)

app.include_router(admin_pipeline.router)
app.include_router(listings.router)
app.include_router(registry.router)
app.include_router(neighborhoods.router)


# Serve downloaded images/documents at /media/images/{egid}/...
# __file__ = src/strata_api/main.py → parents[2] = apps/api/
_DATA_DIR = Path(__file__).resolve().parents[2] / "data"
if _DATA_DIR.exists():
    app.mount("/media", StaticFiles(directory=str(_DATA_DIR)), name="media")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
