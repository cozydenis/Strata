"""Render watch events into a plain-text email digest.

Pure functions only — no I/O. The input is the list of event dicts the
watchlist router produces (see strata_api.watch_events). The philosophy is the
one from the vision: rare, high-signal, restrained. Zero events → no email.
"""
from __future__ import annotations

from dataclasses import dataclass

# Event type → human label used in the body.
_LABELS = {
    "new_listing": "New listing",
    "price_change": "Price change",
    "listing_gone": "Listing removed",
}

_FOOTER = (
    "You're receiving this because you're watching these buildings on Strata. "
    "Manage your watches on the site, or reply to this email to stop."
)


@dataclass(frozen=True)
class Digest:
    """A rendered email ready to hand to an EmailSender."""

    subject: str
    body: str


def _num(value: float | int | str | None) -> str | None:
    """Format a number without a trailing .0 (3.5 → '3.5', 80.0 → '80').

    Accepts strings too — listing_history rent values arrive as strings.
    Non-numeric values are returned unchanged; None stays None.
    """
    if value is None:
        return None
    if isinstance(value, str):
        try:
            value = float(value)
        except ValueError:
            return value
    return f"{value:g}"


def _building_header(event: dict) -> str:
    """A single-line building address, or a stable fallback on the EGID."""
    street = event.get("street")
    house_number = event.get("house_number")
    line1 = " ".join(str(p) for p in (street, house_number) if p)

    plz = event.get("plz")
    city = event.get("city")
    line2 = " ".join(str(p) for p in (plz, city) if p)

    header = ", ".join(p for p in (line1, line2) if p)
    return header or f"Building {event['egid']}"


def _price(value: float | int | None) -> str | None:
    formatted = _num(value)
    return f"CHF {formatted}" if formatted is not None else None


def _detail(event: dict) -> str:
    """The '3.5 Zimmer, 80 m², CHF 2000/Monat' style tail of a listing line."""
    parts: list[str] = []
    rooms = _num(event.get("rooms"))
    if rooms is not None:
        parts.append(f"{rooms} Zimmer")
    area = _num(event.get("area_m2"))
    if area is not None:
        parts.append(f"{area} m²")
    rent = _price(event.get("rent_gross"))
    if rent is not None:
        parts.append(f"{rent}/Monat")
    return ", ".join(parts)


def _event_line(event: dict) -> str:
    label = _LABELS.get(event["type"], event["type"])
    if event["type"] == "price_change":
        old = _price(event.get("old_value"))
        new = _price(event.get("new_value"))
        change = " → ".join(p for p in (old, new) if p is not None)
        detail = f"Miete {change}/Monat" if change else _detail(event)
    else:
        detail = _detail(event)

    head = f"  • {label}"
    line = f"{head} — {detail}" if detail else head

    url = event.get("source_url")
    if url:
        return f"{line}\n    {url}"
    return line


def render_digest(events: list[dict]) -> Digest | None:
    """Group events by building and render subject + body. None if no events."""
    if not events:
        return None

    # Group by building header, preserving first-seen order of both groups
    # and the events within each group.
    groups: dict[str, list[dict]] = {}
    for event in events:
        groups.setdefault(_building_header(event), []).append(event)

    count = len(events)
    noun = "update" if count == 1 else "updates"
    building_noun = "a building" if len(groups) == 1 else "buildings"
    subject = f"Strata: {count} {noun} on {building_noun} you're watching"

    sections: list[str] = []
    for header, group in groups.items():
        lines = "\n".join(_event_line(event) for event in group)
        sections.append(f"{header}\n{lines}")

    body = (
        "Here's what moved on the homes you're watching.\n\n"
        + "\n\n".join(sections)
        + "\n\n—\n"
        + _FOOTER
    )
    return Digest(subject=subject, body=body)
