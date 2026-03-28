"""Tests for quartier commute stats — written FIRST (TDD Red phase)."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# fetch_travel_time
# ---------------------------------------------------------------------------


def _make_plan_response(duration_seconds: int) -> dict:
    """Build a minimal OTP /plan response."""
    return {
        "plan": {
            "itineraries": [
                {"duration": duration_seconds, "legs": []},
            ]
        }
    }


def test_fetch_travel_time_returns_minutes() -> None:
    """fetch_travel_time must return travel time in minutes (int) from OTP plan response."""
    from strata_api.pipeline.commute.quartier_commute import fetch_travel_time

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = _make_plan_response(1320)  # 22 minutes in seconds

    with patch("httpx.get", return_value=mock_response):
        result = fetch_travel_time(47.38, 8.54, 47.3769, 8.5417, "http://localhost:8080")

    assert result == 22
    assert isinstance(result, int)


def test_fetch_travel_time_calls_correct_endpoint() -> None:
    """fetch_travel_time must call the OTP /plan endpoint with correct params."""
    from strata_api.pipeline.commute.quartier_commute import fetch_travel_time

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = _make_plan_response(600)

    with patch("httpx.get", return_value=mock_response) as mock_get:
        fetch_travel_time(47.38, 8.54, 47.3769, 8.5417, "http://localhost:8080")

    mock_get.assert_called_once()
    url = mock_get.call_args.args[0]
    assert "/otp/routers/default/plan" in url

    params = mock_get.call_args.kwargs.get("params", {})
    assert "fromPlace" in params
    assert "toPlace" in params
    assert "47.38" in str(params["fromPlace"])
    assert "47.3769" in str(params["toPlace"])


def test_fetch_travel_time_returns_none_on_http_error() -> None:
    """fetch_travel_time must return None when OTP returns an HTTP error."""
    import httpx

    from strata_api.pipeline.commute.quartier_commute import fetch_travel_time

    with patch("httpx.get", side_effect=httpx.HTTPError("connection failed")):
        result = fetch_travel_time(47.38, 8.54, 47.3769, 8.5417, "http://localhost:8080")

    assert result is None


def test_fetch_travel_time_returns_none_on_empty_itineraries() -> None:
    """fetch_travel_time must return None when OTP returns no itineraries."""
    from strata_api.pipeline.commute.quartier_commute import fetch_travel_time

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {"plan": {"itineraries": []}}

    with patch("httpx.get", return_value=mock_response):
        result = fetch_travel_time(47.38, 8.54, 47.3769, 8.5417, "http://localhost:8080")

    assert result is None


def test_fetch_travel_time_returns_none_on_missing_plan() -> None:
    """fetch_travel_time must return None when OTP response has no plan key."""
    from strata_api.pipeline.commute.quartier_commute import fetch_travel_time

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {"error": "no route found"}

    with patch("httpx.get", return_value=mock_response):
        result = fetch_travel_time(47.38, 8.54, 47.3769, 8.5417, "http://localhost:8080")

    assert result is None


# ---------------------------------------------------------------------------
# compute_quartier_commute_hb
# ---------------------------------------------------------------------------


def test_compute_quartier_commute_hb_returns_dict() -> None:
    """compute_quartier_commute_hb must return a dict mapping quartier_id → minutes."""
    from strata_api.pipeline.commute.quartier_commute import compute_quartier_commute_hb

    centroids = {
        1: (47.38, 8.54),
        2: (47.39, 8.55),
        3: (47.40, 8.56),
    }

    with patch(
        "strata_api.pipeline.commute.quartier_commute.fetch_travel_time",
        side_effect=[15, 22, None],
    ):
        result = compute_quartier_commute_hb(centroids, "http://localhost:8080")

    assert isinstance(result, dict)
    assert set(result.keys()) == {1, 2, 3}
    assert result[1] == 15
    assert result[2] == 22
    assert result[3] is None


def test_compute_quartier_commute_hb_passes_hb_coordinates() -> None:
    """compute_quartier_commute_hb must route to Zürich HB coordinates."""
    from strata_api.pipeline.commute.quartier_commute import compute_quartier_commute_hb

    centroids = {1: (47.38, 8.54)}

    with patch(
        "strata_api.pipeline.commute.quartier_commute.fetch_travel_time",
        return_value=10,
    ) as mock_fetch:
        compute_quartier_commute_hb(centroids, "http://localhost:8080")

    mock_fetch.assert_called_once()
    call_args = mock_fetch.call_args
    # to_lat, to_lon should be Zürich HB
    to_lat = call_args.args[2] if len(call_args.args) > 2 else call_args.kwargs.get("to_lat")
    to_lon = call_args.args[3] if len(call_args.args) > 3 else call_args.kwargs.get("to_lon")
    assert to_lat == pytest.approx(47.3769, abs=0.001)
    assert to_lon == pytest.approx(8.5417, abs=0.001)


def test_compute_quartier_commute_hb_empty_centroids() -> None:
    """compute_quartier_commute_hb with empty input returns empty dict."""
    from strata_api.pipeline.commute.quartier_commute import compute_quartier_commute_hb

    result = compute_quartier_commute_hb({}, "http://localhost:8080")

    assert result == {}
