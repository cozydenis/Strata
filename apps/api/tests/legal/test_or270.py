"""Tests for the static OR Art. 270 legal-information payload."""
from strata_api.legal.or270 import OR270Info, or270_info


def test_or270_info_is_frozen_dataclass():
    info = or270_info()
    assert isinstance(info, OR270Info)


def test_or270_deadline_is_thirty_days():
    info = or270_info()
    assert info.deadline_days == 30
    assert "30 Tage" in info.deadline_note


def test_or270_mentions_schlichtungsbehoerde():
    info = or270_info()
    blob = " ".join([info.deadline_note, info.schlichtungsbehoerde])
    assert "Schlichtungsbehörde" in blob


def test_or270_conditions_cover_hardship_shortage_increase():
    joined = " ".join(or270_info().conditions).lower()
    assert "hardship" in joined
    assert "shortage" in joined
    assert "increased" in joined or "increase" in joined


def test_or270_assessment_method_is_quartierueblichkeit():
    assert "Quartierüblichkeit" in or270_info().assessment_method


def test_or270_carries_not_legal_advice_disclaimer():
    disclaimer = or270_info().disclaimer
    assert "keine Rechtsberatung" in disclaimer
    assert "not legal advice" in disclaimer


def test_or270_as_dict_serialises_conditions_as_list():
    d = or270_info().as_dict()
    assert isinstance(d["conditions"], list)
    assert d["deadline_days"] == 30
