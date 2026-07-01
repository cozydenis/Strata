"""TDD tests for neighborhood pipeline runner — written BEFORE implementation (RED phase)."""
from __future__ import annotations

import json
from unittest.mock import patch

NOISE_GEOJSON: dict = {"type": "FeatureCollection", "features": []}

CONSTRUCTION_CSV = (
    '"StichtagDatJahr","DatenstandCd","QuarSort","QuarCd","QuarLang","KreisSort","KreisCd","KreisLang",'
    '"ProjektStatusSSZPubl1Sort","ProjektStatusSSZPubl1Cd","ProjektStatusSSZPubl1Lang",'
    '"ArtArbeitenSort","ArtArbeitenCd","ArtArbeitenLang","AnzBauprojekte","BaukostenEffektiv"\n'
    '2025,"D",11,"011","Rathaus",1,"1","Kreis 1",2,"2","Bewilligt harmonisiert",1,"N","Neubau",3,45000\n'
)

QUARTIER_GEOJSON = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {"type": "Polygon", "coordinates": [[[8.53, 47.37], [8.54, 47.37], [8.54, 47.38], [8.53, 47.37]]]},
            "properties": {"objectid": 1, "qnr": 11, "qname": "Rathaus", "knr": 1, "kname": "Kreis 1", "geometrie_gdo": None},
        }
    ],
}

DEMO_CSV = (
    "StichtagDatJahr,AlterVSort,AlterVCd,AlterV05Sort,AlterV05Cd,AlterV05Kurz,"
    "AlterV10Cd,AlterV10Kurz,AlterV20Cd,AlterV20Kurz,SexCd,SexLang,SexKurz,"
    "KreisCd,KreisLang,QuarSort,QuarCd,QuarLang,HerkunftSort,HerkunftCd,HerkunftLang,AnzBestWir\n"
    '2023,0,"0",1,"0","0-4","0","0-9","0","0-19","1","männlich","M","1","Kreis 1",'
    '11,"011","Rathaus",1,"1","Schweizer*in",500\n'
)


class TestRunNeighborhoodPipeline:
    """Tests for run_neighborhood_pipeline."""

    def test_function_is_importable(self):
        from strata_api.pipeline.neighborhoods.runner import run_neighborhood_pipeline  # noqa: F401

    def test_returns_stats_dict(self, tmp_path):
        from strata_api.pipeline.neighborhoods.runner import run_neighborhood_pipeline

        with (
            patch("strata_api.pipeline.neighborhoods.runner.download_quartier_geojson", return_value=QUARTIER_GEOJSON),
            patch("strata_api.pipeline.neighborhoods.runner.download_demographics_csv", return_value=DEMO_CSV),
            patch("strata_api.pipeline.neighborhoods.runner.download_noise_geojson", return_value=NOISE_GEOJSON),
            patch("strata_api.pipeline.neighborhoods.runner.download_construction_csv", return_value=CONSTRUCTION_CSV),
        ):
            stats = run_neighborhood_pipeline(tmp_path)

        assert isinstance(stats, dict)

    def test_stats_contains_quartiere_count(self, tmp_path):
        from strata_api.pipeline.neighborhoods.runner import run_neighborhood_pipeline

        with (
            patch("strata_api.pipeline.neighborhoods.runner.download_quartier_geojson", return_value=QUARTIER_GEOJSON),
            patch("strata_api.pipeline.neighborhoods.runner.download_demographics_csv", return_value=DEMO_CSV),
            patch("strata_api.pipeline.neighborhoods.runner.download_noise_geojson", return_value=NOISE_GEOJSON),
            patch("strata_api.pipeline.neighborhoods.runner.download_construction_csv", return_value=CONSTRUCTION_CSV),
        ):
            stats = run_neighborhood_pipeline(tmp_path)

        assert "quartiere" in stats
        assert stats["quartiere"] == 1

    def test_stats_contains_year(self, tmp_path):
        from strata_api.pipeline.neighborhoods.runner import run_neighborhood_pipeline

        with (
            patch("strata_api.pipeline.neighborhoods.runner.download_quartier_geojson", return_value=QUARTIER_GEOJSON),
            patch("strata_api.pipeline.neighborhoods.runner.download_demographics_csv", return_value=DEMO_CSV),
            patch("strata_api.pipeline.neighborhoods.runner.download_noise_geojson", return_value=NOISE_GEOJSON),
            patch("strata_api.pipeline.neighborhoods.runner.download_construction_csv", return_value=CONSTRUCTION_CSV),
        ):
            stats = run_neighborhood_pipeline(tmp_path)

        assert "year" in stats
        assert stats["year"] == 2023

    def test_writes_quartiere_geojson_file(self, tmp_path):
        from strata_api.pipeline.neighborhoods.runner import run_neighborhood_pipeline

        with (
            patch("strata_api.pipeline.neighborhoods.runner.download_quartier_geojson", return_value=QUARTIER_GEOJSON),
            patch("strata_api.pipeline.neighborhoods.runner.download_demographics_csv", return_value=DEMO_CSV),
            patch("strata_api.pipeline.neighborhoods.runner.download_noise_geojson", return_value=NOISE_GEOJSON),
            patch("strata_api.pipeline.neighborhoods.runner.download_construction_csv", return_value=CONSTRUCTION_CSV),
        ):
            run_neighborhood_pipeline(tmp_path)

        output_file = tmp_path / "quartiere.geojson"
        assert output_file.exists()

    def test_geojson_output_is_valid(self, tmp_path):
        from strata_api.pipeline.neighborhoods.runner import run_neighborhood_pipeline

        with (
            patch("strata_api.pipeline.neighborhoods.runner.download_quartier_geojson", return_value=QUARTIER_GEOJSON),
            patch("strata_api.pipeline.neighborhoods.runner.download_demographics_csv", return_value=DEMO_CSV),
            patch("strata_api.pipeline.neighborhoods.runner.download_noise_geojson", return_value=NOISE_GEOJSON),
            patch("strata_api.pipeline.neighborhoods.runner.download_construction_csv", return_value=CONSTRUCTION_CSV),
        ):
            run_neighborhood_pipeline(tmp_path)

        output = json.loads((tmp_path / "quartiere.geojson").read_text())
        assert output["type"] == "FeatureCollection"
        assert len(output["features"]) == 1

    def test_geojson_features_have_demographic_properties(self, tmp_path):
        from strata_api.pipeline.neighborhoods.runner import run_neighborhood_pipeline

        with (
            patch("strata_api.pipeline.neighborhoods.runner.download_quartier_geojson", return_value=QUARTIER_GEOJSON),
            patch("strata_api.pipeline.neighborhoods.runner.download_demographics_csv", return_value=DEMO_CSV),
            patch("strata_api.pipeline.neighborhoods.runner.download_noise_geojson", return_value=NOISE_GEOJSON),
            patch("strata_api.pipeline.neighborhoods.runner.download_construction_csv", return_value=CONSTRUCTION_CSV),
        ):
            run_neighborhood_pipeline(tmp_path)

        output = json.loads((tmp_path / "quartiere.geojson").read_text())
        props = output["features"][0]["properties"]
        assert "total_population" in props
        assert "swiss_pct" in props
        assert "trend" in props

    def test_output_dir_created_if_missing(self, tmp_path):
        from strata_api.pipeline.neighborhoods.runner import run_neighborhood_pipeline

        nested_dir = tmp_path / "nested" / "output"

        with (
            patch("strata_api.pipeline.neighborhoods.runner.download_quartier_geojson", return_value=QUARTIER_GEOJSON),
            patch("strata_api.pipeline.neighborhoods.runner.download_demographics_csv", return_value=DEMO_CSV),
            patch("strata_api.pipeline.neighborhoods.runner.download_noise_geojson", return_value=NOISE_GEOJSON),
            patch("strata_api.pipeline.neighborhoods.runner.download_construction_csv", return_value=CONSTRUCTION_CSV),
        ):
            run_neighborhood_pipeline(nested_dir)

        assert (nested_dir / "quartiere.geojson").exists()

    def test_downloads_are_called(self, tmp_path):
        """Verifies downloader functions are actually called."""
        from strata_api.pipeline.neighborhoods.runner import run_neighborhood_pipeline

        with (
            patch("strata_api.pipeline.neighborhoods.runner.download_quartier_geojson", return_value=QUARTIER_GEOJSON) as mock_q,
            patch("strata_api.pipeline.neighborhoods.runner.download_demographics_csv", return_value=DEMO_CSV) as mock_d,
            patch("strata_api.pipeline.neighborhoods.runner.download_noise_geojson", return_value=NOISE_GEOJSON) as mock_n,
        ):
            run_neighborhood_pipeline(tmp_path)

        mock_q.assert_called_once()
        mock_d.assert_called_once()
        mock_n.assert_called_once()


OVERPASS_RAW = {
    "elements": [
        # Inside the Rathaus fixture polygon
        {"type": "node", "id": 1, "lat": 47.372, "lon": 8.535, "tags": {"amenity": "cafe", "name": "C"}},
        # Outside every quartier
        {"type": "node", "id": 2, "lat": 47.50, "lon": 8.70, "tags": {"amenity": "cafe"}},
    ]
}


class TestRunnerAmenities:
    def test_amenities_skipped_by_default(self, tmp_path):
        from strata_api.pipeline.neighborhoods.runner import run_neighborhood_pipeline

        with (
            patch("strata_api.pipeline.neighborhoods.runner.download_quartier_geojson", return_value=QUARTIER_GEOJSON),
            patch("strata_api.pipeline.neighborhoods.runner.download_demographics_csv", return_value=DEMO_CSV),
            patch("strata_api.pipeline.neighborhoods.runner.download_noise_geojson", return_value=NOISE_GEOJSON),
            patch("strata_api.pipeline.neighborhoods.runner.download_construction_csv", return_value=CONSTRUCTION_CSV),
        ):
            stats = run_neighborhood_pipeline(tmp_path)
        assert stats["amenities"] is None
        geojson = json.loads((tmp_path / "quartiere.geojson").read_text())
        assert geojson["features"][0]["properties"]["amenities"] is None

    def test_cached_amenities_raw_reused(self, tmp_path):
        from strata_api.pipeline.neighborhoods.runner import run_neighborhood_pipeline

        (tmp_path / "amenities_raw.json").write_text(json.dumps(OVERPASS_RAW))
        with (
            patch("strata_api.pipeline.neighborhoods.runner.download_quartier_geojson", return_value=QUARTIER_GEOJSON),
            patch("strata_api.pipeline.neighborhoods.runner.download_demographics_csv", return_value=DEMO_CSV),
            patch("strata_api.pipeline.neighborhoods.runner.download_noise_geojson", return_value=NOISE_GEOJSON),
            patch("strata_api.pipeline.neighborhoods.runner.download_construction_csv", return_value=CONSTRUCTION_CSV),
        ):
            stats = run_neighborhood_pipeline(tmp_path)
        assert stats["amenities"] == 1  # only the in-polygon cafe counts
        geojson = json.loads((tmp_path / "quartiere.geojson").read_text())
        amenities = geojson["features"][0]["properties"]["amenities"]
        assert amenities["cafes"] == 1
        assert amenities["total"] == 1

    def test_fetch_amenities_calls_overpass_and_caches(self, tmp_path):
        from strata_api.pipeline.neighborhoods.runner import run_neighborhood_pipeline

        with (
            patch("strata_api.pipeline.neighborhoods.runner.download_quartier_geojson", return_value=QUARTIER_GEOJSON),
            patch("strata_api.pipeline.neighborhoods.runner.download_demographics_csv", return_value=DEMO_CSV),
            patch("strata_api.pipeline.neighborhoods.runner.download_noise_geojson", return_value=NOISE_GEOJSON),
            patch("strata_api.pipeline.neighborhoods.runner.download_construction_csv", return_value=CONSTRUCTION_CSV),
            patch("strata_api.pipeline.neighborhoods.runner.fetch_overpass_amenities", return_value=OVERPASS_RAW) as mock_fetch,
        ):
            stats = run_neighborhood_pipeline(tmp_path, fetch_amenities=True)
        mock_fetch.assert_called_once()
        assert stats["amenities"] == 1
        assert (tmp_path / "amenities_raw.json").exists()


GREEN_RAW = {
    "elements": [
        # A park whose vertices sit inside the Rathaus fixture polygon
        {
            "type": "way",
            "id": 1,
            "tags": {"leisure": "park", "name": "Fixture Park"},
            "geometry": [
                {"lat": 47.3705, "lon": 8.5305},
                {"lat": 47.3705, "lon": 8.5315},
                {"lat": 47.3715, "lon": 8.5315},
                {"lat": 47.3705, "lon": 8.5305},
            ],
        },
        # A forest well outside every quartier -> dropped
        {
            "type": "way",
            "id": 2,
            "tags": {"landuse": "forest"},
            "geometry": [
                {"lat": 47.50, "lon": 8.70},
                {"lat": 47.50, "lon": 8.71},
                {"lat": 47.51, "lon": 8.71},
                {"lat": 47.50, "lon": 8.70},
            ],
        },
    ]
}


class TestRunnerGreen:
    def test_green_skipped_by_default(self, tmp_path):
        from strata_api.pipeline.neighborhoods.runner import run_neighborhood_pipeline

        with (
            patch("strata_api.pipeline.neighborhoods.runner.download_quartier_geojson", return_value=QUARTIER_GEOJSON),
            patch("strata_api.pipeline.neighborhoods.runner.download_demographics_csv", return_value=DEMO_CSV),
            patch("strata_api.pipeline.neighborhoods.runner.download_noise_geojson", return_value=NOISE_GEOJSON),
            patch("strata_api.pipeline.neighborhoods.runner.download_construction_csv", return_value=CONSTRUCTION_CSV),
        ):
            stats = run_neighborhood_pipeline(tmp_path)
        assert stats["green_areas"] is None
        geojson = json.loads((tmp_path / "quartiere.geojson").read_text())
        props = geojson["features"][0]["properties"]
        assert props["green_area_m2"] is None
        assert props["green_share_pct"] is None
        assert props["green_m2_per_capita"] is None
        assert not (tmp_path / "green_spaces.geojson").exists()

    def test_cached_green_raw_reused(self, tmp_path):
        from strata_api.pipeline.neighborhoods.runner import run_neighborhood_pipeline

        (tmp_path / "green_raw.json").write_text(json.dumps(GREEN_RAW))
        with (
            patch("strata_api.pipeline.neighborhoods.runner.download_quartier_geojson", return_value=QUARTIER_GEOJSON),
            patch("strata_api.pipeline.neighborhoods.runner.download_demographics_csv", return_value=DEMO_CSV),
            patch("strata_api.pipeline.neighborhoods.runner.download_noise_geojson", return_value=NOISE_GEOJSON),
            patch("strata_api.pipeline.neighborhoods.runner.download_construction_csv", return_value=CONSTRUCTION_CSV),
        ):
            stats = run_neighborhood_pipeline(tmp_path)
        assert stats["green_areas"] == 1  # only the in-polygon park counts toward a quartier
        geojson = json.loads((tmp_path / "quartiere.geojson").read_text())
        props = geojson["features"][0]["properties"]
        assert props["green_area_m2"] > 0
        assert props["green_share_pct"] is not None
        # green_spaces.geojson written for the map layer (both parsed areas kept)
        green_fc = json.loads((tmp_path / "green_spaces.geojson").read_text())
        assert green_fc["type"] == "FeatureCollection"
        assert len(green_fc["features"]) == 2

    def test_fetch_green_calls_overpass_and_caches(self, tmp_path):
        from strata_api.pipeline.neighborhoods.runner import run_neighborhood_pipeline

        with (
            patch("strata_api.pipeline.neighborhoods.runner.download_quartier_geojson", return_value=QUARTIER_GEOJSON),
            patch("strata_api.pipeline.neighborhoods.runner.download_demographics_csv", return_value=DEMO_CSV),
            patch("strata_api.pipeline.neighborhoods.runner.download_noise_geojson", return_value=NOISE_GEOJSON),
            patch("strata_api.pipeline.neighborhoods.runner.download_construction_csv", return_value=CONSTRUCTION_CSV),
            patch("strata_api.pipeline.neighborhoods.runner.fetch_overpass_green", return_value=GREEN_RAW) as mock_fetch,
        ):
            stats = run_neighborhood_pipeline(tmp_path, fetch_green=True)
        mock_fetch.assert_called_once()
        assert stats["green_areas"] == 1
        assert (tmp_path / "green_raw.json").exists()


class TestRunnerSkipNoise:
    def test_skip_noise_avoids_download_and_keeps_existing_file(self, tmp_path):
        from strata_api.pipeline.neighborhoods.runner import run_neighborhood_pipeline

        (tmp_path / "noise.geojson").write_text('{"existing": true}')
        with (
            patch("strata_api.pipeline.neighborhoods.runner.download_quartier_geojson", return_value=QUARTIER_GEOJSON),
            patch("strata_api.pipeline.neighborhoods.runner.download_demographics_csv", return_value=DEMO_CSV),
            patch("strata_api.pipeline.neighborhoods.runner.download_noise_geojson") as mock_noise,
            patch("strata_api.pipeline.neighborhoods.runner.download_construction_csv", return_value=CONSTRUCTION_CSV),
        ):
            stats = run_neighborhood_pipeline(tmp_path, skip_noise=True)
        mock_noise.assert_not_called()
        assert stats["noise_points"] is None
        assert (tmp_path / "noise.geojson").read_text() == '{"existing": true}'
        assert (tmp_path / "quartiere.geojson").exists()


class TestRunnerConstruction:
    def test_construction_attached_to_features(self, tmp_path):
        from strata_api.pipeline.neighborhoods.runner import run_neighborhood_pipeline

        with (
            patch("strata_api.pipeline.neighborhoods.runner.download_quartier_geojson", return_value=QUARTIER_GEOJSON),
            patch("strata_api.pipeline.neighborhoods.runner.download_demographics_csv", return_value=DEMO_CSV),
            patch("strata_api.pipeline.neighborhoods.runner.download_noise_geojson", return_value=NOISE_GEOJSON),
            patch("strata_api.pipeline.neighborhoods.runner.download_construction_csv", return_value=CONSTRUCTION_CSV),
        ):
            stats = run_neighborhood_pipeline(tmp_path)
        assert stats["construction_quartiere"] == 1
        geojson = json.loads((tmp_path / "quartiere.geojson").read_text())
        construction = geojson["features"][0]["properties"]["construction"]
        assert construction["approved_projects"] == 3
        assert construction["year"] == 2025
        assert construction["cost_mchf"] == 45.0
