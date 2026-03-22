"""Deduplication logic: Stadt Zürich records win over Kanton Zürich."""
from __future__ import annotations

from strata_api.pipeline.schemas import BuildingRecord, EntranceRecord, UnitRecord


def extract_stadt_egids(buildings: list[BuildingRecord]) -> frozenset[int]:
    """Return the set of EGIDs present in Stadt Zürich data."""
    return frozenset(b.egid for b in buildings)


def filter_kanton_buildings(
    kanton: list[BuildingRecord],
    stadt_egids: frozenset[int],
) -> list[BuildingRecord]:
    """Drop kanton buildings whose EGID is already covered by Stadt Zürich."""
    return [b for b in kanton if b.egid not in stadt_egids]


def filter_kanton_entrances(
    kanton: list[EntranceRecord],
    stadt_egids: frozenset[int],
) -> list[EntranceRecord]:
    """Drop kanton entrances whose parent EGID is already covered by Stadt Zürich."""
    return [e for e in kanton if e.egid not in stadt_egids]


def filter_kanton_units(
    kanton: list[UnitRecord],
    stadt_egids: frozenset[int],
) -> list[UnitRecord]:
    """Drop kanton units whose parent EGID is already covered by Stadt Zürich."""
    return [u for u in kanton if u.egid not in stadt_egids]
