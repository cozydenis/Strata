"""Unit tests for Referenzzinssatz rent-adjustment math (OR Art. 269a lit. b).

The permitted rent-change percentages are pinned to the official BWO table so a
future refactor of the formula cannot silently drift from the published values.
"""
import pytest

from strata_api.legal.referenzzins import (
    RentAnalysis,
    analyze_rent,
    monthly_reduction_chf,
    permitted_change_pct,
)


# ── permitted_change_pct: pinned to the official BWO step table ──
@pytest.mark.parametrize(
    "base, current, expected",
    [
        (1.75, 1.50, -2.91),   # one 0.25 step down
        (1.75, 1.25, -5.74),   # two steps down
        (2.00, 1.25, -8.49),   # three steps down
        (2.25, 1.25, -11.15),  # four steps down
        (1.25, 1.50, 3.00),    # one step up (increase)
        (1.25, 1.75, 6.09),    # two steps up
        (1.50, 1.50, 0.0),     # no change
    ],
)
def test_permitted_change_pct_matches_bwo_table(base, current, expected):
    assert permitted_change_pct(base, current) == expected


def test_permitted_change_pct_rejects_non_quarter_rate():
    with pytest.raises(ValueError):
        permitted_change_pct(1.30, 1.25)


def test_permitted_change_pct_rejects_out_of_range():
    with pytest.raises(ValueError):
        permitted_change_pct(0.0, 1.25)
    with pytest.raises(ValueError):
        permitted_change_pct(8.0, 1.25)


# ── monthly_reduction_chf: absolute CHF magnitude of the change ──
def test_monthly_reduction_chf_reduction():
    assert monthly_reduction_chf(2000, -2.91) == 58.20


def test_monthly_reduction_chf_rejects_negative_rent():
    with pytest.raises(ValueError):
        monthly_reduction_chf(-100, -2.91)


# ── analyze_rent: full structured result ──
def test_analyze_rent_reduction():
    result = analyze_rent(base_rate=1.75, current_rate=1.25, rent_net=2000)
    assert isinstance(result, RentAnalysis)
    assert result.change_pct == -5.74
    assert result.direction == "reduction"
    assert result.monthly_chf == -114.80    # 2000 * -5.74%
    assert result.new_rent_net == 1885.20


def test_analyze_rent_increase():
    result = analyze_rent(base_rate=1.25, current_rate=1.75, rent_net=2000)
    assert result.direction == "increase"
    assert result.change_pct == 6.09


def test_analyze_rent_no_change():
    result = analyze_rent(base_rate=1.25, current_rate=1.25, rent_net=2000)
    assert result.direction == "none"
    assert result.change_pct == 0.0
    assert result.monthly_chf == 0.0
    assert result.new_rent_net == 2000.0
