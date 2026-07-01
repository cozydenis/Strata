"""Unit tests for Herabsetzungsbegehren letter rendering."""
import datetime

import pytest

from strata_api.legal.herabsetzung import HerabsetzungContext, render
from strata_api.legal.referenzzins import analyze_rent


def _context(**overrides):
    analysis = analyze_rent(base_rate=1.75, current_rate=1.25, rent_net=2000)
    defaults = dict(
        tenant_name="Anna Muster",
        tenant_address="Teststrasse 1, 8001 Zürich",
        landlord_name="Verwaltung AG",
        landlord_address="Bahnhofstrasse 5, 8001 Zürich",
        property_address="Wohnung 3. OG, Teststrasse 1, 8001 Zürich",
        analysis=analysis,
        rent_net=2000,
        letter_date=datetime.date(2026, 7, 1),
    )
    defaults.update(overrides)
    return HerabsetzungContext(**defaults)


def test_render_contains_legal_citations_and_parties():
    letter = render(_context())
    for needle in [
        "Herabsetzungsbegehren",
        "Art. 269a",
        "VMWG",
        "Anna Muster",
        "Verwaltung AG",
        "Teststrasse 1",
        "nächstmöglichen Kündigungstermin",
        "Einschreiben",
        "Schlichtungsbehörde",
        "Teuerung",
        "1. Juli 2026",
    ]:
        assert needle in letter, f"letter missing expected text: {needle}"


def test_render_shows_rates_and_amounts():
    letter = render(_context())
    assert "1.75" in letter          # base rate
    assert "1.25" in letter          # current rate
    assert "5.74" in letter          # permitted reduction %
    assert "114" in letter           # monthly CHF magnitude


def test_render_has_no_unresolved_placeholders():
    letter = render(_context())
    assert "{" not in letter
    assert "}" not in letter


def test_render_carries_no_legal_advice_disclaimer():
    letter = render(_context())
    assert "keine Rechtsberatung" in letter


def test_render_requires_tenant_name():
    with pytest.raises(ValueError):
        render(_context(tenant_name="   "))
