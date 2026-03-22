"""SQLAlchemy model for pipeline run audit log (pipeline_runs)."""
from __future__ import annotations

import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from strata_api.db.base import Base


class PipelineRun(Base):
    """Audit record for each pipeline execution."""

    __tablename__ = "pipeline_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_type: Mapped[str] = mapped_column(String(10), nullable=False)   # 'stadt' | 'kanton'
    status: Mapped[str] = mapped_column(String(20), nullable=False)     # 'started' | 'completed' | 'failed'

    buildings_upserted: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    entrances_upserted: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    units_upserted: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    started_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)
    finished_at: Mapped[datetime.datetime | None] = mapped_column(DateTime, nullable=True)
