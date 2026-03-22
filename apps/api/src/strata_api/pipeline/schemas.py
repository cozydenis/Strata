"""Pydantic v2 frozen schemas — intermediate data between parsers and the DB loader."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class BuildingRecord(BaseModel):
    """Normalised GWR building record (one per EGID)."""

    model_config = ConfigDict(frozen=True)

    egid: int
    data_source: str  # 'stadt' | 'kanton'

    gstat: int | None = None        # Gebaeudestatus_Code
    gkat: int | None = None         # Gebaeudekategorie_Code
    gklas: int | None = None        # Gebaeudeklasse_Code
    gbauj: int | None = None        # Baujahr
    gabbj: int | None = None        # Abbruchjahr
    garea: int | None = None        # Gebaeudeflaeche m²
    gastw: int | None = None        # Anzahl Geschosse
    ganzwhg: int | None = None      # Anzahl Wohnungen

    lat: float | None = None        # WGS84
    lon: float | None = None        # WGS84

    municipality: str | None = None
    municipality_code: int | None = None
    canton: str | None = None


class EntranceRecord(BaseModel):
    """Normalised GWR building entrance record (one per EGID + EDID)."""

    model_config = ConfigDict(frozen=True)

    egid: int
    edid: int
    data_source: str

    strname: str | None = None
    deinr: str | None = None        # entrance number
    dplz4: int | None = None        # postcode
    dplzname: str | None = None
    doffadr: int | None = None      # official address flag

    lat: float | None = None
    lon: float | None = None


class UnitRecord(BaseModel):
    """Normalised GWR dwelling unit record (one per EGID + EWID)."""

    model_config = ConfigDict(frozen=True)

    egid: int
    ewid: int
    data_source: str

    edid: int | None = None         # entrance reference
    wstwk: int | None = None        # Stockwerk_Code
    wstwklang: str | None = None    # floor description
    wazim: int | None = None        # Anzahl Zimmer
    warea: int | None = None        # Wohnungsflaeche m²
    wkche: int | None = None        # Kocheinrichtung_Code
    wstat: int | None = None        # Wohnungsstatus_Code
    wbauj: int | None = None        # Baujahr der Wohnung
    wabbj: int | None = None        # Abbruchjahr

    dplz4: int | None = None
    dplzname: str | None = None
    strname: str | None = None
    deinr: str | None = None

    lat: float | None = None
    lon: float | None = None
