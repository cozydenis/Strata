"""Tests for the Stadt Zürich GeoJSON parser."""
import json
import pytest
from pathlib import Path

RECON_DIR = Path(__file__).parent.parent.parent / "data" / "recon"


@pytest.fixture
def gebaeude_geojson() -> dict:
    return json.loads((RECON_DIR / "stadt_gebaeude.json").read_text())


@pytest.fixture
def wohnungen_geojson() -> dict:
    return json.loads((RECON_DIR / "stadt_wohnungen.json").read_text())


@pytest.fixture
def eingaenge_geojson() -> dict:
    return json.loads((RECON_DIR / "stadt_eingaenge.json").read_text())


# ── buildings ──────────────────────────────────────────────────────────────────

def test_parse_buildings_returns_list(gebaeude_geojson):
    from strata_api.pipeline.parsers.stadt_parser import parse_buildings

    result = parse_buildings(gebaeude_geojson)
    assert isinstance(result, list)
    assert len(result) > 0


def test_parse_buildings_record_structure(gebaeude_geojson):
    from strata_api.pipeline.parsers.stadt_parser import parse_buildings
    from strata_api.pipeline.schemas import BuildingRecord

    result = parse_buildings(gebaeude_geojson)
    assert all(isinstance(r, BuildingRecord) for r in result)


def test_parse_buildings_egid(gebaeude_geojson):
    from strata_api.pipeline.parsers.stadt_parser import parse_buildings

    result = parse_buildings(gebaeude_geojson)
    first = result[0]
    assert first.egid == 140002


def test_parse_buildings_attribute_codes(gebaeude_geojson):
    from strata_api.pipeline.parsers.stadt_parser import parse_buildings

    result = parse_buildings(gebaeude_geojson)
    first = result[0]
    assert first.gstat == 1004
    assert first.gkat == 1030
    assert first.gklas == 1122
    assert first.gbauj == 1884
    assert first.garea == 106
    assert first.gastw == 6
    assert first.ganzwhg == 4


def test_parse_buildings_coordinates_wgs84(gebaeude_geojson):
    from strata_api.pipeline.parsers.stadt_parser import parse_buildings

    result = parse_buildings(gebaeude_geojson)
    first = result[0]
    # GeoJSON geometry is [lon, lat]
    assert first.lon == pytest.approx(8.544426, abs=0.001)
    assert first.lat == pytest.approx(47.375929, abs=0.001)


def test_parse_buildings_municipality(gebaeude_geojson):
    from strata_api.pipeline.parsers.stadt_parser import parse_buildings

    result = parse_buildings(gebaeude_geojson)
    first = result[0]
    assert first.municipality == "Zürich"
    assert first.municipality_code == 261
    assert first.canton == "ZH"


def test_parse_buildings_data_source_is_stadt(gebaeude_geojson):
    from strata_api.pipeline.parsers.stadt_parser import parse_buildings

    result = parse_buildings(gebaeude_geojson)
    assert all(r.data_source == "stadt" for r in result)


# ── entrances ─────────────────────────────────────────────────────────────────

def test_parse_entrances_returns_list(eingaenge_geojson):
    from strata_api.pipeline.parsers.stadt_parser import parse_entrances

    result = parse_entrances(eingaenge_geojson)
    assert isinstance(result, list)
    assert len(result) > 0


def test_parse_entrances_record_structure(eingaenge_geojson):
    from strata_api.pipeline.parsers.stadt_parser import parse_entrances
    from strata_api.pipeline.schemas import EntranceRecord

    result = parse_entrances(eingaenge_geojson)
    assert all(isinstance(r, EntranceRecord) for r in result)


def test_parse_entrances_egid_edid(eingaenge_geojson):
    from strata_api.pipeline.parsers.stadt_parser import parse_entrances

    result = parse_entrances(eingaenge_geojson)
    first = result[0]
    assert first.egid == 158269
    assert first.edid == 0


def test_parse_entrances_address(eingaenge_geojson):
    from strata_api.pipeline.parsers.stadt_parser import parse_entrances

    result = parse_entrances(eingaenge_geojson)
    first = result[0]
    assert first.strname == "Eschenhaustrasse"
    assert first.deinr == "42"
    assert first.dplz4 == 8053


def test_parse_entrances_coordinates(eingaenge_geojson):
    from strata_api.pipeline.parsers.stadt_parser import parse_entrances

    result = parse_entrances(eingaenge_geojson)
    first = result[0]
    assert first.lon == pytest.approx(8.591809, abs=0.001)
    assert first.lat == pytest.approx(47.365145, abs=0.001)


# ── units ─────────────────────────────────────────────────────────────────────

def test_parse_units_returns_list(wohnungen_geojson):
    from strata_api.pipeline.parsers.stadt_parser import parse_units

    result = parse_units(wohnungen_geojson)
    assert isinstance(result, list)
    assert len(result) > 0


def test_parse_units_record_structure(wohnungen_geojson):
    from strata_api.pipeline.parsers.stadt_parser import parse_units
    from strata_api.pipeline.schemas import UnitRecord

    result = parse_units(wohnungen_geojson)
    assert all(isinstance(r, UnitRecord) for r in result)


def test_parse_units_egid_ewid(wohnungen_geojson):
    from strata_api.pipeline.parsers.stadt_parser import parse_units

    result = parse_units(wohnungen_geojson)
    first = result[0]
    assert first.egid == 140002
    assert first.ewid == 1


def test_parse_units_attributes(wohnungen_geojson):
    from strata_api.pipeline.parsers.stadt_parser import parse_units

    result = parse_units(wohnungen_geojson)
    first = result[0]
    assert first.wstwk == 3101
    assert first.wstwklang == "1. Stock"
    assert first.wazim == 4
    assert first.warea == 66
    assert first.wkche == 1
    assert first.wstat == 3004


def test_parse_units_address(wohnungen_geojson):
    from strata_api.pipeline.parsers.stadt_parser import parse_units

    result = parse_units(wohnungen_geojson)
    first = result[0]
    assert first.strname == "Zähringerstrasse"
    assert first.deinr == "39"
    assert first.dplz4 == 8001


def test_parse_units_coordinates(wohnungen_geojson):
    from strata_api.pipeline.parsers.stadt_parser import parse_units

    result = parse_units(wohnungen_geojson)
    first = result[0]
    assert first.lon == pytest.approx(8.544487, abs=0.001)
    assert first.lat == pytest.approx(47.375898, abs=0.001)
