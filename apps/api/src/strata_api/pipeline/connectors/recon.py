"""
Phase A reconnaissance: download sample responses from Flatfox and Homegate.

Run from the api directory:
    python -m strata_api.pipeline.connectors.recon

Saves raw samples to apps/api/data/samples/.
"""

import json
import re
import time
import urllib.request
from pathlib import Path

SAMPLES_DIR = Path(__file__).resolve().parents[5] / "data" / "samples"

# Zürich bbox (rough)
FLATFOX_SEARCH_URL = (
    "https://flatfox.ch/en/search/"
    "?east=8.61&north=47.42&south=47.34&west=8.47&take=3&offer_type=RENT"
)

HOMEGATE_SEARCH_URL = (
    "https://www.homegate.ch/rent/real-estate/city-zurich/matching-list?ep=1"
)

HEADERS_JSON = {
    "Accept": "application/json",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
}

HEADERS_HTML = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "de-CH,de;q=0.9,en;q=0.8",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
}


def fetch(url: str, headers: dict) -> bytes:
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


def recon_flatfox() -> None:
    print("=== FLATFOX SEARCH ===")
    print(f"GET {FLATFOX_SEARCH_URL}")
    data = fetch(FLATFOX_SEARCH_URL, HEADERS_JSON)
    parsed = json.loads(data)
    out = SAMPLES_DIR / "flatfox_search.json"
    out.write_text(json.dumps(parsed, indent=2, ensure_ascii=False))
    print(f"Saved {out} ({len(data)} bytes)")

    # Print top-level keys and first result shape
    print(f"Top-level keys: {list(parsed.keys()) if isinstance(parsed, dict) else type(parsed)}")
    if isinstance(parsed, dict):
        for k, v in parsed.items():
            if isinstance(v, list) and v:
                print(f"\nFirst item in '{k}':")
                print(json.dumps(v[0], indent=2, ensure_ascii=False)[:2000])
                break
            else:
                print(f"  {k}: {repr(v)[:200]}")
    elif isinstance(parsed, list) and parsed:
        print("\nFirst item:")
        print(json.dumps(parsed[0], indent=2, ensure_ascii=False)[:2000])


def recon_homegate() -> None:
    print("\n=== HOMEGATE SEARCH ===")
    print(f"GET {HOMEGATE_SEARCH_URL}")
    time.sleep(2.5)  # be polite
    html = fetch(HOMEGATE_SEARCH_URL, HEADERS_HTML)
    html_text = html.decode("utf-8", errors="replace")

    # Save raw HTML
    html_out = SAMPLES_DIR / "homegate_search.html"
    html_out.write_bytes(html)
    print(f"Saved raw HTML: {html_out} ({len(html)} bytes)")

    # Extract __INITIAL_STATE__
    match = re.search(
        r"window\.__INITIAL_STATE__\s*=\s*(\{.*?\});\s*(?:window\.|</script>)",
        html_text,
        re.DOTALL,
    )
    if not match:
        # Fallback: find the script tag with __INITIAL_STATE__
        match = re.search(
            r"window\.__INITIAL_STATE__\s*=\s*(\{.+)",
            html_text,
            re.DOTALL,
        )

    if match:
        raw_json = match.group(1)
        # Trim to valid JSON (greedy match may overshoot)
        # Use json decoder to find boundary
        decoder = json.JSONDecoder()
        try:
            parsed, end_idx = decoder.raw_decode(raw_json)
            out = SAMPLES_DIR / "homegate_search.json"
            out.write_text(json.dumps(parsed, indent=2, ensure_ascii=False))
            print(f"Extracted __INITIAL_STATE__ → {out}")
            # Print top-level structure
            print(f"Top-level keys: {list(parsed.keys()) if isinstance(parsed, dict) else type(parsed)}")
            _inspect_homegate_structure(parsed)
        except json.JSONDecodeError as e:
            print(f"JSON parse failed: {e}")
            # Save raw extract for manual inspection
            raw_out = SAMPLES_DIR / "homegate_initial_state_raw.txt"
            raw_out.write_text(raw_json[:50000])
            print(f"Saved raw extract to {raw_out}")
    else:
        print("WARNING: __INITIAL_STATE__ not found in page")
        # Check what script tags look like
        scripts = re.findall(r"<script[^>]*>(.*?)</script>", html_text, re.DOTALL)
        print(f"Found {len(scripts)} script tags")
        for i, s in enumerate(scripts[:5]):
            if "window." in s or "INITIAL" in s or "listings" in s.lower():
                print(f"  Script {i} (first 500 chars): {s[:500]}")


def _inspect_homegate_structure(state: dict, depth: int = 0, max_depth: int = 3) -> None:
    if depth >= max_depth:
        return
    indent = "  " * depth
    for key, val in state.items():
        if isinstance(val, dict):
            print(f"{indent}{key}: {{...{len(val)} keys}}")
            if depth < 2 and key in ("listings", "resultList", "searchResult", "results", "items"):
                _inspect_homegate_structure(val, depth + 1, max_depth)
        elif isinstance(val, list):
            print(f"{indent}{key}: [{len(val)} items]")
            if val and depth < 2 and key in ("listings", "resultList", "results", "items", "listing"):
                print(f"{indent}  First item keys: {list(val[0].keys()) if isinstance(val[0], dict) else val[0]}")
        else:
            print(f"{indent}{key}: {repr(val)[:100]}")


if __name__ == "__main__":
    SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Saving samples to: {SAMPLES_DIR}\n")
    recon_flatfox()
    recon_homegate()
    print("\nDone. Inspect samples/ before writing any parsers.")
