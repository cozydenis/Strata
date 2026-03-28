#!/usr/bin/env python3
"""Filter Swiss GTFS to Zürich area only.

Keeps stops within an expanded Zürich bbox, plus all trips that have
at least one stop in that area, plus all agencies/routes/calendars
referenced by those trips.

Usage:
    python filter_gtfs.py [input.zip] [output.zip]
    Defaults: otp-data/swiss-gtfs.zip → otp-data/zurich-gtfs.zip
"""

import csv
import io
import sys
import zipfile
from pathlib import Path

# Expanded Zürich bbox (includes suburbs + airport + nearby connections)
LON_MIN, LON_MAX = 8.35, 8.75
LAT_MIN, LAT_MAX = 47.25, 47.50


def read_csv(zf: zipfile.ZipFile, name: str) -> list[dict]:
    try:
        with zf.open(name) as f:
            return list(csv.DictReader(io.TextIOWrapper(f, encoding="utf-8-sig")))
    except KeyError:
        return []


def write_csv(out: zipfile.ZipFile, name: str, rows: list[dict], fieldnames: list[str] | None = None) -> None:
    if not rows:
        return
    buf = io.StringIO()
    fields = fieldnames or list(rows[0].keys())
    w = csv.DictWriter(buf, fieldnames=fields, extrasaction="ignore", lineterminator="\r\n")
    w.writeheader()
    w.writerows(rows)
    out.writestr(name, buf.getvalue().encode("utf-8"))


def main(input_path: str, output_path: str) -> None:
    print(f"[filter-gtfs] Reading {input_path}...")
    with zipfile.ZipFile(input_path) as zf:
        stops = read_csv(zf, "stops.txt")
        trips = read_csv(zf, "trips.txt")
        stop_times = read_csv(zf, "stop_times.txt")
        routes = read_csv(zf, "routes.txt")
        agencies = read_csv(zf, "agency.txt")
        calendars = read_csv(zf, "calendar.txt")
        calendar_dates = read_csv(zf, "calendar_dates.txt")
        frequencies = read_csv(zf, "frequencies.txt")
        shapes = read_csv(zf, "shapes.txt")
        transfers = read_csv(zf, "transfers.txt")
        pathways = read_csv(zf, "pathways.txt")
        feed_info = read_csv(zf, "feed_info.txt")

    print(f"[filter-gtfs] Input: {len(stops):,} stops, {len(trips):,} trips, {len(stop_times):,} stop_times")

    # Step 1: stops in bbox
    bbox_stop_ids: set[str] = set()
    for s in stops:
        try:
            lat = float(s["stop_lat"])
            lon = float(s["stop_lon"])
            if LAT_MIN <= lat <= LAT_MAX and LON_MIN <= lon <= LON_MAX:
                bbox_stop_ids.add(s["stop_id"])
        except (ValueError, KeyError):
            pass

    print(f"[filter-gtfs] Stops in Zürich bbox: {len(bbox_stop_ids):,}")

    # Step 2: trips that have at least one stop in bbox
    keep_trip_ids: set[str] = set()
    for st in stop_times:
        if st["stop_id"] in bbox_stop_ids:
            keep_trip_ids.add(st["trip_id"])

    print(f"[filter-gtfs] Trips passing through Zürich: {len(keep_trip_ids):,}")

    # Step 3: filter stop_times to kept trips
    kept_stop_times = [st for st in stop_times if st["trip_id"] in keep_trip_ids]
    # Keep all stops referenced by those stop_times
    keep_stop_ids: set[str] = {st["stop_id"] for st in kept_stop_times}
    # Also keep parent stations (location_type=1) for kept stops
    stop_by_id = {s["stop_id"]: s for s in stops}
    for sid in list(keep_stop_ids):
        s = stop_by_id.get(sid)
        if s and s.get("parent_station"):
            keep_stop_ids.add(s["parent_station"])

    kept_stops = [s for s in stops if s["stop_id"] in keep_stop_ids]

    # Step 4: filter trips, then routes/agencies/calendars
    kept_trips = [t for t in trips if t["trip_id"] in keep_trip_ids]
    keep_route_ids = {t["route_id"] for t in kept_trips}
    kept_routes = [r for r in routes if r["route_id"] in keep_route_ids]
    keep_agency_ids = {r["agency_id"] for r in kept_routes}
    kept_agencies = [a for a in agencies if a["agency_id"] in keep_agency_ids]

    keep_service_ids = {t["service_id"] for t in kept_trips}
    kept_calendars = [c for c in calendars if c["service_id"] in keep_service_ids]
    kept_calendar_dates = [cd for cd in calendar_dates if cd["service_id"] in keep_service_ids]

    # Frequencies for kept trips
    kept_frequencies = [f for f in frequencies if f["trip_id"] in keep_trip_ids]

    # Shapes for kept trips (optional)
    keep_shape_ids = {t["shape_id"] for t in kept_trips if t.get("shape_id")}
    kept_shapes = [s for s in shapes if s.get("shape_id") in keep_shape_ids]

    # Transfers between kept stops
    kept_transfers = [
        t for t in transfers
        if t.get("from_stop_id") in keep_stop_ids and t.get("to_stop_id") in keep_stop_ids
    ]

    # Pathways between kept stops
    kept_pathways = [
        p for p in pathways
        if p.get("from_stop_id") in keep_stop_ids and p.get("to_stop_id") in keep_stop_ids
    ]

    print(f"[filter-gtfs] Output: {len(kept_stops):,} stops, {len(kept_trips):,} trips, {len(kept_stop_times):,} stop_times")
    print(f"[filter-gtfs] Routes: {len(kept_routes):,}, Agencies: {len(kept_agencies):,}, Frequencies: {len(kept_frequencies):,}")

    print(f"[filter-gtfs] Writing {output_path}...")
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as out:
        write_csv(out, "stops.txt", kept_stops)
        write_csv(out, "trips.txt", kept_trips)
        write_csv(out, "stop_times.txt", kept_stop_times)
        write_csv(out, "routes.txt", kept_routes)
        write_csv(out, "agency.txt", kept_agencies)
        if kept_calendars:
            write_csv(out, "calendar.txt", kept_calendars)
        if kept_calendar_dates:
            write_csv(out, "calendar_dates.txt", kept_calendar_dates)
        if kept_frequencies:
            write_csv(out, "frequencies.txt", kept_frequencies)
        if kept_shapes:
            write_csv(out, "shapes.txt", kept_shapes)
        if kept_transfers:
            write_csv(out, "transfers.txt", kept_transfers)
        if kept_pathways:
            write_csv(out, "pathways.txt", kept_pathways)
        if feed_info:
            write_csv(out, "feed_info.txt", feed_info)

    import os
    size_mb = os.path.getsize(output_path) / 1_048_576
    print(f"[filter-gtfs] Done. Output size: {size_mb:.1f} MB")


if __name__ == "__main__":
    script_dir = Path(__file__).parent
    input_zip = sys.argv[1] if len(sys.argv) > 1 else str(script_dir / "otp-data" / "swiss-gtfs.zip")
    output_zip = sys.argv[2] if len(sys.argv) > 2 else str(script_dir / "otp-data" / "zurich-gtfs.zip")
    main(input_zip, output_zip)
