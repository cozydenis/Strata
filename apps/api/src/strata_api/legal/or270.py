"""OR Art. 270 — static legal-information payload for the initial-rent challenge.

Keeps the reviewed legal copy in one place. A tenant may contest the INITIAL
rent before the Schlichtungsbehörde within 30 days of taking over the flat if
one of the statutory conditions is met (personal/family hardship, a local
housing shortage — in Zurich the shortage is regularly acknowledged — or a
significant increase versus the previous tenancy). The assessment uses the
"absolute method" via Quartierüblichkeit (OR Art. 269a lit. a).

German legal terms are paired with English explanations, matching
``legal/herabsetzung.py``. Nothing here is legal advice.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OR270Info:
    """Reviewed, static legal-information payload about OR Art. 270."""

    article: str
    deadline_days: int
    deadline_note: str
    conditions: tuple[str, ...]
    assessment_method: str
    schlichtungsbehoerde: str
    disclaimer: str

    def as_dict(self) -> dict:
        """Serialise for the API response (tuples become lists)."""
        return {
            "article": self.article,
            "deadline_days": self.deadline_days,
            "deadline_note": self.deadline_note,
            "conditions": list(self.conditions),
            "assessment_method": self.assessment_method,
            "schlichtungsbehoerde": self.schlichtungsbehoerde,
            "disclaimer": self.disclaimer,
        }


_INFO = OR270Info(
    article="OR Art. 270 (Anfechtung des Anfangsmietzinses)",
    deadline_days=30,
    deadline_note=(
        "Frist: 30 Tage / within 30 days of taking over the flat (Übernahme der Wohnung) "
        "you may contest the initial rent before the Schlichtungsbehörde."
    ),
    conditions=(
        "Persönliche oder familiäre Notlage / personal or family hardship compelling you "
        "to accept the contract.",
        "Wohnungsmangel / local housing shortage — in Zurich this condition is regularly "
        "acknowledged as satisfied.",
        "Erhebliche Erhöhung / the rent was significantly increased versus the previous "
        "tenancy's rent.",
    ),
    assessment_method=(
        "Absolute Methode via Quartierüblichkeit / the absolute method: comparison with "
        "rents customary in the quarter for comparable objects (OR Art. 269a lit. a)."
    ),
    schlichtungsbehoerde=(
        "Schlichtungsbehörde in Mietsachen / the free tenancy mediation authority for your "
        "district is the body that hears an initial-rent challenge (Mietschlichtungsbehörde "
        "des Bezirks)."
    ),
    disclaimer=(
        "Hinweis: Dies ist eine indikative Analyse und keine Rechtsberatung. / This is an "
        "indicative analysis, not legal advice. Verify the facts and deadlines for your case."
    ),
)


def or270_info() -> OR270Info:
    """Return the reviewed static OR Art. 270 information payload."""
    return _INFO
