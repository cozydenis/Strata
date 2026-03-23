"""Address matching engine — links rental listings to GWR registry entries.

Matching pipeline:
  1. Exact:         normalize(street) + house_number + plz → entrances
  2. Probable:      fuzzy street similarity within same PLZ (difflib, score ≥ 0.85)
  3. Building-only: nearest-entrance geo fallback within 50 m
  4. Unit narrowing: within matched egid, filter by wazim (±0.5) and warea (±10%)
"""
from __future__ import annotations

import difflib
import math
import re
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from strata_api.db.models.entrance import Entrance
from strata_api.db.models.unit import Unit

# ── Constants ─────────────────────────────────────────────────────────────────

_FUZZY_THRESHOLD = 0.85        # minimum SequenceMatcher ratio for "probable"
_GEO_MAX_DIST_M = 50.0         # metres — max distance for geo fallback
_ROOM_TOLERANCE = 0.5          # ±0.5 rooms (Swiss half-room counting)
_AREA_TOLERANCE_PCT = 0.10     # ±10% of area

# Abbreviation expansions applied before comparison
_ABBREV = [
    (re.compile(r"-?str\.$", re.I), "strasse"),
    (re.compile(r"-?str\b", re.I), "strasse"),
    (re.compile(r"-?pl\.$", re.I), "platz"),
    (re.compile(r"-?gss\.$", re.I), "gasse"),
    (re.compile(r"-?g\.$", re.I), "gasse"),
    (re.compile(r"-?weg\.$", re.I), "weg"),
    (re.compile(r"-?allee\.$", re.I), "allee"),
]

# Umlaut → ASCII digraph, so "Mühlgasse" == "Muehlgasse" after normalisation
_UMLAUT = str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "Ä": "ae", "Ö": "oe", "Ü": "ue", "ß": "ss"})


# ── Public types ──────────────────────────────────────────────────────────────

@dataclass
class MatchResult:
    egid: int
    ewid: int | None
    confidence: str  # "exact" | "probable" | "building_only"


# ── Street normalisation ──────────────────────────────────────────────────────

def normalize_street(raw: str | None) -> str:
    """Normalise a street name for comparison.

    * lowercase
    * strip leading/trailing whitespace
    * expand common abbreviations (Str. → strasse, Pl. → platz, …)
    * map umlauts to ASCII digraphs (ä→ae, ö→oe, ü→ue)
    """
    if not raw:
        return ""
    s = raw.strip().translate(_UMLAUT)
    for pattern, replacement in _ABBREV:
        s = pattern.sub(replacement, s)
    return s.lower()


# ── Geo helpers ───────────────────────────────────────────────────────────────

def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Approximate distance in metres between two WGS-84 points."""
    R = 6_371_000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


# ── Unit narrowing ────────────────────────────────────────────────────────────

def _narrow_to_units(
    db: Session,
    egid: int,
    rooms: float | None,
    area_m2: float | None,
    base_confidence: str,
) -> list[MatchResult]:
    """Try to narrow a building match down to individual units.

    Returns a list of MatchResult.  Falls back to building_only if:
    - rooms/area not provided, OR
    - no units in the DB match the criteria.
    """
    if rooms is None and area_m2 is None:
        # Address matched the building but no room/area criteria to narrow further
        return [MatchResult(egid=egid, ewid=None, confidence=base_confidence)]

    stmt = select(Unit).where(Unit.egid == egid)
    units = db.execute(stmt).scalars().all()

    if not units:
        return [MatchResult(egid=egid, ewid=None, confidence="building_only")]

    candidates: list[MatchResult] = []
    for unit in units:
        if rooms is not None and unit.wazim is not None:
            if abs(unit.wazim - rooms) > _ROOM_TOLERANCE:
                continue
        if area_m2 is not None and area_m2 > 0 and unit.warea is not None:
            if abs(unit.warea - area_m2) / area_m2 > _AREA_TOLERANCE_PCT:
                continue
        candidates.append(MatchResult(egid=egid, ewid=unit.ewid, confidence=base_confidence))

    if not candidates:
        return [MatchResult(egid=egid, ewid=None, confidence="building_only")]
    return candidates


# ── Main matching entry point ─────────────────────────────────────────────────

def match_listing(
    db: Session,
    street: str | None,
    house_number: str | None,
    plz: int | None,
    rooms: float | None = None,
    area_m2: float | None = None,
    lat: float | None = None,
    lng: float | None = None,
) -> list[MatchResult]:
    """Match a rental listing to GWR entrance(s) and optionally unit(s).

    Returns a list of MatchResult sorted by confidence (exact first).
    Returns [] if no match is found.
    """
    norm_street = normalize_street(street)

    # ── Step 1: Exact match ────────────────────────────────────────────────────
    if norm_street and house_number and plz:
        stmt = select(Entrance).where(Entrance.dplz4 == plz)
        candidates = db.execute(stmt).scalars().all()

        exact_egids: list[int] = []
        for ent in candidates:
            if (
                normalize_street(ent.strname) == norm_street
                and (ent.deinr or "").strip() == house_number.strip()
            ):
                exact_egids.append(ent.egid)

        if exact_egids:
            results: list[MatchResult] = []
            for egid in exact_egids:
                results.extend(_narrow_to_units(db, egid, rooms, area_m2, "exact"))
            return results

    # ── Step 2: Probable (fuzzy) ───────────────────────────────────────────────
    if norm_street and house_number and plz:
        stmt = select(Entrance).where(Entrance.dplz4 == plz)
        candidates = db.execute(stmt).scalars().all()

        probable_egids: list[int] = []
        for ent in candidates:
            ratio = difflib.SequenceMatcher(
                None, norm_street, normalize_street(ent.strname)
            ).ratio()
            if ratio >= _FUZZY_THRESHOLD and (ent.deinr or "").strip() == house_number.strip():
                probable_egids.append(ent.egid)

        if probable_egids:
            results = []
            for egid in probable_egids:
                results.extend(_narrow_to_units(db, egid, rooms, area_m2, "probable"))
            return results

    # ── Step 3: Geo fallback ───────────────────────────────────────────────────
    # Falls through here when exact/fuzzy both fail (address not in GWR, or PLZ
    # from a different canton). Use coordinates to find the nearest entrance.
    if lat is not None and lng is not None:
        # Bounding box pre-filter: ~50m ≈ 0.0005° lat, ~0.0007° lon at 47°N
        _BBOX_DEG = 0.001  # ~110m — generous to ensure we don't miss nearby entrances
        stmt = select(Entrance).where(
            Entrance.lat.isnot(None),
            Entrance.lon.isnot(None),
            Entrance.lat.between(lat - _BBOX_DEG, lat + _BBOX_DEG),
            Entrance.lon.between(lng - _BBOX_DEG, lng + _BBOX_DEG),
        )
        candidates = db.execute(stmt).scalars().all()

        best_ent: Entrance | None = None
        best_dist = float("inf")
        for ent in candidates:
            dist = _haversine_m(lat, lng, ent.lat, ent.lon)
            if dist < best_dist:
                best_dist = dist
                best_ent = ent

        if best_ent is not None and best_dist <= _GEO_MAX_DIST_M:
            return [MatchResult(egid=best_ent.egid, ewid=None, confidence="building_only")]

    return []
