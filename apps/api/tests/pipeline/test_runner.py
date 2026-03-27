"""Tests for pipeline/runner.py — end-to-end orchestration with mocked I/O."""
import io
from unittest.mock import patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from strata_api.pipeline.schemas import BuildingRecord


@pytest.fixture(scope="module")
def engine():
    from strata_api.db import models  # noqa: F401
    from strata_api.db.base import Base

    eng = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)


_MINI_GEBAEUDE = {
    "features": [{
        "type": "Feature",
        "properties": {
            "egid": 99001, "gstat": 1004, "gkat": 1020, "gklas": 1122,
            "gbauj": 2000, "gabbj": None, "garea": 100, "gastw": 4,
            "ganzwhg": 8, "ggdename": "Zürich", "ggdenr": 261, "gdekt": "ZH",
        },
        "geometry": {"type": "Point", "coordinates": [8.54, 47.38]},
    }]
}

_MINI_EINGAENGE = {
    "features": [{
        "type": "Feature",
        "properties": {
            "egid": 99001, "edid": 0, "strname": "Testgasse", "deinr": "1",
            "dplz4": 8001, "dplzname": "Zürich", "doffadr": 1,
        },
        "geometry": {"type": "Point", "coordinates": [8.54, 47.38]},
    }]
}

_MINI_WOHNUNGEN = {
    "features": [{
        "type": "Feature",
        "properties": {
            "egid": 99001, "ewid": 1, "edid": 0, "wstwk": 3101,
            "wstwklang": "1. Stock", "wazim": 3, "warea": 70,
            "wkche": 1, "wstat": 3004, "wbauj": 2000, "wabbj": None,
            "dplz4": 8001, "dplzname": "Zürich", "strname": "Testgasse", "deinr": "1",
        },
        "geometry": {"type": "Point", "coordinates": [8.54, 47.38]},
    }]
}

_MINI_KANTON_GEBAEUDE = (
    '"Eidgenoessischer_Gebaeudeidentifikator","Kanton","BFS_NR","Gemeindename",'
    '"E-Gebaeudekoordinate","N-Gebaeudekoordinate","Gebaeudestatus_Code",'
    '"Gebaeudekategorie_Code","Gebaeudeklasse_Code","Baujahr_des_Gebaeudes",'
    '"Abbruchjahr_des_Gebaeudes","Gebaeudeflaeche","Anzahl_Geschosse","Anzahl_Wohnungen"\n'
    '88001,"ZH",191,"Wallisellen",2686300.0,1252100.0,1004,1020,1122,1995,,120,4,6\n'
    '99001,"ZH",261,"Zürich",2683111.0,1247945.0,1004,1020,1122,2000,,100,4,8\n'  # overlap
)

_MINI_KANTON_EINGAENGE = (
    '"Eidgenoessischer_Gebaeudeidentifikator","Eidgenoessischer_Eingangsidentifikator",'
    '"Strassenbezeichnung","Eingangsnummer_Gebaeude","Postleitzahl","Postleitzahl-Name",'
    '"E-Eingangskoordinate","N-Eingangskoordinate"\n'
    '88001,0,"Zwicky-Allee","1",8304,"Wallisellen",2686300.0,1252100.0\n'
)

_MINI_KANTON_WOHNUNGEN = (
    '"Eidgenoessischer_Gebaeudeidentifikator","Eidgenoessischer_Wohnungsidentifikator",'
    '"Eidgenoessischer_Eingangsidentifikator","Stockwerk_Code","Stockwerk_Bezeichnung",'
    '"Wohnungsflaeche","Anzahl_Zimmer","Kocheinrichtung_Code","Wohnungsstatus_Code"\n'
    '88001,1,0,3100,"Parterre",90,4,1,3004\n'
)


def test_run_stadt_pipeline_loads_data(engine):
    from strata_api.pipeline.runner import run_stadt_pipeline

    downloads = {
        "gebaeude": _MINI_GEBAEUDE,
        "eingaenge": _MINI_EINGAENGE,
        "wohnungen": _MINI_WOHNUNGEN,
    }

    with patch("strata_api.pipeline.runner.download_geojson", side_effect=lambda url: downloads[
        "wohnungen" if "WOHNUNGEN" in url.upper() else
        "eingaenge" if "EINGAENGE" in url.upper() else
        "gebaeude"
    ]):
        result = run_stadt_pipeline(engine)

    assert result.buildings_upserted >= 1
    assert result.entrances_upserted >= 1
    assert result.units_upserted >= 1
    assert result.status == "completed"
    assert result.run_type == "stadt"


def test_run_kanton_pipeline_excludes_stadt_overlap(engine):

    # First ensure egid 99001 is in DB from Stadt (loaded by previous test or insert directly)
    from strata_api.pipeline.loader import upsert_buildings
    from strata_api.pipeline.runner import run_kanton_pipeline
    upsert_buildings(engine, [BuildingRecord(egid=99001, data_source="stadt")])

    downloads = {
        "gebaeude": _MINI_KANTON_GEBAEUDE,
        "eingaenge": _MINI_KANTON_EINGAENGE,
        "wohnungen": _MINI_KANTON_WOHNUNGEN,
    }

    def _open_csv(url):
        if "gebaeude" in url or "GEBAEUDE" in url:
            return io.StringIO(downloads["gebaeude"])
        elif "eingang" in url or "EINGANG" in url:
            return io.StringIO(downloads["eingaenge"])
        return io.StringIO(downloads["wohnungen"])

    with patch("strata_api.pipeline.runner.download_csv_stream", side_effect=_open_csv):
        result = run_kanton_pipeline(engine)

    assert result.status == "completed"
    assert result.run_type == "kanton"
    # egid 88001 should be loaded (not in Stadt), 99001 should be skipped
    assert result.buildings_upserted == 1  # only 88001


def test_run_stadt_pipeline_records_pipeline_run(engine):
    from strata_api.db.models.pipeline_run import PipelineRun
    from strata_api.pipeline.runner import run_stadt_pipeline

    with patch("strata_api.pipeline.runner.download_geojson", return_value={"features": []}):
        result = run_stadt_pipeline(engine)

    with Session(engine) as s:
        run = s.get(PipelineRun, result.run_id)
        assert run is not None
        assert run.status == "completed"
        assert run.finished_at is not None


def test_run_stadt_pipeline_handles_error(engine):
    from strata_api.pipeline.runner import run_stadt_pipeline

    with patch("strata_api.pipeline.runner.download_geojson", side_effect=RuntimeError("network error")):
        result = run_stadt_pipeline(engine)

    assert result.status == "failed"
    assert "network error" in result.error_message
