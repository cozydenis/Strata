"""SQLAlchemy engine and session factory."""
from __future__ import annotations

from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from strata_api.config import settings

# TCP keepalive args for PostgreSQL — keeps long-running pipeline connections alive.
# Ignored by SQLite (psycopg2 not used there).
_PG_CONNECT_ARGS = {
    "keepalives": 1,
    "keepalives_idle": 30,      # send keepalive after 30s idle
    "keepalives_interval": 10,  # retry every 10s
    "keepalives_count": 5,      # drop after 5 failed probes
}


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    """Return a cached SQLAlchemy engine using the configured DATABASE_URL."""
    is_postgres = settings.database_url.startswith("postgresql")
    connect_args = _PG_CONNECT_ARGS if is_postgres else {}
    return create_engine(
        settings.database_url,
        pool_pre_ping=True,
        connect_args=connect_args,
    )


def get_session() -> Session:
    """Return a new SQLAlchemy session (caller is responsible for closing)."""
    factory = sessionmaker(bind=get_engine())
    return factory()
