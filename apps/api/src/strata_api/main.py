from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from strata_api.config import settings
from strata_api.routers import admin_pipeline, registry

app = FastAPI(title="Strata API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(admin_pipeline.router)
app.include_router(registry.router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
