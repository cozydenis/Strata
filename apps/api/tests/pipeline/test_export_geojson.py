"""Tests for the GeoJSON buildings export script."""
import datetime
import json
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from strata_api.db.base import Base
from strata_api.db import models  # noqa: F401
from strata_api.db.models.building import Building


@pytest.fixture
def export_engine():
    eng = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(eng)

    now = datetime.datetime.utcnow()
    with Session(eng) as s:
        s.add(Building(
            egid=30001, gkat=1021, gbauj=1980, gastw=3, ganzwhg=6,
            lat=47.376, lon=8.541,
            gstat=1004, municipality="Zürich", municipality_code=261,
            canton="ZH", data_source="stadt", created_at=now, updated_at=now,
        ))
        s.add(Building(
            egid=30002, gkat=1025, gbauj=2015, gastw=5, ganzwhg=10,
            lat=47.391, lon=8.552,
            gstat=1004, municipality="Wallisellen", municipality_code=191,
            canton="ZH", data_source="kanton", created_at=now, updated_at=now,
        ))
        # building with null coords — must be excluded from export
        s.add(Building(
            egid=30003, gkat=1060, gbauj=1965, gastw=2, ganzwhg=0,
            lat=None, lon=None,
            gstat=1004, municipality="Zürich", municipality_code=261,
            canton="ZH", data_source="kanton", created_at=now, updated_at=now,
        ))
        # building with null gbauj — must be included, property should be null
        s.add(Building(
            egid=30004, gkat=1030, gbauj=None, gastw=1, ganzwhg=1,
            lat=47.385, lon=8.546,
            gstat=1004, municipality="Dübendorf", municipality_code=191,
            canton="ZH", data_source="kanton", created_at=now, updated_at=now,
        ))
        s.commit()
    yield eng
    Base.metadata.drop_all(eng)


def test_export_returns_feature_collection(export_engine):
    from strata_api.scripts.export_buildings_geojson import export_buildings_geojson

    result = export_buildings_geojson(export_engine)
    assert result["type"] == "FeatureCollection"
    assert "features" in result


def test_export_excludes_null_coordinate_buildings(export_engine):
    from strata_api.scripts.export_buildings_geojson import export_buildings_geojson

    result = export_buildings_geojson(export_engine)
    egids = [f["properties"]["egid"] for f in result["features"]]
    assert 30003 not in egids  # lat=None, lon=None → excluded


def test_export_includes_all_geolocated_buildings(export_engine):
    from strata_api.scripts.export_buildings_geojson import export_buildings_geojson

    result = export_buildings_geojson(export_engine)
    egids = {f["properties"]["egid"] for f in result["features"]}
    assert 30001 in egids
    assert 30002 in egids
    assert 30004 in egids


def test_export_feature_has_point_geometry(export_engine):
    from strata_api.scripts.export_buildings_geojson import export_buildings_geojson

    result = export_buildings_geojson(export_engine)
    feature = next(f for f in result["features"] if f["properties"]["egid"] == 30001)
    assert feature["type"] == "Feature"
    geom = feature["geometry"]
    assert geom["type"] == "Point"
    # GeoJSON uses [lon, lat] order
    assert geom["coordinates"] == pytest.approx([8.541, 47.376], abs=1e-5)


def test_export_feature_has_exactly_five_properties(export_engine):
    from strata_api.scripts.export_buildings_geojson import export_buildings_geojson

    result = export_buildings_geojson(export_engine)
    for feature in result["features"]:
        props = feature["properties"]
        assert set(props.keys()) == {"egid", "gbauj", "gkat", "gastw", "ganzwhg"}, (
            f"Expected exactly 5 properties, got: {set(props.keys())}"
        )


def test_export_null_gbauj_preserved(export_engine):
    from strata_api.scripts.export_buildings_geojson import export_buildings_geojson

    result = export_buildings_geojson(export_engine)
    feature = next(f for f in result["features"] if f["properties"]["egid"] == 30004)
    assert feature["properties"]["gbauj"] is None


def test_export_is_valid_json(export_engine):
    from strata_api.scripts.export_buildings_geojson import export_buildings_geojson

    result = export_buildings_geojson(export_engine)
    # round-trip through JSON to verify serializability
    dumped = json.dumps(result)
    parsed = json.loads(dumped)
    assert parsed["type"] == "FeatureCollection"
