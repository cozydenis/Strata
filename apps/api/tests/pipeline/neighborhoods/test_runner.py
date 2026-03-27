"""TDD tests for neighborhood pipeline runner — written BEFORE implementation (RED phase)."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest


NOISE_GEOJSON: dict = {"type": "FeatureCollection", "features": []}

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
        ):
            stats = run_neighborhood_pipeline(tmp_path)

        assert isinstance(stats, dict)

    def test_stats_contains_quartiere_count(self, tmp_path):
        from strata_api.pipeline.neighborhoods.runner import run_neighborhood_pipeline

        with (
            patch("strata_api.pipeline.neighborhoods.runner.download_quartier_geojson", return_value=QUARTIER_GEOJSON),
            patch("strata_api.pipeline.neighborhoods.runner.download_demographics_csv", return_value=DEMO_CSV),
            patch("strata_api.pipeline.neighborhoods.runner.download_noise_geojson", return_value=NOISE_GEOJSON),
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
