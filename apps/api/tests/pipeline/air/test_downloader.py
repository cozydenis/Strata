"""Thin tests for the air downloader — URL construction only (no network)."""

from __future__ import annotations

from strata_api.pipeline.air.downloader import air_csv_url, stations_url


def test_air_csv_url_for_year():
    assert air_csv_url(2026) == (
        "https://data.stadt-zuerich.ch/dataset/ugz_luftschadstoffmessung_stundenwerte/download/ugz_ogd_air_h1_2026.csv"
    )


def test_air_csv_url_interpolates_year():
    assert air_csv_url(1999).endswith("ugz_ogd_air_h1_1999.csv")


def test_stations_url_is_metadata_json():
    assert stations_url().endswith("uzg_ogd_metadaten.json")
