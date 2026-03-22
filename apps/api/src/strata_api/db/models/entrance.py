"""SQLAlchemy model for GWR building entrances (gwr_entrances)."""
from __future__ import annotations

from sqlalchemy import Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from strata_api.db.base import Base, TimestampMixin


class Entrance(TimestampMixin, Base):
    """One row per (EGID, EDID) entrance pair."""

    __tablename__ = "gwr_entrances"

    egid: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    edid: Mapped[int] = mapped_column(Integer, primary_key=True)

    strname: Mapped[str | None] = mapped_column(String(100), nullable=True)
    deinr: Mapped[str | None] = mapped_column(String(20), nullable=True)   # entrance number
    dplz4: Mapped[int | None] = mapped_column(Integer, nullable=True)      # postcode
    dplzname: Mapped[str | None] = mapped_column(String(100), nullable=True)
    doffadr: Mapped[int | None] = mapped_column(Integer, nullable=True)    # official address flag

    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    lon: Mapped[float | None] = mapped_column(Float, nullable=True)

    data_source: Mapped[str] = mapped_column(String(10), nullable=False)
