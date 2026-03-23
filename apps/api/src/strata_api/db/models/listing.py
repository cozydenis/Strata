"""SQLAlchemy models for rental listing ingestion pipeline."""
from __future__ import annotations

import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from strata_api.db.base import Base, TimestampMixin


class Listing(TimestampMixin, Base):
    """One row per unique listing, identified by (source, source_id)."""

    __tablename__ = "listings"
    __table_args__ = (UniqueConstraint("source", "source_id", name="uq_listings_source_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Source identity
    source: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    source_id: Mapped[str] = mapped_column(String(50), nullable=False)

    # Pricing
    rent_net: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rent_gross: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rent_charges: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Unit characteristics
    rooms: Mapped[float | None] = mapped_column(Float, nullable=True)
    area_m2: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Address (raw + normalized)
    address_raw: Mapped[str | None] = mapped_column(String(300), nullable=True)
    street: Mapped[str | None] = mapped_column(String(150), nullable=True)
    house_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    plz: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Coordinates
    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    lng: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Classification
    object_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    offer_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    status: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Source URL
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Rich content
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Lifecycle
    first_seen: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)
    last_seen: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Relationships
    unit_matches: Mapped[list[ListingUnitMatch]] = relationship(
        "ListingUnitMatch", back_populates="listing", cascade="all, delete-orphan"
    )
    history: Mapped[list[ListingHistory]] = relationship(
        "ListingHistory", back_populates="listing", cascade="all, delete-orphan"
    )
    images: Mapped[list[ListingImage]] = relationship(
        "ListingImage", back_populates="listing", cascade="all, delete-orphan",
        order_by="ListingImage.ordering",
    )
    documents: Mapped[list[ListingDocument]] = relationship(
        "ListingDocument", back_populates="listing", cascade="all, delete-orphan",
    )


class ListingUnitMatch(Base):
    """Maps a listing to one or more candidate units in the GWR registry."""

    __tablename__ = "listing_unit_matches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    listing_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("listings.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # GWR unit reference
    egid: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    ewid: Mapped[int | None] = mapped_column(Integer, nullable=True)  # null for building_only

    # Match quality
    match_confidence: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # "exact" | "probable" | "building_only"
    matched_egid: Mapped[int] = mapped_column(Integer, nullable=False)

    listing: Mapped[Listing] = relationship("Listing", back_populates="unit_matches")


class ListingHistory(Base):
    """Tracks changes to listing fields over time (price changes, status changes)."""

    __tablename__ = "listing_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    listing_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("listings.id", ondelete="CASCADE"), nullable=False, index=True
    )

    field_changed: Mapped[str] = mapped_column(String(50), nullable=False)
    old_value: Mapped[str | None] = mapped_column(String(500), nullable=True)
    new_value: Mapped[str | None] = mapped_column(String(500), nullable=True)
    changed_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)

    listing: Mapped[Listing] = relationship("Listing", back_populates="history")


class ListingImage(Base):
    """Image associated with a listing (photo, floor plan, cover)."""

    __tablename__ = "listing_images"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    listing_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("listings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    local_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    caption: Mapped[str | None] = mapped_column(String(300), nullable=True)
    ordering: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    image_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="photo"
    )  # "photo" | "floorplan" | "cover"

    listing: Mapped[Listing] = relationship("Listing", back_populates="images")


class ListingDocument(Base):
    """Document associated with a listing (floor plan PDF, brochure)."""

    __tablename__ = "listing_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    listing_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("listings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    local_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    caption: Mapped[str | None] = mapped_column(String(300), nullable=True)
    doc_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="floorplan"
    )  # "floorplan" | "other"

    listing: Mapped[Listing] = relationship("Listing", back_populates="documents")
