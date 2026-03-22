"""Parse Stadt Zürich GWR GeoJSON feature collections into normalised schemas."""
from __future__ import annotations

from strata_api.pipeline.schemas import BuildingRecord, EntranceRecord, UnitRecord
from strata_api.pipeline.transform import parse_optional_int

_SOURCE = "stadt"


def parse_buildings(geojson: dict) -> list[BuildingRecord]:
    """Parse a GWR_STZH_GEBAEUDE GeoJSON feature collection."""
    records: list[BuildingRecord] = []
    for feature in geojson.get("features", []):
        props = feature.get("properties") or {}
        coords = (feature.get("geometry") or {}).get("coordinates") or []
        lon = float(coords[0]) if len(coords) >= 2 else None
        lat = float(coords[1]) if len(coords) >= 2 else None

        records.append(BuildingRecord(
            egid=int(props["egid"]),
            data_source=_SOURCE,
            gstat=parse_optional_int(props.get("gstat")),
            gkat=parse_optional_int(props.get("gkat")),
            gklas=parse_optional_int(props.get("gklas")),
            gbauj=parse_optional_int(props.get("gbauj")),
            gabbj=parse_optional_int(props.get("gabbj")),
            garea=parse_optional_int(props.get("garea")),
            gastw=parse_optional_int(props.get("gastw")),
            ganzwhg=parse_optional_int(props.get("ganzwhg")),
            lat=lat,
            lon=lon,
            municipality=props.get("ggdename"),
            municipality_code=parse_optional_int(props.get("ggdenr")),
            canton=props.get("gdekt"),
        ))
    return records


def parse_entrances(geojson: dict) -> list[EntranceRecord]:
    """Parse a GWR_STZH_GEBAEUDEEINGAENGE GeoJSON feature collection."""
    records: list[EntranceRecord] = []
    for feature in geojson.get("features", []):
        props = feature.get("properties") or {}
        coords = (feature.get("geometry") or {}).get("coordinates") or []
        lon = float(coords[0]) if len(coords) >= 2 else None
        lat = float(coords[1]) if len(coords) >= 2 else None

        records.append(EntranceRecord(
            egid=int(props["egid"]),
            edid=int(props["edid"]),
            data_source=_SOURCE,
            strname=props.get("strname"),
            deinr=str(props["deinr"]) if props.get("deinr") is not None else None,
            dplz4=parse_optional_int(props.get("dplz4")),
            dplzname=props.get("dplzname"),
            doffadr=parse_optional_int(props.get("doffadr")),
            lat=lat,
            lon=lon,
        ))
    return records


def parse_units(geojson: dict) -> list[UnitRecord]:
    """Parse a GWR_STZH_WOHNUNGEN GeoJSON feature collection."""
    records: list[UnitRecord] = []
    for feature in geojson.get("features", []):
        props = feature.get("properties") or {}
        coords = (feature.get("geometry") or {}).get("coordinates") or []
        lon = float(coords[0]) if len(coords) >= 2 else None
        lat = float(coords[1]) if len(coords) >= 2 else None

        records.append(UnitRecord(
            egid=int(props["egid"]),
            ewid=int(props["ewid"]),
            data_source=_SOURCE,
            edid=parse_optional_int(props.get("edid")),
            wstwk=parse_optional_int(props.get("wstwk")),
            wstwklang=props.get("wstwklang"),
            wazim=parse_optional_int(props.get("wazim")),
            warea=parse_optional_int(props.get("warea")),
            wkche=parse_optional_int(props.get("wkche")),
            wstat=parse_optional_int(props.get("wstat")),
            wbauj=parse_optional_int(props.get("wbauj")),
            wabbj=parse_optional_int(props.get("wabbj")),
            dplz4=parse_optional_int(props.get("dplz4")),
            dplzname=props.get("dplzname"),
            strname=props.get("strname"),
            deinr=str(props["deinr"]) if props.get("deinr") is not None else None,
            lat=lat,
            lon=lon,
        ))
    return records
