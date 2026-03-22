"""Tests for pipeline/transform.py — LV95 (EPSG:2056) → WGS84 (EPSG:4326)."""
import pytest


def test_lv95_to_wgs84_zwicky_areal():
    """Zwicky Areal, Dübendorf/Wallisellen — well-known reference point."""
    from strata_api.pipeline.transform import lv95_to_wgs84

    lat, lon = lv95_to_wgs84(e=2686300.0, n=1252100.0)
    # Approximate expected coordinates for Zwicky Areal area
    assert lat == pytest.approx(47.405, abs=0.01)
    assert lon == pytest.approx(8.582, abs=0.01)


def test_lv95_to_wgs84_zurich_hb():
    """Zürich Hauptbahnhof — well-known reference point."""
    from strata_api.pipeline.transform import lv95_to_wgs84

    lat, lon = lv95_to_wgs84(e=2683111.0, n=1247945.0)
    assert lat == pytest.approx(47.378, abs=0.005)
    assert lon == pytest.approx(8.540, abs=0.005)


def test_lv95_to_wgs84_returns_floats():
    from strata_api.pipeline.transform import lv95_to_wgs84

    lat, lon = lv95_to_wgs84(e=2683111.0, n=1247945.0)
    assert isinstance(lat, float)
    assert isinstance(lon, float)


def test_lv95_to_wgs84_lat_in_switzerland_range():
    from strata_api.pipeline.transform import lv95_to_wgs84

    lat, lon = lv95_to_wgs84(e=2683111.0, n=1247945.0)
    assert 45.8 < lat < 47.9   # Switzerland latitude range
    assert 5.9 < lon < 10.6    # Switzerland longitude range


def test_lv95_to_wgs84_none_returns_none_pair():
    """If either coordinate is None, return (None, None)."""
    from strata_api.pipeline.transform import lv95_to_wgs84

    lat, lon = lv95_to_wgs84(e=None, n=1247945.0)
    assert lat is None
    assert lon is None

    lat, lon = lv95_to_wgs84(e=2683111.0, n=None)
    assert lat is None
    assert lon is None

    lat, lon = lv95_to_wgs84(e=None, n=None)
    assert lat is None
    assert lon is None


def test_parse_optional_int():
    from strata_api.pipeline.transform import parse_optional_int

    assert parse_optional_int("1980") == 1980
    assert parse_optional_int("") is None
    assert parse_optional_int(None) is None
    assert parse_optional_int("abc") is None
    assert parse_optional_int(42) == 42


def test_parse_optional_float():
    from strata_api.pipeline.transform import parse_optional_float

    assert parse_optional_float("47.376") == pytest.approx(47.376)
    assert parse_optional_float("") is None
    assert parse_optional_float(None) is None
    assert parse_optional_float("xyz") is None
    assert parse_optional_float(8.541) == pytest.approx(8.541)
