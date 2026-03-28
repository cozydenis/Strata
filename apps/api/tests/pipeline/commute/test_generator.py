"""Tests for the commute isochrone generator — written FIRST (TDD Red phase)."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch
from urllib.parse import urlparse

# ---------------------------------------------------------------------------
# Phase 2A: destinations constants
# ---------------------------------------------------------------------------


def test_destinations_has_four_keys() -> None:
    """DESTINATIONS must contain exactly the four expected keys."""
    from strata_api.pipeline.commute.destinations import DESTINATIONS

    assert set(DESTINATIONS.keys()) == {"hb", "eth", "airport", "technopark"}


def test_contour_minutes_are_correct() -> None:
    """CONTOUR_MINUTES must be exactly [10, 20, 30, 45]."""
    from strata_api.pipeline.commute.destinations import CONTOUR_MINUTES

    assert CONTOUR_MINUTES == [10, 20, 30, 45]


def test_destinations_have_required_fields() -> None:
    """Each destination must have name, lat, lon keys."""
    from strata_api.pipeline.commute.destinations import DESTINATIONS

    for key, dest in DESTINATIONS.items():
        assert "name" in dest, f"{key} missing 'name'"
        assert "lat" in dest, f"{key} missing 'lat'"
        assert "lon" in dest, f"{key} missing 'lon'"
        assert isinstance(dest["lat"], float), f"{key} lat must be float"
        assert isinstance(dest["lon"], float), f"{key} lon must be float"


# ---------------------------------------------------------------------------
# Phase 2B: fetch_isochrone
# ---------------------------------------------------------------------------


def _make_otp_feature(time_seconds: int) -> dict:
    """Helper: build a minimal OTP isochrone feature."""
    return {
        "type": "Feature",
        "geometry": {"type": "MultiPolygon", "coordinates": [[[[8.5, 47.4], [8.6, 47.4], [8.6, 47.3], [8.5, 47.4]]]]},
        "properties": {"time": time_seconds},
    }


def _make_otp_response(contour_minutes: list[int]) -> dict:
    """Helper: build a minimal OTP FeatureCollection response."""
    return {
        "type": "FeatureCollection",
        "features": [_make_otp_feature(m * 60) for m in contour_minutes],
    }


def test_fetch_isochrone_calls_correct_url() -> None:
    """fetch_isochrone must call the OTP traveltime/isochrone endpoint with correct params."""
    from strata_api.pipeline.commute.generator import fetch_isochrone

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = _make_otp_response([10, 20, 30, 45])

    with patch("httpx.get", return_value=mock_response) as mock_get:
        fetch_isochrone("hb", "http://localhost:8080", [10, 20, 30, 45])

    mock_get.assert_called_once()
    url, *_ = mock_get.call_args.args
    params = mock_get.call_args.kwargs.get("params", {})

    assert "/otp/routers/default/isochrone" in url
    # params is now a list of tuples — check serialized form
    params_str = str(params)
    assert "47.3769" in params_str
    assert "arriveBy" in params_str


def test_fetch_isochrone_returns_geojson() -> None:
    """fetch_isochrone must return a FeatureCollection dict."""
    from strata_api.pipeline.commute.generator import fetch_isochrone

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = _make_otp_response([10, 20, 30, 45])

    with patch("httpx.get", return_value=mock_response):
        result = fetch_isochrone("hb", "http://localhost:8080", [10, 20, 30, 45])

    assert isinstance(result, dict)
    assert result["type"] == "FeatureCollection"
    assert isinstance(result["features"], list)


def test_fetch_isochrone_tags_features_with_contour_minutes() -> None:
    """Each returned feature must have contour_minutes as an int (converted from seconds)."""
    from strata_api.pipeline.commute.generator import fetch_isochrone

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = _make_otp_response([10, 20, 30, 45])

    with patch("httpx.get", return_value=mock_response):
        result = fetch_isochrone("hb", "http://localhost:8080", [10, 20, 30, 45])

    contour_values = [f["properties"]["contour_minutes"] for f in result["features"]]
    assert contour_values == [10, 20, 30, 45]
    for v in contour_values:
        assert isinstance(v, int)


def test_fetch_isochrone_uses_arrive_by_true() -> None:
    """arriveBy parameter must be set to true in the OTP request."""
    from strata_api.pipeline.commute.generator import fetch_isochrone

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = _make_otp_response([10])

    with patch("httpx.get", return_value=mock_response) as mock_get:
        fetch_isochrone("hb", "http://localhost:8080", [10], arrive_by=True)

    params = mock_get.call_args.kwargs.get("params", [])
    # params is a list of tuples: [("arriveBy", "true"), ...]
    params_str = str(params)
    assert "arriveBy" in params_str
    assert "true" in params_str


# ---------------------------------------------------------------------------
# Phase 2C: generate_all
# ---------------------------------------------------------------------------


def test_generate_all_writes_four_files(tmp_path: Path) -> None:
    """generate_all must write exactly 4 GeoJSON files, one per destination."""
    from strata_api.pipeline.commute.generator import generate_all

    mock_geojson = _make_otp_response([10, 20, 30, 45])

    with patch("strata_api.pipeline.commute.generator.fetch_isochrone", return_value=mock_geojson):
        generate_all("http://localhost:8080", str(tmp_path))

    written = list(tmp_path.glob("*.geojson"))
    assert len(written) == 4
    names = {f.stem for f in written}
    assert names == {"hb", "eth", "airport", "technopark"}


def test_generate_all_file_is_valid_geojson(tmp_path: Path) -> None:
    """Each file written by generate_all must be parseable as a GeoJSON FeatureCollection.

    The mock returns what fetch_isochrone returns after processing (contour_minutes already set).
    """
    from strata_api.pipeline.commute.generator import generate_all

    # Simulate what fetch_isochrone returns after tagging (contour_minutes already set)
    mock_geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "MultiPolygon", "coordinates": []},
                "properties": {"contour_minutes": m},
            }
            for m in [10, 20, 30, 45]
        ],
    }

    with patch("strata_api.pipeline.commute.generator.fetch_isochrone", return_value=mock_geojson):
        generate_all("http://localhost:8080", str(tmp_path))

    for filepath in tmp_path.glob("*.geojson"):
        data = json.loads(filepath.read_text(encoding="utf-8"))
        assert data["type"] == "FeatureCollection"
        assert isinstance(data["features"], list)
        for feat in data["features"]:
            assert "contour_minutes" in feat["properties"]


# ---------------------------------------------------------------------------
# TravelTime API backend
# ---------------------------------------------------------------------------


def _make_traveltime_shape(coords: list[list[float]] | None = None) -> dict:
    """Helper: minimal TravelTime shape (shell + no holes)."""
    pts = coords or [[8.5, 47.4], [8.6, 47.4], [8.6, 47.3], [8.5, 47.4]]
    return {"shell": [{"lat": p[1], "lng": p[0]} for p in pts], "holes": []}


def _make_traveltime_response(destination_key: str, contour_minutes: list[int]) -> dict:
    """Helper: build a minimal TravelTime API /v4/time-map response."""
    return {
        "results": [
            {
                "search_id": f"{destination_key}_{m}min",
                "shapes": [_make_traveltime_shape()],
            }
            for m in contour_minutes
        ]
    }


def test_fetch_isochrone_traveltime_calls_correct_endpoint() -> None:
    """fetch_isochrone_traveltime must POST to the TravelTime /v4/time-map endpoint."""
    from strata_api.pipeline.commute.generator import fetch_isochrone_traveltime

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = _make_traveltime_response("hb", [10, 20, 30, 45])

    with patch("httpx.post", return_value=mock_response) as mock_post:
        fetch_isochrone_traveltime("hb", "test-app-id", "test-api-key", [10, 20, 30, 45])

    mock_post.assert_called_once()
    url = mock_post.call_args.args[0]
    parsed = urlparse(url)
    assert parsed.hostname == "api.traveltimeapp.com"
    assert "time-map" in parsed.path


def test_fetch_isochrone_traveltime_sends_auth_headers() -> None:
    """fetch_isochrone_traveltime must send X-Application-Id and X-Api-Key headers."""
    from strata_api.pipeline.commute.generator import fetch_isochrone_traveltime

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = _make_traveltime_response("hb", [10])

    with patch("httpx.post", return_value=mock_response) as mock_post:
        fetch_isochrone_traveltime("hb", "my-app-id", "my-api-key", [10])

    headers = mock_post.call_args.kwargs.get("headers", {})
    assert headers.get("X-Application-Id") == "my-app-id"
    assert headers.get("X-Api-Key") == "my-api-key"


def test_fetch_isochrone_traveltime_uses_arrival_searches() -> None:
    """fetch_isochrone_traveltime must send arrival_searches (not departure_searches)."""
    from strata_api.pipeline.commute.generator import fetch_isochrone_traveltime

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = _make_traveltime_response("hb", [10])

    with patch("httpx.post", return_value=mock_response) as mock_post:
        fetch_isochrone_traveltime("hb", "app", "key", [10])

    body = mock_post.call_args.kwargs.get("json", {})
    assert "arrival_searches" in body
    assert "departure_searches" not in body
    searches = body["arrival_searches"]
    assert len(searches) == 1
    assert searches[0]["travel_time"] == 600  # 10 min in seconds


def test_fetch_isochrone_traveltime_returns_featurecollection() -> None:
    """fetch_isochrone_traveltime must return a FeatureCollection with contour_minutes."""
    from strata_api.pipeline.commute.generator import fetch_isochrone_traveltime

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = _make_traveltime_response("hb", [10, 20, 30, 45])

    with patch("httpx.post", return_value=mock_response):
        result = fetch_isochrone_traveltime("hb", "app", "key", [10, 20, 30, 45])

    assert result["type"] == "FeatureCollection"
    features = result["features"]
    assert len(features) == 4
    contour_values = {f["properties"]["contour_minutes"] for f in features}
    assert contour_values == {10, 20, 30, 45}
    for f in features:
        assert isinstance(f["properties"]["contour_minutes"], int)


def test_fetch_isochrone_traveltime_converts_shapes_to_geojson_polygon() -> None:
    """Shapes must be converted to Polygon (single) or MultiPolygon (multiple)."""
    from strata_api.pipeline.commute.generator import fetch_isochrone_traveltime

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = _make_traveltime_response("hb", [10])

    with patch("httpx.post", return_value=mock_response):
        result = fetch_isochrone_traveltime("hb", "app", "key", [10])

    feature = result["features"][0]
    assert feature["geometry"]["type"] in ("Polygon", "MultiPolygon")
    assert feature["geometry"]["coordinates"]


def test_fetch_isochrone_traveltime_multipolygon_for_multiple_shapes() -> None:
    """When a result has multiple shapes, geometry must be MultiPolygon."""
    from strata_api.pipeline.commute.generator import fetch_isochrone_traveltime

    response_two_shapes = {
        "results": [
            {
                "search_id": "hb_10min",
                "shapes": [_make_traveltime_shape(), _make_traveltime_shape()],
            }
        ]
    }

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = response_two_shapes

    with patch("httpx.post", return_value=mock_response):
        result = fetch_isochrone_traveltime("hb", "app", "key", [10])

    assert result["features"][0]["geometry"]["type"] == "MultiPolygon"


def test_fetch_isochrone_traveltime_orders_features_largest_first() -> None:
    """Features must be sorted largest contour_minutes first (for layer rendering)."""
    from strata_api.pipeline.commute.generator import fetch_isochrone_traveltime

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = _make_traveltime_response("hb", [10, 20, 30, 45])

    with patch("httpx.post", return_value=mock_response):
        result = fetch_isochrone_traveltime("hb", "app", "key", [10, 20, 30, 45])

    contours = [f["properties"]["contour_minutes"] for f in result["features"]]
    assert contours == sorted(contours, reverse=True)


# ---------------------------------------------------------------------------
# generate_all_traveltime
# ---------------------------------------------------------------------------


def test_generate_all_traveltime_writes_four_files(tmp_path: Path) -> None:
    """generate_all_traveltime must write 4 GeoJSON files, one per destination."""
    from strata_api.pipeline.commute.generator import generate_all_traveltime

    mock_fc = {"type": "FeatureCollection", "features": []}

    with (
        patch("strata_api.pipeline.commute.generator.fetch_isochrone_traveltime", return_value=mock_fc),
        patch("time.sleep"),  # skip throttle delay in tests
    ):
        generate_all_traveltime("app", "key", str(tmp_path))

    written = {f.stem for f in tmp_path.glob("*.geojson")}
    assert written == {"hb", "eth", "airport", "technopark"}


# ---------------------------------------------------------------------------
# generate_all_auto backend selection
# ---------------------------------------------------------------------------


def test_generate_all_auto_uses_traveltime_when_env_set(tmp_path: Path, monkeypatch) -> None:
    """generate_all_auto must call generate_all_traveltime when env vars are present."""
    import strata_api.pipeline.commute.generator as gen_module

    monkeypatch.setenv("TRAVELTIME_APP_ID", "my-app")
    monkeypatch.setenv("TRAVELTIME_API_KEY", "my-key")

    with (
        patch.object(gen_module, "generate_all_traveltime") as mock_tt,
        patch.object(gen_module, "generate_all") as mock_otp,
    ):
        gen_module.generate_all_auto(str(tmp_path))

    mock_tt.assert_called_once_with("my-app", "my-key", str(tmp_path))
    mock_otp.assert_not_called()


def test_generate_all_auto_uses_otp_when_env_not_set(tmp_path: Path, monkeypatch) -> None:
    """generate_all_auto must call generate_all (OTP) when env vars are absent."""
    import strata_api.pipeline.commute.generator as gen_module

    monkeypatch.delenv("TRAVELTIME_APP_ID", raising=False)
    monkeypatch.delenv("TRAVELTIME_API_KEY", raising=False)

    with (
        patch.object(gen_module, "generate_all_traveltime") as mock_tt,
        patch.object(gen_module, "generate_all") as mock_otp,
    ):
        gen_module.generate_all_auto(str(tmp_path), otp_base_url="http://otp:8080")

    mock_otp.assert_called_once_with("http://otp:8080", str(tmp_path))
    mock_tt.assert_not_called()
