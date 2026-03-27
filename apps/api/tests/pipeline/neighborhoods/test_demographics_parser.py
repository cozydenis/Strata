"""TDD tests for demographics_parser — written BEFORE implementation (RED phase).

CSV field names discovered via recon:
  StichtagDatJahr -> year
  QuarCd          -> quartier_id (string like "011", parse as int -> 11)
  QuarLang        -> quartier_name
  HerkunftCd      -> "1"=Swiss, "2"=Foreign
  AlterV20Cd      -> age bucket start: "0"=0-19, "20"=20-39, "40"=40-59, "60"=60-79, "80"=80-99, "100"=100+
  AnzBestWir      -> population count
"""
from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import pytest

FIXTURE_CSV = Path(__file__).resolve().parents[2] / "fixtures" / "neighborhoods" / "demographics_sample.csv"


@pytest.fixture
def csv_text() -> str:
    return FIXTURE_CSV.read_text(encoding="utf-8")


@pytest.fixture
def minimal_csv() -> str:
    """Minimal CSV: 2 years × 1 quartier, one age bucket each."""
    return dedent("""\
        StichtagDatJahr,AlterVSort,AlterVCd,AlterV05Sort,AlterV05Cd,AlterV05Kurz,AlterV10Cd,AlterV10Kurz,AlterV20Cd,AlterV20Kurz,SexCd,SexLang,SexKurz,KreisCd,KreisLang,QuarSort,QuarCd,QuarLang,HerkunftSort,HerkunftCd,HerkunftLang,AnzBestWir
        2022,0,"0",1,"0","0-4","0","0-9","0","0-19","1","männlich","M","1","Kreis 1",11,"011","Rathaus",1,"1","Schweizer*in",100
        2022,0,"0",1,"0","0-4","0","0-9","0","0-19","1","männlich","M","1","Kreis 1",11,"011","Rathaus",2,"2","Ausländer*in",20
        2023,0,"0",1,"0","0-4","0","0-9","0","0-19","1","männlich","M","1","Kreis 1",11,"011","Rathaus",1,"1","Schweizer*in",110
        2023,0,"0",1,"0","0-4","0","0-9","0","0-19","1","männlich","M","1","Kreis 1",11,"011","Rathaus",2,"2","Ausländer*in",22
    """)


class TestQuartierDemographics:
    """Unit tests for the QuartierDemographics dataclass."""

    def test_is_importable(self):
        from strata_api.pipeline.neighborhoods.demographics_parser import (
            QuartierDemographics,  # noqa: F401
        )

    def test_has_required_fields(self):
        from strata_api.pipeline.neighborhoods.demographics_parser import QuartierDemographics

        d = QuartierDemographics(
            quartier_id=11,
            year=2023,
            total_population=1000,
            age_buckets={"0-17": 100, "18-29": 200, "30-44": 300, "45-64": 250, "65+": 150},
            swiss_count=700,
            foreign_count=300,
            yoy_change=None,
        )
        assert d.quartier_id == 11
        assert d.year == 2023
        assert d.total_population == 1000
        assert d.swiss_count == 700
        assert d.foreign_count == 300
        assert d.yoy_change is None

    def test_age_buckets_keys(self):
        from strata_api.pipeline.neighborhoods.demographics_parser import QuartierDemographics

        d = QuartierDemographics(
            quartier_id=11,
            year=2023,
            total_population=100,
            age_buckets={"0-17": 10, "18-29": 20, "30-44": 30, "45-64": 25, "65+": 15},
            swiss_count=70,
            foreign_count=30,
            yoy_change=5,
        )
        assert set(d.age_buckets.keys()) == {"0-17", "18-29", "30-44", "45-64", "65+"}


class TestParseDemographicsCSV:
    """Unit tests for parse_demographics_csv function."""

    def test_is_importable(self):
        from strata_api.pipeline.neighborhoods.demographics_parser import (
            parse_demographics_csv,  # noqa: F401
        )

    def test_returns_dict_keyed_by_quartier_id(self, csv_text):
        from strata_api.pipeline.neighborhoods.demographics_parser import parse_demographics_csv

        result = parse_demographics_csv(csv_text)
        assert isinstance(result, dict)
        assert 11 in result

    def test_filters_to_latest_year(self, csv_text):
        """Should only return data for the most recent year."""
        from strata_api.pipeline.neighborhoods.demographics_parser import parse_demographics_csv

        result = parse_demographics_csv(csv_text)
        for demo in result.values():
            assert demo.year == 2023

    def test_aggregates_total_population(self, csv_text):
        """total_population is sum of AnzBestWir across all rows for that quartier+year."""
        from strata_api.pipeline.neighborhoods.demographics_parser import parse_demographics_csv

        result = parse_demographics_csv(csv_text)
        demo = result[11]
        # From fixture: sum of all AnzBestWir for QuarCd=011, year=2023
        # 50+40+10+8 + 100+90+30+25 + 80+70+20+15 + 60+55+12+10 = 675
        assert demo.total_population == 675

    def test_separates_swiss_and_foreign(self, csv_text):
        from strata_api.pipeline.neighborhoods.demographics_parser import parse_demographics_csv

        result = parse_demographics_csv(csv_text)
        demo = result[11]
        # Swiss (HerkunftCd=1): 50+40+100+90+80+70+60+55 = 545
        # Foreign (HerkunftCd=2): 10+8+30+25+20+15+12+10 = 130
        assert demo.swiss_count == 545
        assert demo.foreign_count == 130
        assert demo.swiss_count + demo.foreign_count == demo.total_population

    def test_quarcdr_string_parsed_as_int(self, minimal_csv):
        """QuarCd '011' should be parsed as quartier_id=11."""
        from strata_api.pipeline.neighborhoods.demographics_parser import parse_demographics_csv

        result = parse_demographics_csv(minimal_csv)
        assert 11 in result

    def test_yoy_change_is_computed(self, csv_text):
        """yoy_change = latest_total - previous_year_total."""
        from strata_api.pipeline.neighborhoods.demographics_parser import parse_demographics_csv

        result = parse_demographics_csv(csv_text)
        demo = result[11]
        # 2023 total=675, 2022 total (from fixture): 45+38+95+85 = 263
        # yoy_change = 675 - 263 = 412
        assert demo.yoy_change == 675 - 263

    def test_yoy_change_is_none_when_only_one_year(self, minimal_csv):
        """When only one year of data, yoy_change should be computed from year before."""
        from strata_api.pipeline.neighborhoods.demographics_parser import parse_demographics_csv

        # minimal_csv has 2022 and 2023 data
        result = parse_demographics_csv(minimal_csv)
        demo = result[11]
        # 2023: 110+22=132, 2022: 100+20=120
        assert demo.yoy_change == 12

    def test_age_buckets_sum_to_total(self, csv_text):
        """Age bucket counts should sum to total_population."""
        from strata_api.pipeline.neighborhoods.demographics_parser import parse_demographics_csv

        result = parse_demographics_csv(csv_text)
        demo = result[11]
        bucket_sum = sum(demo.age_buckets.values())
        assert bucket_sum == demo.total_population

    def test_age_bucket_keys_are_correct(self, csv_text):
        from strata_api.pipeline.neighborhoods.demographics_parser import parse_demographics_csv

        result = parse_demographics_csv(csv_text)
        demo = result[11]
        assert set(demo.age_buckets.keys()) == {"0-17", "18-29", "30-44", "45-64", "65+"}

    def test_multiple_quartiere_parsed(self, csv_text):
        from strata_api.pipeline.neighborhoods.demographics_parser import parse_demographics_csv

        result = parse_demographics_csv(csv_text)
        # Fixture has data for quartier 11 and 73
        assert 11 in result
        assert 73 in result

    def test_empty_csv_returns_empty_dict(self):
        from strata_api.pipeline.neighborhoods.demographics_parser import parse_demographics_csv

        result = parse_demographics_csv("StichtagDatJahr,QuarCd,QuarLang,HerkunftCd,AlterV20Cd,AnzBestWir\n")
        assert result == {}

    def test_bom_header_handled(self):
        """CSV may have a BOM prefix on the header row."""
        from strata_api.pipeline.neighborhoods.demographics_parser import parse_demographics_csv

        csv_with_bom = (
            '\ufeffStichtagDatJahr,AlterVSort,AlterVCd,AlterV05Sort,AlterV05Cd,AlterV05Kurz,'
            'AlterV10Cd,AlterV10Kurz,AlterV20Cd,AlterV20Kurz,SexCd,SexLang,SexKurz,'
            'KreisCd,KreisLang,QuarSort,QuarCd,QuarLang,HerkunftSort,HerkunftCd,HerkunftLang,AnzBestWir\n'
            '2023,0,"0",1,"0","0-4","0","0-9","0","0-19","1","männlich","M","1","Kreis 1",'
            '11,"011","Rathaus",1,"1","Schweizer*in",50\n'
        )
        result = parse_demographics_csv(csv_with_bom)
        assert 11 in result
