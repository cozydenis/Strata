"""Phase 0 reconnaissance script — discover actual field names from data sources.

Run:
    cd apps/api && uv run python -m strata_api.pipeline.neighborhoods.recon
"""
from __future__ import annotations

import json
import urllib.request
from pathlib import Path

_USER_AGENT = "Strata-Pipeline/1.0 (research; contact: hello@strata.ch)"
_RECON_DIR = Path(__file__).resolve().parents[4] / "data" / "recon"

_QUARTIER_WFS_URL = (
    "https://www.ogd.stadt-zuerich.ch/wfs/geoportal/Statistische_Quartiere"
    "?service=WFS&version=1.1.0&request=GetFeature"
    "&typename=adm_statistische_quartiere_map&outputFormat=GeoJSON"
)
_DEMOGRAPHICS_CKAN_URL = (
    "https://data.stadt-zuerich.ch/api/3/action/package_show"
    "?id=bev_bestand_jahr_quartier_alter_herkunft_geschlecht_od3903"
)
_NOISE_CKAN_URL = (
    "https://data.stadt-zuerich.ch/api/3/action/package_show"
    "?id=geo_strassenlaermkataster_der_stadt_zuerich"
)


def _fetch(url: str, timeout: int = 30) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def _fetch_text(url: str, timeout: int = 30) -> str:
    return _fetch(url, timeout).decode("utf-8", errors="replace")


def recon_quartier_boundaries() -> None:
    """Fetch and inspect Quartier WFS GeoJSON."""
    print("\n" + "=" * 60)
    print("SECTION 1: Quartier Boundaries (WFS GeoJSON)")
    print("=" * 60)

    raw = _fetch(_QUARTIER_WFS_URL, timeout=60)
    data = json.loads(raw)

    _RECON_DIR.mkdir(parents=True, exist_ok=True)
    out_path = _RECON_DIR / "quartier_boundaries.json"
    out_path.write_bytes(raw)
    print(f"Saved: {out_path}")

    crs = data.get("crs", "NOT PRESENT")
    features = data.get("features", [])
    print(f"CRS: {crs}")
    print(f"Feature count: {len(features)}")

    if features:
        sample = features[0]
        props = sample.get("properties", {})
        geom = sample.get("geometry", {})
        print(f"\nAll property keys: {sorted(props.keys())}")
        print("\nSample feature properties:")
        for k, v in props.items():
            print(f"  {k!r}: {v!r}")
        print(f"\nGeometry type: {geom.get('type')}")


def recon_demographics() -> None:
    """Fetch demographics CSV metadata via CKAN, then download CSV."""
    print("\n" + "=" * 60)
    print("SECTION 2: Demographics CSV (CKAN)")
    print("=" * 60)

    meta_raw = _fetch_text(_DEMOGRAPHICS_CKAN_URL)
    meta = json.loads(meta_raw)

    resources = meta.get("result", {}).get("resources", [])
    print(f"Total resources: {len(resources)}")
    print("\nAll resources:")
    csv_url: str | None = None
    for r in resources:
        name = r.get("name", "")
        fmt = r.get("format", "")
        url = r.get("url", "")
        print(f"  [{fmt}] {name!r} -> {url}")
        if fmt.upper() == "CSV" and csv_url is None:
            csv_url = url

    if csv_url is None:
        print("ERROR: No CSV resource found!")
        return

    print(f"\nDownloading CSV from: {csv_url}")
    csv_text = _fetch_text(csv_url, timeout=120)

    # Save first 500 lines as sample
    lines = csv_text.splitlines()
    sample_lines = "\n".join(lines[:500])
    sample_path = _RECON_DIR / "demographics_sample.csv"
    sample_path.write_text(sample_lines, encoding="utf-8")
    print(f"Saved sample ({min(500, len(lines))} of {len(lines)} lines): {sample_path}")

    print(f"\nColumn names: {lines[0] if lines else 'EMPTY'}")
    print("\nFirst 3 data rows:")
    for row in lines[1:4]:
        print(f"  {row}")


def recon_noise() -> None:
    """Fetch noise cadastre resource metadata."""
    print("\n" + "=" * 60)
    print("SECTION 3: Noise Cadastre (CKAN)")
    print("=" * 60)

    notes: list[str] = []
    try:
        meta_raw = _fetch_text(_NOISE_CKAN_URL)
        meta = json.loads(meta_raw)
        resources = meta.get("result", {}).get("resources", [])
        print(f"Total resources: {len(resources)}")

        wfs_url: str | None = None
        geojson_url: str | None = None

        for r in resources:
            name = r.get("name", "")
            fmt = r.get("format", "")
            url = r.get("url", "")
            desc = r.get("description", "")
            line = f"[{fmt}] {name!r} -> {url}"
            print(f"  {line}")
            notes.append(line)
            if "wfs" in url.lower() or fmt.upper() == "WFS":
                wfs_url = url
            if fmt.upper() in ("GEOJSON", "JSON") and geojson_url is None:
                geojson_url = url

        # Try fetching a small WFS sample
        if wfs_url:
            print(f"\nTrying WFS endpoint: {wfs_url}")
            try:
                # Request just 5 features
                sample_url = (
                    wfs_url
                    if "?" not in wfs_url
                    else wfs_url.split("?")[0]
                ) + (
                    "?service=WFS&version=1.1.0&request=GetFeature"
                    "&maxFeatures=5&outputFormat=GeoJSON"
                )
                print(f"  Sample URL: {sample_url}")
                sample_raw = _fetch(sample_url, timeout=30)
                sample_data = json.loads(sample_raw)
                feats = sample_data.get("features", [])
                if feats:
                    props = feats[0].get("properties", {})
                    print(f"  Property keys: {sorted(props.keys())}")
                    print("  Sample properties:")
                    for k, v in props.items():
                        print(f"    {k!r}: {v!r}")
                    notes.append(f"WFS sample property keys: {sorted(props.keys())}")
                notes.append(f"WFS sample URL: {sample_url}")
            except Exception as e:
                print(f"  WFS fetch failed: {e}")
                notes.append(f"WFS fetch failed: {e}")

    except Exception as e:
        print(f"CKAN metadata fetch failed: {e}")
        notes.append(f"CKAN fetch failed: {e}")

    notes_path = _RECON_DIR / "noise_notes.txt"
    notes_path.write_text("\n".join(notes), encoding="utf-8")
    print(f"\nSaved: {notes_path}")


def write_field_notes(quartier_path: Path, demo_path: Path) -> None:
    """Write FIELD_NOTES.md summarizing all discovered field names."""
    notes = ["# Field Notes — Neighborhood Intelligence Recon\n"]

    if quartier_path.exists():
        data = json.loads(quartier_path.read_bytes())
        features = data.get("features", [])
        if features:
            props = features[0].get("properties", {})
            notes.append("## Quartier Boundaries (WFS GeoJSON)\n")
            notes.append(f"- Feature count: {len(features)}")
            notes.append(f"- CRS: {data.get('crs', 'N/A')}")
            notes.append("- Property keys:")
            for k, v in props.items():
                notes.append(f"  - `{k}`: e.g. `{v!r}`")
            notes.append("")

    if demo_path.exists():
        lines = demo_path.read_text(encoding="utf-8").splitlines()
        if lines:
            notes.append("## Demographics CSV\n")
            notes.append(f"- Columns: `{lines[0]}`")
            notes.append("- First data row:")
            if len(lines) > 1:
                notes.append(f"  `{lines[1]}`")
            notes.append("")

    field_notes_path = _RECON_DIR / "FIELD_NOTES.md"
    field_notes_path.write_text("\n".join(notes), encoding="utf-8")
    print(f"\nWrote: {field_notes_path}")


if __name__ == "__main__":
    recon_quartier_boundaries()
    recon_demographics()
    recon_noise()

    quartier_path = _RECON_DIR / "quartier_boundaries.json"
    demo_path = _RECON_DIR / "demographics_sample.csv"
    write_field_notes(quartier_path, demo_path)

    print("\n" + "=" * 60)
    print("Recon complete. Check apps/api/data/recon/FIELD_NOTES.md")
    print("=" * 60)
