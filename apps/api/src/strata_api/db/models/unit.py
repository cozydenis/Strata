"""SQLAlchemy model for GWR dwelling units (gwr_units)."""
from __future__ import annotations

from sqlalchemy import Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from strata_api.db.base import Base, TimestampMixin


class Unit(TimestampMixin, Base):
    """One row per (EGID, EWID) dwelling unit pair."""

    __tablename__ = "gwr_units"

    egid: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    ewid: Mapped[int] = mapped_column(Integer, primary_key=True)

    edid: Mapped[int | None] = mapped_column(Integer, nullable=True)       # entrance ref
    wstwk: Mapped[int | None] = mapped_column(Integer, nullable=True)      # Stockwerk_Code
    wstwklang: Mapped[str | None] = mapped_column(String(100), nullable=True)  # floor description
    wazim: Mapped[int | None] = mapped_column(Integer, nullable=True)      # Anzahl Zimmer
    warea: Mapped[int | None] = mapped_column(Integer, nullable=True)      # Wohnungsflaeche m²
    wkche: Mapped[int | None] = mapped_column(Integer, nullable=True)      # Kocheinrichtung
    wstat: Mapped[int | None] = mapped_column(Integer, nullable=True)      # Wohnungsstatus
    wbauj: Mapped[int | None] = mapped_column(Integer, nullable=True)      # Baujahr
    wabbj: Mapped[int | None] = mapped_column(Integer, nullable=True)      # Abbruchjahr

    # Address (denormalized from entrance for convenience)
    dplz4: Mapped[int | None] = mapped_column(Integer, nullable=True)
    dplzname: Mapped[str | None] = mapped_column(String(100), nullable=True)
    strname: Mapped[str | None] = mapped_column(String(100), nullable=True)
    deinr: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Coordinates (WGS84)
    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    lon: Mapped[float | None] = mapped_column(Float, nullable=True)

    data_source: Mapped[str] = mapped_column(String(10), nullable=False)
