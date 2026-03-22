"""SQLAlchemy engine and session factory."""
from __future__ import annotations

from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from strata_api.config import settings


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    """Return a cached SQLAlchemy engine using the configured DATABASE_URL."""
    return create_engine(settings.database_url, pool_pre_ping=True)


def get_session() -> Session:
    """Return a new SQLAlchemy session (caller is responsible for closing)."""
    factory = sessionmaker(bind=get_engine())
    return factory()
