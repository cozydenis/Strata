"""TDD tests for the construction projects parser — written BEFORE implementation (RED phase).

Source: Stadt Zürich OGD BAU501OD5011 — Neubautätigkeit nach Bauprojektstatus
und Stadtquartier. Statuses: '2' Bewilligt harmonisiert, '3' Baubegonnen.
Costs are CHF thousands; 'K' means masked for confidentiality.
"""
from __future__ import annotations

from strata_api.pipeline.neighborhoods.construction_parser import parse_construction_csv

CSV = (
    '﻿"StichtagDatJahr","DatenstandCd","QuarSort","QuarCd","QuarLang","KreisSort","KreisCd","KreisLang",'
    '"ProjektStatusSSZPubl1Sort","ProjektStatusSSZPubl1Cd","ProjektStatusSSZPubl1Lang",'
    '"ArtArbeitenSort","ArtArbeitenCd","ArtArbeitenLang","AnzBauprojekte","BaukostenEffektiv"\n'
    '2024,"D",21,"021","Wollishofen",2,"2","Kreis 2",2,"2","Bewilligt harmonisiert",1,"N","Neubau",9,90000\n'
    '2025,"D",21,"021","Wollishofen",2,"2","Kreis 2",2,"2","Bewilligt harmonisiert",1,"N","Neubau",11,113705\n'
    '2025,"D",21,"021","Wollishofen",2,"2","Kreis 2",3,"3","Baubegonnen",1,"N","Neubau",13,164252\n'
    '2025,"D",13,"013","Lindenhof",1,"1","Kreis 1",2,"2","Bewilligt harmonisiert",1,"N","Neubau",1,K\n'
    '2025,"D",23,"023","Leimbach",1,"1","Kreis 1",3,"3","Baubegonnen",1,"N","Neubau",2,K\n'
)


class TestParseConstructionCsv:
    def test_latest_year_only(self):
        stats = parse_construction_csv(CSV)
        assert stats[21]["year"] == 2025
        # 2024 row for Wollishofen ignored
        assert stats[21]["approved_projects"] == 11

    def test_approved_and_started_split(self):
        stats = parse_construction_csv(CSV)
        assert stats[21]["approved_projects"] == 11
        assert stats[21]["started_projects"] == 13

    def test_cost_summed_in_mchf(self):
        """Costs are CHF thousands → (113705 + 164252) / 1000 ≈ 278.0 MCHF."""
        stats = parse_construction_csv(CSV)
        assert stats[21]["cost_mchf"] == 278.0

    def test_masked_costs_yield_none(self):
        stats = parse_construction_csv(CSV)
        assert stats[13]["approved_projects"] == 1
        assert stats[13]["cost_mchf"] is None

    def test_missing_status_defaults_to_zero(self):
        stats = parse_construction_csv(CSV)
        assert stats[13]["started_projects"] == 0
        assert stats[23]["approved_projects"] == 0

    def test_quartier_ids_are_ints(self):
        stats = parse_construction_csv(CSV)
        assert set(stats) == {21, 13, 23}

    def test_empty_csv(self):
        header = CSV.split("\n")[0] + "\n"
        assert parse_construction_csv(header) == {}
