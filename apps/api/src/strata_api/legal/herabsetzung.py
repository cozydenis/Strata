"""Herabsetzungsbegehren (rent-reduction request) letter generation.

Produces a formatted German letter a tenant can send to their landlord or
Verwaltung when the Referenzzinssatz has dropped below the level their rent was
last based on (OR Art. 270a i.V.m. Art. 269a lit. b OR, VMWG Art. 13).

This is a document template, not legal advice: the rendered letter carries an
explicit reservation for offset factors (Teuerung, Kostensteigerungen), a
Schlichtungsbehörde reference, and a "keine Rechtsberatung" disclaimer.
"""
from __future__ import annotations

import datetime
from dataclasses import dataclass

from strata_api.legal.referenzzins import RentAnalysis

_MONTHS_DE = {
    1: "Januar", 2: "Februar", 3: "März", 4: "April", 5: "Mai", 6: "Juni",
    7: "Juli", 8: "August", 9: "September", 10: "Oktober", 11: "November", 12: "Dezember",
}


def _format_date_de(d: datetime.date) -> str:
    return f"{d.day}. {_MONTHS_DE[d.month]} {d.year}"


def _format_chf(amount: float) -> str:
    return f"CHF {amount:,.2f}".replace(",", "'")


@dataclass(frozen=True)
class HerabsetzungContext:
    tenant_name: str
    tenant_address: str
    landlord_name: str
    landlord_address: str
    property_address: str
    analysis: RentAnalysis
    rent_net: float
    letter_date: datetime.date


_TEMPLATE = """{tenant_name}
{tenant_address}


{landlord_name}
{landlord_address}


{letter_date}
Einschreiben


Herabsetzungsbegehren für die Mietwohnung {property_address}

Sehr geehrte Damen und Herren

Der hypothekarische Referenzzinssatz, auf dem mein aktueller Mietzins basiert, ist
gesunken. Gestützt auf Art. 270a OR in Verbindung mit Art. 269a lit. b OR und
Art. 13 VMWG beantrage ich hiermit eine Herabsetzung des Netto-Mietzinses.

- Referenzzinssatz bei letzter Mietzinsfestsetzung: {base_rate}
- Aktueller Referenzzinssatz: {current_rate}
- Zulässige Mietzinsherabsetzung: {change_pct}
- Aktueller Netto-Mietzins: {rent_net_chf}
- Beantragte Herabsetzung: {monthly_chf} pro Monat
- Neuer Netto-Mietzins: {new_rent_chf}

Ich ersuche Sie, die Mietzinsherabsetzung auf den nächstmöglichen Kündigungstermin
umzusetzen und mir die Anpassung schriftlich zu bestätigen.

Der genannte Betrag versteht sich vorbehältlich einer Verrechnung mit
aufgelaufener Teuerung und allgemeinen Kostensteigerungen.

Sollten Sie diesem Begehren nicht entsprechen, behalte ich mir vor, fristgerecht
die Schlichtungsbehörde in Mietsachen anzurufen.

Freundliche Grüsse


{tenant_name}


---
Hinweis: Dieses Schreiben wurde automatisch als Vorlage erstellt und stellt
keine Rechtsberatung dar. Prüfen Sie die Angaben anhand Ihres Mietvertrags."""


def render(context: HerabsetzungContext) -> str:
    """Render the Herabsetzungsbegehren letter text from a context."""
    if not context.tenant_name.strip():
        raise ValueError("tenant_name is required")
    a = context.analysis
    return _TEMPLATE.format(
        tenant_name=context.tenant_name,
        tenant_address=context.tenant_address,
        landlord_name=context.landlord_name,
        landlord_address=context.landlord_address,
        property_address=context.property_address,
        letter_date=_format_date_de(context.letter_date),
        base_rate=f"{a.base_rate:.2f}%",
        current_rate=f"{a.current_rate:.2f}%",
        change_pct=f"{abs(a.change_pct):.2f}%",
        rent_net_chf=_format_chf(context.rent_net),
        monthly_chf=_format_chf(abs(a.monthly_chf)),
        new_rent_chf=_format_chf(abs(a.new_rent_net)),
    )
