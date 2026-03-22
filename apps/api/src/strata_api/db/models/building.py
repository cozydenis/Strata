"""SQLAlchemy model for GWR buildings (gwr_buildings)."""
from __future__ import annotations

from sqlalchemy import Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from strata_api.db.base import Base, TimestampMixin


class Building(TimestampMixin, Base):
    """One row per EGID (federal building identifier)."""

    __tablename__ = "gwr_buildings"

    egid: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # GWR attribute codes
    gstat: Mapped[int | None] = mapped_column(Integer, nullable=True)   # Gebaeudestatus
    gkat: Mapped[int | None] = mapped_column(Integer, nullable=True)    # Gebaeudekategorie
    gklas: Mapped[int | None] = mapped_column(Integer, nullable=True)   # Gebaeudeklasse
    gbauj: Mapped[int | None] = mapped_column(Integer, nullable=True)   # Baujahr
    gabbj: Mapped[int | None] = mapped_column(Integer, nullable=True)   # Abbruchjahr
    garea: Mapped[int | None] = mapped_column(Integer, nullable=True)   # Gebaeudeflaeche
    gastw: Mapped[int | None] = mapped_column(Integer, nullable=True)   # Anzahl Geschosse
    ganzwhg: Mapped[int | None] = mapped_column(Integer, nullable=True) # Anzahl Wohnungen

    # Coordinates (WGS84)
    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    lon: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Administrative
    municipality: Mapped[str | None] = mapped_column(String(100), nullable=True)
    municipality_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    canton: Mapped[str | None] = mapped_column(String(2), nullable=True)

    # Pipeline metadata
    data_source: Mapped[str] = mapped_column(String(10), nullable=False)
