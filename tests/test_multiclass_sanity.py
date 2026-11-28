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
FAMILIAR_SOURCE_EXACT = {
    "familiar",
    "marine ally",
    "leshy familiar",
    "elemental familiar",
    "shadow familiar",
    "spirit guide",
    "glyph familiar",
    "call wizardly tools",
    "witch dedication",
    "familiar master dedication",
    "leaf order",
}


def _has_familiar_granting_source(sheet) -> bool:
    cls_low = (getattr(sheet, "character_class", None) or "").strip().lower()
    sub_low = ((getattr(sheet, "subclass", None).name if getattr(sheet, "subclass", None) else "") or "").strip().lower()
    arch_low = (getattr(sheet, "archetype", None) or "").strip().lower()

    if cls_low == "witch" or "leaf order" in sub_low:
        return True
    if any(k in arch_low for k in ("witch", "familiar master")):
        return True

    for f in (getattr(sheet, "feats", None) or []):
        fn = (getattr(f, "name", None) or "").strip().lower()
        if not fn or "spell familiarity" in fn or "weapon familiarity" in fn:
            continue
        if fn in FAMILIAR_SOURCE_EXACT or fn.endswith(" familiar") or " familiar (" in fn:
            return True
    return False


def test_familiar_requires_valid_source_and_no_strikes():
    gen = PF2eGenerator()
    for _ in range(30):
        sheet = gen.generate(level=1)
        partners = ([sheet.companion] if getattr(sheet, "companion", None) else []) + list(getattr(sheet, "additional_partners", None) or [])
        for partner in partners:
            ctype = (getattr(partner, "creature_type", None) or "").strip().lower()
            if "familiar" in ctype and "companion" not in ctype:
                assert _has_familiar_granting_source(sheet), (
                    f"Familiar {partner.name!r} appeared on {sheet.name!r} ({sheet.character_class}) "
                    f"with feats {[f.name for f in (sheet.feats or [])]}"
                )
                assert len(getattr(partner, "strikes", None) or []) == 0, (
                    f"Familiar {partner.name!r} should not carry strike rows"
                )
def test_bear_companion_base_stats_and_sheet_traits():
    gen = PF2eGenerator()
    sheet = gen.generate(
        ancestry_name="Leshy",
        heritage_name="Gourd Leshy",
        class_name="Ranger",
        subclass_name="Flurry",
        level=1,
    )
    assert len(sheet.traits or []) >= 2
    comp = resolve_companion_check = sheet.companion
    if comp and "bear" in (comp.name or "").lower() and (comp.stage or "").lower() == "young":
        assert int(str((comp.attributes or {}).get("CON", 0)).lstrip("+")) == 2
        assert (comp.attributes or {}).get("STR") == "+3"
