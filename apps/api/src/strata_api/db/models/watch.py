"""SQLAlchemy model for user watchlist entries (watches)."""
from __future__ import annotations

import datetime

from sqlalchemy import DateTime, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from strata_api.db.base import Base


class Watch(Base):
    """A user watching a building (ewid NULL) or a specific unit within it."""

    __tablename__ = "watches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)  # Supabase auth uid
    egid: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    ewid: Mapped[int | None] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)
    # Last time a notification digest was successfully sent covering this watch.
    # NULL = never notified; the runner uses it as the per-user event cutoff.
    last_notified_at: Mapped[datetime.datetime | None] = mapped_column(DateTime, nullable=True)

    __table_args__ = (
        # NULL ewid values are distinct per SQL semantics — building-level
        # idempotency is enforced in the router, not here.
        UniqueConstraint("user_id", "egid", "ewid", name="uq_watch_user_target"),
    )
