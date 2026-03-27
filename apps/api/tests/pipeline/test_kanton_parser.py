"""Tests for the Kanton Zürich CSV parser."""
import io
from pathlib import Path

RECON_DIR = Path(__file__).parent.parent.parent / "data" / "recon"


def _csv_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


# ── buildings ──────────────────────────────────────────────────────────────────

def test_parse_buildings_from_csv_returns_list():
    from strata_api.pipeline.parsers.kanton_parser import parse_buildings_csv

    text = _csv_text(RECON_DIR / "kanton_gebaeude_sample.csv")
    result = list(parse_buildings_csv(io.StringIO(text)))
    assert isinstance(result, list)
    assert len(result) > 0


def test_parse_buildings_csv_record_structure():
    from strata_api.pipeline.parsers.kanton_parser import parse_buildings_csv
    from strata_api.pipeline.schemas import BuildingRecord

    text = _csv_text(RECON_DIR / "kanton_gebaeude_sample.csv")
    result = list(parse_buildings_csv(io.StringIO(text)))
    assert all(isinstance(r, BuildingRecord) for r in result)


def test_parse_buildings_csv_egid():
    from strata_api.pipeline.parsers.kanton_parser import parse_buildings_csv

    text = _csv_text(RECON_DIR / "kanton_gebaeude_sample.csv")
    result = list(parse_buildings_csv(io.StringIO(text)))
    first = result[0]
    assert first.egid == 5109


def test_parse_buildings_csv_attribute_codes():
    from strata_api.pipeline.parsers.kanton_parser import parse_buildings_csv

    text = _csv_text(RECON_DIR / "kanton_gebaeude_sample.csv")
    result = list(parse_buildings_csv(io.StringIO(text)))
    first = result[0]
    assert first.gstat == 1004
    assert first.gbauj == 1880
    assert first.garea == 86
    assert first.gastw == 3
    assert first.ganzwhg == 3


def test_parse_buildings_csv_coordinates_converted_to_wgs84():
    from strata_api.pipeline.parsers.kanton_parser import parse_buildings_csv

    text = _csv_text(RECON_DIR / "kanton_gebaeude_sample.csv")
    result = list(parse_buildings_csv(io.StringIO(text)))
    first = result[0]
    # LV95: E=2673576, N=1235131 → should be in Switzerland
    assert first.lat is not None
    assert first.lon is not None
    assert 45.8 < first.lat < 47.9
    assert 5.9 < first.lon < 10.6


def test_parse_buildings_csv_municipality():
    from strata_api.pipeline.parsers.kanton_parser import parse_buildings_csv

    text = _csv_text(RECON_DIR / "kanton_gebaeude_sample.csv")
    result = list(parse_buildings_csv(io.StringIO(text)))
    first = result[0]
    assert first.municipality == "Obfelden"
    assert first.municipality_code == 10
    assert first.canton == "ZH"


def test_parse_buildings_csv_data_source_is_kanton():
    from strata_api.pipeline.parsers.kanton_parser import parse_buildings_csv

    text = _csv_text(RECON_DIR / "kanton_gebaeude_sample.csv")
    result = list(parse_buildings_csv(io.StringIO(text)))
    assert all(r.data_source == "kanton" for r in result)


# ── entrances ─────────────────────────────────────────────────────────────────

def test_parse_entrances_csv_returns_list():
    from strata_api.pipeline.parsers.kanton_parser import parse_entrances_csv

    text = _csv_text(RECON_DIR / "kanton_eingaenge_sample.csv")
    result = list(parse_entrances_csv(io.StringIO(text)))
    assert isinstance(result, list)
    assert len(result) > 0


def test_parse_entrances_csv_record_structure():
    from strata_api.pipeline.parsers.kanton_parser import parse_entrances_csv
    from strata_api.pipeline.schemas import EntranceRecord

    text = _csv_text(RECON_DIR / "kanton_eingaenge_sample.csv")
    result = list(parse_entrances_csv(io.StringIO(text)))
    assert all(isinstance(r, EntranceRecord) for r in result)


def test_parse_entrances_csv_egid_edid():
    from strata_api.pipeline.parsers.kanton_parser import parse_entrances_csv

    text = _csv_text(RECON_DIR / "kanton_eingaenge_sample.csv")
    result = list(parse_entrances_csv(io.StringIO(text)))
    first = result[0]
    assert first.egid == 5577
    assert first.edid == 0


def test_parse_entrances_csv_address():
    from strata_api.pipeline.parsers.kanton_parser import parse_entrances_csv

    text = _csv_text(RECON_DIR / "kanton_eingaenge_sample.csv")
    result = list(parse_entrances_csv(io.StringIO(text)))
    first = result[0]
    assert first.strname == "Rickenbacherstrasse"
    assert first.deinr == "19"
    assert first.dplz4 == 8913


def test_parse_entrances_csv_coordinates_wgs84():
    from strata_api.pipeline.parsers.kanton_parser import parse_entrances_csv

    text = _csv_text(RECON_DIR / "kanton_eingaenge_sample.csv")
    result = list(parse_entrances_csv(io.StringIO(text)))
    first = result[0]
    assert first.lat is not None
    assert first.lon is not None
    assert 45.8 < first.lat < 47.9
    assert 5.9 < first.lon < 10.6


# ── units ─────────────────────────────────────────────────────────────────────

def test_parse_units_csv_returns_list():
    from strata_api.pipeline.parsers.kanton_parser import parse_units_csv

    text = _csv_text(RECON_DIR / "kanton_wohnungen_sample.csv")
    result = list(parse_units_csv(io.StringIO(text)))
    assert isinstance(result, list)
    assert len(result) > 0


def test_parse_units_csv_record_structure():
    from strata_api.pipeline.parsers.kanton_parser import parse_units_csv
    from strata_api.pipeline.schemas import UnitRecord

    text = _csv_text(RECON_DIR / "kanton_wohnungen_sample.csv")
    result = list(parse_units_csv(io.StringIO(text)))
    assert all(isinstance(r, UnitRecord) for r in result)


def test_parse_units_csv_egid_ewid():
    from strata_api.pipeline.parsers.kanton_parser import parse_units_csv

    text = _csv_text(RECON_DIR / "kanton_wohnungen_sample.csv")
    result = list(parse_units_csv(io.StringIO(text)))
    first = result[0]
    assert first.egid == 4711
    assert first.ewid == 1


def test_parse_units_csv_attributes():
    from strata_api.pipeline.parsers.kanton_parser import parse_units_csv

    text = _csv_text(RECON_DIR / "kanton_wohnungen_sample.csv")
    result = list(parse_units_csv(io.StringIO(text)))
    first = result[0]
    assert first.wstwk == 3100
    assert first.wstwklang == "Parterre inkl. Hochparterre"
    assert first.warea == 144
    assert first.wazim == 5
    assert first.wkche == 1
    assert first.wstat == 3007
