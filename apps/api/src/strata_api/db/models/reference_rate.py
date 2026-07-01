"""SQLAlchemy model for the Referenzzinssatz history."""
from __future__ import annotations

import datetime

from sqlalchemy import Date, Float, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from strata_api.db.base import Base


class ReferenceRate(Base):
    """One row per published change of the hypothekarischer Referenzzinssatz."""

    __tablename__ = "reference_rates"
    __table_args__ = (UniqueConstraint("valid_from", name="uq_reference_rate_valid_from"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    valid_from: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    rate_percent: Mapped[float] = mapped_column(Float, nullable=False)
    source: Mapped[str] = mapped_column(String(50), nullable=False, default="bwo")
