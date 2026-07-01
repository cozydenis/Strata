"""Unit tests for the Referenzzinssatz history helpers."""
import datetime

from strata_api.legal.rates import RATE_HISTORY, latest_rate, rate_at


def test_rate_at_returns_effective_rate():
    assert rate_at(datetime.date(2024, 6, 1)) == 1.75   # between 2023-12 and 2025-03
    assert rate_at(datetime.date(2025, 6, 1)) == 1.50   # between 2025-03 and 2025-09
    assert rate_at(datetime.date(2026, 6, 1)) == 1.25   # current era


def test_rate_at_before_series_returns_none():
    assert rate_at(datetime.date(2000, 1, 1)) is None


def test_rate_at_accepts_datetime():
    assert rate_at(datetime.datetime(2024, 6, 1, 12, 0)) == 1.75


def test_latest_rate_is_current():
    assert latest_rate() == 1.25
    assert RATE_HISTORY[-1][1] == 1.25


def test_history_is_ascending_by_date():
    dates = [entry[0] for entry in RATE_HISTORY]
    assert dates == sorted(dates)
