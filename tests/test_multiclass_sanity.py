import pytest

from app.engine.generator import PF2eGenerator


@pytest.mark.parametrize(
    "kwargs",
    [
        {
            "ancestry_name": "Awakened Animal",
            "heritage_name": "River Otter (Swimming Animal)",
            "class_name": "Ranger",
            "subclass_name": "Flurry",
            "level": 1,
        },
        {
            "ancestry_name": "Nagaji",
            "heritage_name": "Cobra-Crested Nagaji",
            "class_name": "Investigator",
            "subclass_name": "Alchemical Sciences",
            "level": 1,
        },
        {
            "ancestry_name": "Human",
            "heritage_name": "Skilled Heritage",
            "class_name": "Ranger",
            "subclass_name": "Precision",
            "level": 1,
        },
    ],
)
def test_multiclass_sheet_invariants(kwargs):
    gen = PF2eGenerator()
    sheet = gen.generate(**kwargs)

    cls_low = (sheet.character_class or "").lower()
    sub_low = ((sheet.subclass.name if sheet.subclass else "") or kwargs.get("subclass_name") or "").lower()
    feat_names_low = {(f.name or "").lower() for f in (sheet.feats or [])}

    # 1. Core class & subclass features on Ranger
    if "ranger" in cls_low:
        assert "hunt prey" in feat_names_low
        if "flurry" in sub_low:
            assert "hunter's edge: flurry" in feat_names_low
        elif "precision" in sub_low:
            assert "hunter's edge: precision" in feat_names_low
        elif "outwit" in sub_low:
            assert "hunter's edge: outwit" in feat_names_low

    # 2. No crossbow-specific feats when no crossbow is in weapons/strikes
    eq = sheet.equipment
    wep_names = [getattr(w, "name", "") for w in (getattr(eq, "weapons", None) or [])]
    strike_names = [getattr(s, "name", "") for s in (getattr(eq, "strikes", None) or [])]
    wep_blob = " ".join(wep_names + strike_names).lower()
    if "crossbow" not in wep_blob:
        assert "crossbow ace" not in feat_names_low

    # 3. Valid proficiency rank letters and modifiers across all_skills
    valid_ranks = {"U", "T", "E", "M", "L"}
    for sk in (sheet.all_skills or []):
        assert sk.rank_letter in valid_ranks
        assert isinstance(sk.modifier, int)

    # 4. Companion & additional_partners basic sanity
    partners = ([sheet.companion] if sheet.companion else []) + list(sheet.additional_partners or [])
    for p in partners:
        assert p.name
        assert p.ac >= 10
