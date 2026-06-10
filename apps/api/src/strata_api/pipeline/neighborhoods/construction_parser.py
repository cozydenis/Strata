"""Parse Stadt Zürich new-construction project stats (BAU501OD5011).

One row per year × Quartier × project status. We keep only the latest year:
- status '2' "Bewilligt harmonisiert" → approved (not yet started)
- status '3' "Baubegonnen"            → under construction
Costs are CHF thousands; 'K' marks values masked for confidentiality.
"""
from __future__ import annotations

import csv
import io

_STATUS_APPROVED = "2"
_STATUS_STARTED = "3"


def parse_construction_csv(text: str) -> dict[int, dict]:
    """Latest-year construction pipeline per quartier_id.

    Returns {quartier_id: {year, approved_projects, started_projects, cost_mchf}}.
    cost_mchf is the sum of unmasked costs in CHF millions, or None when every
    cost for the quartier is masked.
    """
    rows = list(csv.DictReader(io.StringIO(text.lstrip("﻿"))))
    if not rows:
        return {}

    latest_year = max(int(r["StichtagDatJahr"]) for r in rows)

    stats: dict[int, dict] = {}
    for row in rows:
        if int(row["StichtagDatJahr"]) != latest_year:
            continue
        qid = int(row["QuarCd"])
        entry = stats.setdefault(
            qid,
            {"year": latest_year, "approved_projects": 0, "started_projects": 0, "cost_mchf": None},
        )

        count = int(row["AnzBauprojekte"] or 0)
        status = row["ProjektStatusSSZPubl1Cd"]
        if status == _STATUS_APPROVED:
            entry["approved_projects"] += count
        elif status == _STATUS_STARTED:
            entry["started_projects"] += count

        cost_raw = (row.get("BaukostenEffektiv") or "").strip()
        if cost_raw and cost_raw.upper() != "K":
            cost_mchf = round(float(cost_raw) / 1000, 1)
            entry["cost_mchf"] = round((entry["cost_mchf"] or 0.0) + cost_mchf, 1)

    return stats
