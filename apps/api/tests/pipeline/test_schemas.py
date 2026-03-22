"""Tests for Pydantic intermediate schemas (pipeline/schemas.py)."""
import pytest
from pydantic import ValidationError


def test_building_record_valid():
    from strata_api.pipeline.schemas import BuildingRecord

    b = BuildingRecord(
        egid=123456,
        gstat=1004,
        gkat=1020,
        gklas=1122,
        gbauj=1980,
        gabbj=None,
        garea=150,
        gastw=3,
        ganzwhg=4,
        lat=47.376,
        lon=8.541,
        municipality="Zürich",
        municipality_code=261,
        canton="ZH",
        data_source="stadt",
    )
    assert b.egid == 123456
    assert b.canton == "ZH"


def test_building_record_requires_egid():
    from strata_api.pipeline.schemas import BuildingRecord

    with pytest.raises(ValidationError):
        BuildingRecord(lat=47.0, lon=8.0, data_source="stadt")  # type: ignore


def test_building_record_requires_data_source():
    from strata_api.pipeline.schemas import BuildingRecord

    with pytest.raises(ValidationError):
        BuildingRecord(egid=1)  # type: ignore


def test_building_record_optional_fields_default_none():
    from strata_api.pipeline.schemas import BuildingRecord

    b = BuildingRecord(egid=1, data_source="kanton")
    assert b.gstat is None
    assert b.lat is None
    assert b.municipality is None


def test_building_record_is_frozen():
    from strata_api.pipeline.schemas import BuildingRecord

    b = BuildingRecord(egid=1, data_source="stadt")
    with pytest.raises(Exception):
        b.egid = 99  # type: ignore


def test_entrance_record_valid():
    from strata_api.pipeline.schemas import EntranceRecord

    e = EntranceRecord(
        egid=123456,
        edid=0,
        strname="Quellenstrasse",
        deinr="17",
        dplz4=8005,
        dplzname="Zürich",
        lat=47.376,
        lon=8.541,
        data_source="stadt",
    )
    assert e.egid == 123456
    assert e.deinr == "17"


def test_entrance_record_requires_egid_and_edid():
    from strata_api.pipeline.schemas import EntranceRecord

    with pytest.raises(ValidationError):
        EntranceRecord(data_source="stadt")  # type: ignore


def test_entrance_record_is_frozen():
    from strata_api.pipeline.schemas import EntranceRecord

    e = EntranceRecord(egid=1, edid=0, data_source="kanton")
    with pytest.raises(Exception):
        e.egid = 2  # type: ignore


def test_unit_record_valid():
    from strata_api.pipeline.schemas import UnitRecord

    u = UnitRecord(
        egid=123456,
        ewid=1,
        edid=0,
        wstwk=3100,
        wstwklang="Parterre",
        wazim=3,
        warea=75,
        wkche=1,
        wstat=3004,
        wbauj=1990,
        wabbj=None,
        dplz4=8005,
        dplzname="Zürich",
        strname="Quellenstrasse",
        deinr="17",
        lat=47.376,
        lon=8.541,
        data_source="stadt",
    )
    assert u.ewid == 1
    assert u.wazim == 3


def test_unit_record_requires_egid_and_ewid():
    from strata_api.pipeline.schemas import UnitRecord

    with pytest.raises(ValidationError):
        UnitRecord(data_source="stadt")  # type: ignore


def test_unit_record_is_frozen():
    from strata_api.pipeline.schemas import UnitRecord

    u = UnitRecord(egid=1, ewid=1, data_source="kanton")
    with pytest.raises(Exception):
        u.egid = 2  # type: ignore


def test_unit_record_optional_fields_default_none():
    from strata_api.pipeline.schemas import UnitRecord

    u = UnitRecord(egid=1, ewid=1, data_source="kanton")
    assert u.wazim is None
    assert u.lat is None
    assert u.strname is None
