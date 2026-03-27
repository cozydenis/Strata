"""Parse Stadt Zürich demographics CSV into structured records per Quartier.

Data source: CKAN dataset bev_bestand_jahr_quartier_alter_herkunft_geschlecht_od3903
CSV file: BEV390OD3903.csv

Relevant columns (discovered via recon):
  StichtagDatJahr -> year (int)
  QuarCd          -> quartier_id as zero-padded string ("011" -> 11)
  QuarLang        -> quartier_name (string)
  HerkunftCd      -> "1"=Swiss ("Schweizer*in"), "2"=Foreign ("Ausländer*in")
  AlterV20Cd      -> age bucket code: "0"=0-19, "1"=20-39, "2"=40-64, "3"=65+
  AnzBestWir      -> count (int)

Our age bucket mapping (actual AlterV20Cd values are the start of each 20-yr range):
  AlterV20Cd "0"   (0-19)   -> "0-17"  (proxy — no finer split in this dataset)
  AlterV20Cd "20"  (20-39)  -> "18-29" proxy
  AlterV20Cd "40"  (40-59)  -> "30-44" proxy
  AlterV20Cd "60"  (60-79)  -> "45-64" proxy
  AlterV20Cd "80"  (80-99)  -> "65+"
  AlterV20Cd "100" (100+)   -> "65+"

Note: The dataset's 20-year buckets don't align perfectly with our 5-bucket display labels.
Labels are proxies; the actual ranges are 0-19, 20-39, 40-59, 60-79, 80+.
"""
from __future__ import annotations

import csv
import io
from dataclasses import dataclass


# Maps AlterV20Cd -> our output bucket key
# Codes are the start of each 20-year band (0, 20, 40, 60, 80, 100)
_AGE_BUCKET_MAP: dict[str, str] = {
    "0": "0-17",    # actual: 0-19
    "20": "18-29",  # actual: 20-39
    "40": "30-44",  # actual: 40-59
    "60": "45-64",  # actual: 60-79
    "80": "65+",    # actual: 80-99
    "100": "65+",   # actual: 100+
}


@dataclass
class QuartierDemographics:
    """Aggregated demographics for a single Quartier in a given year."""

    quartier_id: int
    year: int
    total_population: int
    age_buckets: dict[str, int]  # keys: "0-17", "18-29", "30-44", "45-64", "65+"
    swiss_count: int
    foreign_count: int
    yoy_change: int | None  # difference vs previous year; None if no prior data


def parse_demographics_csv(csv_text: str) -> dict[int, QuartierDemographics]:
    """Parse demographics CSV and return latest-year data keyed by quartier_id.

    Steps:
    1. Read all rows, stripping BOM from header if present.
    2. Collect per-year totals per quartier for yoy_change computation.
    3. Filter to latest year and aggregate: total pop, swiss/foreign split, age buckets.
    4. Compute yoy_change from previous year's total.
    """
    # Strip BOM if present
    text = csv_text.lstrip("\ufeff")

    reader = csv.DictReader(io.StringIO(text))

    # Structure: {year: {quartier_id: {field: value}}}
    # We collect raw counts in two passes.
    # Pass 1: group by (year, quartier_id)
    from collections import defaultdict

    # year_quar_total[year][qid] = total count
    year_quar_total: dict[int, dict[int, int]] = defaultdict(lambda: defaultdict(int))
    # For latest year: more detailed aggregation
    # latest_data[qid] = {"swiss": int, "foreign": int, "age": {bucket: int}, "name": str}
    all_years: set[int] = set()
    rows_by_year: dict[int, list[dict]] = defaultdict(list)

    for row in reader:
        try:
            year = int(row["StichtagDatJahr"])
            qid = int(row["QuarCd"])  # "011" -> 11 via int()
            count = int(row["AnzBestWir"])
        except (KeyError, ValueError):
            continue

        all_years.add(year)
        year_quar_total[year][qid] += count
        rows_by_year[year].append(row)

    if not all_years:
        return {}

    latest_year = max(all_years)
    prev_year = latest_year - 1

    # Aggregate latest-year data per quartier
    result: dict[int, QuartierDemographics] = {}

    # Group latest rows by quartier
    quar_rows: dict[int, list[dict]] = defaultdict(list)
    for row in rows_by_year[latest_year]:
        try:
            qid = int(row["QuarCd"])
        except (KeyError, ValueError):
            continue
        quar_rows[qid].append(row)

    for qid, rows in quar_rows.items():
        swiss = 0
        foreign = 0
        age_buckets: dict[str, int] = {k: 0 for k in ("0-17", "18-29", "30-44", "45-64", "65+")}

        for row in rows:
            try:
                count = int(row["AnzBestWir"])
                herkunft = str(row["HerkunftCd"]).strip()
                age_cd = str(row["AlterV20Cd"]).strip()
            except (KeyError, ValueError):
                continue

            if herkunft == "1":
                swiss += count
            elif herkunft == "2":
                foreign += count

            bucket = _AGE_BUCKET_MAP.get(age_cd)
            if bucket:
                age_buckets[bucket] += count

        total = swiss + foreign

        # Compute yoy_change
        prev_total = year_quar_total.get(prev_year, {}).get(qid)
        yoy_change = (total - prev_total) if prev_total is not None else None

        result[qid] = QuartierDemographics(
            quartier_id=qid,
            year=latest_year,
            total_population=total,
            age_buckets=age_buckets,
            swiss_count=swiss,
            foreign_count=foreign,
            yoy_change=yoy_change,
        )

    return result
