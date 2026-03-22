"""Parse Kanton Zürich GWR CSV files into normalised schemas.

CSV files use semicolons for quotes but commas as delimiter (standard CSV).
Streams rows to avoid loading large files into memory.
"""
from __future__ import annotations

import csv
from typing import IO, Iterator

from strata_api.pipeline.schemas import BuildingRecord, EntranceRecord, UnitRecord
from strata_api.pipeline.transform import lv95_to_wgs84, parse_optional_int

_SOURCE = "kanton"


def parse_buildings_csv(file: IO[str]) -> Iterator[BuildingRecord]:
    """Yield BuildingRecord objects from a Kanton GWR buildings CSV stream."""
    reader = csv.DictReader(file)
    for row in reader:
        e_coord = _float_or_none(row.get("E-Gebaeudekoordinate"))
        n_coord = _float_or_none(row.get("N-Gebaeudekoordinate"))
        lat, lon = lv95_to_wgs84(e_coord, n_coord)

        yield BuildingRecord(
            egid=int(row["Eidgenoessischer_Gebaeudeidentifikator"]),
            data_source=_SOURCE,
            gstat=parse_optional_int(row.get("Gebaeudestatus_Code")),
            gkat=parse_optional_int(row.get("Gebaeudekategorie_Code")),
            gklas=parse_optional_int(row.get("Gebaeudeklasse_Code")),
            gbauj=parse_optional_int(row.get("Baujahr_des_Gebaeudes")),
            gabbj=parse_optional_int(row.get("Abbruchjahr_des_Gebaeudes")),
            garea=parse_optional_int(row.get("Gebaeudeflaeche")),
            gastw=parse_optional_int(row.get("Anzahl_Geschosse")),
            ganzwhg=parse_optional_int(row.get("Anzahl_Wohnungen")),
            lat=lat,
            lon=lon,
            municipality=row.get("Gemeindename") or None,
            municipality_code=parse_optional_int(row.get("BFS_NR")),
            canton=row.get("Kanton") or None,
        )


def parse_entrances_csv(file: IO[str]) -> Iterator[EntranceRecord]:
    """Yield EntranceRecord objects from a Kanton GWR entrances CSV stream."""
    reader = csv.DictReader(file)
    for row in reader:
        e_coord = _float_or_none(row.get("E-Eingangskoordinate"))
        n_coord = _float_or_none(row.get("N-Eingangskoordinate"))
        lat, lon = lv95_to_wgs84(e_coord, n_coord)

        deinr_raw = row.get("Eingangsnummer_Gebaeude")
        yield EntranceRecord(
            egid=int(row["Eidgenoessischer_Gebaeudeidentifikator"]),
            edid=int(row["Eidgenoessischer_Eingangsidentifikator"]),
            data_source=_SOURCE,
            strname=row.get("Strassenbezeichnung") or None,
            deinr=str(deinr_raw) if deinr_raw else None,
            dplz4=parse_optional_int(row.get("Postleitzahl")),
            dplzname=row.get("Postleitzahl-Name") or None,
            lat=lat,
            lon=lon,
        )


def parse_units_csv(file: IO[str]) -> Iterator[UnitRecord]:
    """Yield UnitRecord objects from a Kanton GWR dwellings CSV stream."""
    reader = csv.DictReader(file)
    for row in reader:
        yield UnitRecord(
            egid=int(row["Eidgenoessischer_Gebaeudeidentifikator"]),
            ewid=int(row["Eidgenoessischer_Wohnungsidentifikator"]),
            data_source=_SOURCE,
            edid=parse_optional_int(row.get("Eidgenoessischer_Eingangsidentifikator")),
            wstwk=parse_optional_int(row.get("Stockwerk_Code")),
            wstwklang=row.get("Stockwerk_Bezeichnung") or None,
            wazim=parse_optional_int(row.get("Anzahl_Zimmer")),
            warea=parse_optional_int(row.get("Wohnungsflaeche")),
            wkche=parse_optional_int(row.get("Kocheinrichtung_Code")),
            wstat=parse_optional_int(row.get("Wohnungsstatus_Code")),
            wbauj=parse_optional_int(row.get("Baujahr_der_Wohnung")),
            wabbj=parse_optional_int(row.get("Abbruchjahr_der_Wohnung")),
        )


def _float_or_none(value: str | None) -> float | None:
    if not value:
        return None
    try:
        return float(value.strip())
    except ValueError:
        return None
