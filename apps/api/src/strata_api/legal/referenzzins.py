"""Referenzzinssatz-based rent-adjustment math.

Encodes the Swiss legal mechanic for rent changes tied to the mortgage
reference rate (hypothekarischer Referenzzinssatz), per OR Art. 269a lit. b and
VMWG Art. 13 Abs. 1 lit. c: for reference rates below 5%, each 0.25
percentage-point step corresponds to a 3% rent change, compounded.

A drop in the reference rate permits a rent *reduction* (Herabsetzungsanspruch);
a rise permits an *increase*. Offset factors (Teuerung, allgemeine
Kostensteigerungen) are deliberately out of scope for this first version — the
generated documents state that reservation explicitly.
"""
from __future__ import annotations

from dataclasses import dataclass

STEP = 0.25          # reference-rate quantum, in percentage points
STEP_FACTOR = 1.03   # 3% rent change per 0.25-point step
RATE_MIN = 0.25
RATE_MAX = 7.00

_QUARTER_TOLERANCE = 1e-9


def _validate_rate(rate: float) -> None:
    if not RATE_MIN <= rate <= RATE_MAX:
        raise ValueError(f"reference rate {rate} out of range [{RATE_MIN}, {RATE_MAX}]")
    steps = rate / STEP
    if abs(steps - round(steps)) > _QUARTER_TOLERANCE:
        raise ValueError(f"reference rate {rate} is not a multiple of {STEP}")


def permitted_change_pct(base_rate: float, current_rate: float) -> float:
    """Signed permitted rent change in percent (negative = reduction)."""
    _validate_rate(base_rate)
    _validate_rate(current_rate)
    delta_steps = (base_rate - current_rate) / STEP
    pct = (STEP_FACTOR ** (-delta_steps) - 1) * 100
    return round(pct, 2)


def monthly_reduction_chf(rent_net: float, change_pct: float) -> float:
    """Absolute monthly CHF impact of a percentage change on the net rent."""
    if rent_net < 0:
        raise ValueError("rent_net must be non-negative")
    return abs(round(rent_net * change_pct / 100, 2))


@dataclass(frozen=True)
class RentAnalysis:
    """Result of applying a reference-rate change to a specific net rent."""

    base_rate: float
    current_rate: float
    change_pct: float        # signed (negative = reduction)
    monthly_chf: float       # signed (negative = reduction)
    new_rent_net: float
    direction: str           # "reduction" | "increase" | "none"


def analyze_rent(base_rate: float, current_rate: float, rent_net: float) -> RentAnalysis:
    """Full structured analysis for a rent basis vs. the current reference rate."""
    if rent_net < 0:
        raise ValueError("rent_net must be non-negative")
    change_pct = permitted_change_pct(base_rate, current_rate)
    monthly_chf = round(rent_net * change_pct / 100, 2)
    new_rent_net = round(rent_net + monthly_chf, 2)
    if change_pct < 0:
        direction = "reduction"
    elif change_pct > 0:
        direction = "increase"
    else:
        direction = "none"
    return RentAnalysis(
        base_rate=base_rate,
        current_rate=current_rate,
        change_pct=change_pct,
        monthly_chf=monthly_chf,
        new_rent_net=new_rent_net,
        direction=direction,
    )
