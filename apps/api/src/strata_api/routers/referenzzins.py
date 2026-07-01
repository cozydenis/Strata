"""Legal intelligence endpoints — Referenzzinssatz rent analysis + Herabsetzungsbegehren.

Public (unauthenticated) for the MVP so exploration is never gated; Pro-gating of
letter generation can be layered on later. All rent math lives in ``strata_api.legal``;
this router only resolves the rate basis and serialises responses.
"""
from __future__ import annotations

import datetime

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from strata_api.config import settings
from strata_api.db.models.listing import Listing
from strata_api.db.models.reference_rate import ReferenceRate
from strata_api.db.session import get_engine
from strata_api.legal import rates
from strata_api.legal.herabsetzung import HerabsetzungContext, render
from strata_api.legal.referenzzins import analyze_rent, permitted_change_pct

router = APIRouter(prefix="/legal", tags=["legal"])


class LetterRequest(BaseModel):
    tenant_name: str = Field(min_length=1)
    tenant_address: str = ""
    landlord_name: str = ""
    landlord_address: str = ""
    property_address: str | None = None
    base_rate: float | None = None
    actual_rent: int | None = None


def _current_rate(s: Session) -> float:
    row = s.execute(
        select(ReferenceRate).order_by(ReferenceRate.valid_from.desc())
    ).scalars().first()
    return row.rate_percent if row else settings.default_reference_rate


def _resolve_base_rate(listing: Listing, override: float | None) -> tuple[float | None, str]:
    """Return (base_rate, basis) — basis is override | known | assumed_from_first_seen | unknown."""
    if override is not None:
        return override, "override"
    if listing.base_reference_rate is not None:
        return listing.base_reference_rate, "known"
    if listing.first_seen is not None:
        inferred = rates.rate_at(listing.first_seen)
        if inferred is not None:
            return inferred, "assumed_from_first_seen"
    return None, "unknown"


def _validate_override(base_rate: float | None) -> None:
    if base_rate is None:
        return
    try:
        permitted_change_pct(base_rate, base_rate)  # validates range + quarter-step
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


def _analysis_message(base_rate: float, current_rate: float, monthly_chf: float | None, direction: str) -> str:
    if direction == "reduction" and monthly_chf is not None:
        return (
            f"This rent is based on a {base_rate:.2f}% reference rate. The current rate is "
            f"{current_rate:.2f}%. You may be entitled to a CHF {abs(monthly_chf):.2f}/month reduction."
        )
    if direction == "reduction":
        return (
            f"The reference rate has dropped from {base_rate:.2f}% to {current_rate:.2f}%, "
            "but the rent amount is unknown so the CHF impact cannot be computed."
        )
    if direction == "increase":
        return f"The reference rate has risen from {base_rate:.2f}% to {current_rate:.2f}%; no reduction applies."
    return "The current reference rate matches this rent's basis; no adjustment applies."


def _build_analysis_response(listing: Listing, current_rate: float, override: float | None) -> dict:
    base_rate, basis = _resolve_base_rate(listing, override)
    resp: dict = {
        "listing_id": listing.id,
        "basis": basis,
        "base_rate": base_rate,
        "current_rate": current_rate,
        "rent_net": listing.rent_net,
        "change_pct": None,
        "monthly_chf": None,
        "new_rent_net": None,
        "direction": None,
        "message": "No reference-rate basis known for this listing; provide base_rate to analyse.",
    }
    if base_rate is None:
        return resp

    change_pct = permitted_change_pct(base_rate, current_rate)
    direction = "reduction" if change_pct < 0 else "increase" if change_pct > 0 else "none"
    resp["change_pct"] = change_pct
    resp["direction"] = direction
    if listing.rent_net is not None:
        analysis = analyze_rent(base_rate, current_rate, listing.rent_net)
        resp["monthly_chf"] = analysis.monthly_chf
        resp["new_rent_net"] = analysis.new_rent_net
    resp["message"] = _analysis_message(base_rate, current_rate, resp["monthly_chf"], direction)
    return resp


@router.get("/reference-rate")
def get_reference_rate() -> dict:
    """Return the current Referenzzinssatz and its published history."""
    with Session(get_engine()) as s:
        rows = s.execute(
            select(ReferenceRate).order_by(ReferenceRate.valid_from.desc())
        ).scalars().all()
    if rows:
        current = {"rate_percent": rows[0].rate_percent, "valid_from": rows[0].valid_from.isoformat()}
    else:
        current = {"rate_percent": settings.default_reference_rate, "valid_from": None}
    return {
        "current": current,
        "history": [
            {"rate_percent": r.rate_percent, "valid_from": r.valid_from.isoformat(), "source": r.source}
            for r in rows
        ],
    }


@router.get("/listings/{listing_id}/rent-analysis")
def rent_analysis(listing_id: int, base_rate: float | None = Query(default=None)) -> dict:
    """Per-listing rent analysis vs. the current reference rate."""
    _validate_override(base_rate)
    with Session(get_engine()) as s:
        listing = s.get(Listing, listing_id)
        if listing is None:
            raise HTTPException(status_code=404, detail="listing not found")
        current_rate = _current_rate(s)
        return _build_analysis_response(listing, current_rate, base_rate)


@router.post("/listings/{listing_id}/herabsetzungsbegehren")
def generate_letter(listing_id: int, req: LetterRequest) -> dict:
    """Generate a Herabsetzungsbegehren letter for a listing (409 if no reduction applies)."""
    _validate_override(req.base_rate)
    with Session(get_engine()) as s:
        listing = s.get(Listing, listing_id)
        if listing is None:
            raise HTTPException(status_code=404, detail="listing not found")
        current_rate = _current_rate(s)
        base_rate, basis = _resolve_base_rate(listing, req.base_rate)
        if base_rate is None:
            raise HTTPException(status_code=409, detail="No reference-rate basis known; provide base_rate.")
        rent_net = req.actual_rent if req.actual_rent is not None else listing.rent_net
        if rent_net is None:
            raise HTTPException(status_code=409, detail="Rent amount unknown; provide actual_rent.")
        analysis = analyze_rent(base_rate, current_rate, rent_net)
        if analysis.direction != "reduction":
            raise HTTPException(status_code=409, detail="No rent reduction applies at the current reference rate.")
        context = HerabsetzungContext(
            tenant_name=req.tenant_name,
            tenant_address=req.tenant_address,
            landlord_name=req.landlord_name,
            landlord_address=req.landlord_address,
            property_address=req.property_address or _listing_address(listing),
            analysis=analysis,
            rent_net=rent_net,
            letter_date=datetime.date.today(),
        )
        letter = render(context)
    return {"listing_id": listing_id, "basis": basis, "letter": letter}


def _listing_address(listing: Listing) -> str:
    head = " ".join(p for p in [listing.street, listing.house_number] if p)
    tail = " ".join(p for p in [str(listing.plz) if listing.plz else None, listing.city] if p)
    if head and tail:
        return f"{head}, {tail}"
    return head or tail or "unbekannte Adresse"
