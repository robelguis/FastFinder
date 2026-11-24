import re
from typing import Any, Dict, List


def audit_remaster_sheet(sheet: Dict[str, Any]) -> List[str]:
    """Return human-readable PF2e Remaster consistency warnings for a generated sheet dict."""
    issues: List[str] = []
    level = int(sheet.get("level") or 1)
    ancestry = str(sheet.get("ancestry") or "").lower()
    senses = str(sheet.get("senses") or "")
    skills = sheet.get("all_skills") or sheet.get("skills") or []
    feats = sheet.get("feats") or []
    focus = sheet.get("focus_spells") or {}
    companion = sheet.get("companion")

    bad_tokens = ("chosen lore", "tbd", "ternary(", "gte(", "undefined")
    for sk in skills:
        sk_name = sk.get("name", "") if isinstance(sk, dict) else getattr(sk, "name", "")
        if any(tok in str(sk_name).lower() for tok in bad_tokens):
            issues.append(f"Placeholder/unresolved skill name: '{sk_name}'")

    low_light_ancestries = ("centaur", "elf", "gnome", "goblin", "leshy", "minotaur", "sprite")
    if any(a in ancestry for a in low_light_ancestries) and senses.strip().lower() == "normal":
        issues.append(f"Ancestry '{sheet.get('ancestry')}' reports Senses='Normal' instead of Low-Light Vision/senses")

    feat_names = [
        (f.get("name", "") if isinstance(f, dict) else getattr(f, "name", "")).lower()
        for f in feats
    ]
    skill_names_lower = {
        (s.get("name", "") if isinstance(s, dict) else getattr(s, "name", "")).lower()
        for s in skills
    }
    if any("living monolith dedication" in fn for fn in feat_names):
        if "ancient osirion lore" not in skill_names_lower:
            issues.append("Living Monolith Dedication present, but 'Ancient Osirion Lore' is missing from skills")

    if level >= 15 and isinstance(companion, dict):
        comp_ac = companion.get("ac")
        if isinstance(comp_ac, (int, float)) and comp_ac < 32:
            issues.append(f"Level {level} companion/eidolon AC ({comp_ac}) looks low for high-level play")

    max_focus = focus.get("max_focus_points") if isinstance(focus, dict) else getattr(focus, "max_focus_points", None)
    if level >= 15 and isinstance(max_focus, (int, float)) and max_focus < 1:
        issues.append(f"Level {level} focus pool max ({max_focus}) is below 1")

    for field_key in ("senses", "background_description", "ancestry_description"):
        val = str(sheet.get(field_key) or "")
        if re.search(r"\$[^$]+\$", val):
            issues.append(f"Raw dollar-sign math markup found in '{field_key}'")

    return issues


def test_audit_flags_common_anomalies():
    sample_sheet = {
        "level": 20,
        "ancestry": "Centaur",
        "senses": "Normal",
        "all_skills": [{"name": "Chosen Lore", "rank": 2}],
        "feats": [{"name": "Living Monolith Dedication"}],
        "companion": {"ac": 28},
        "focus_spells": {"max_focus_points": 1},
    }
    found = audit_remaster_sheet(sample_sheet)
    print("\nDetected issues:", found)
    assert any("Chosen Lore" in msg for msg in found)
    assert any("Senses='Normal'" in msg for msg in found)
    assert any("Ancient Osirion Lore" in msg for msg in found)
    assert any("companion/eidolon AC (28)" in msg for msg in found)


def test_audit_live_level20_centaur_summoner():
    from app.engine.generator import PF2eGenerator

    gen = PF2eGenerator()
    sheet_obj = gen.generate(
        ancestry_name="Centaur",
        class_name="Summoner",
        background_name="Union Representative",
        archetype_name="Living Monolith",
        char_name="Ursicka Dusk-Prowler",
        level=20,
        use_dedication=True,
        heritage_name="Plain-Runner Centaur",
        subclass_name="Fey Eidolon",
    )
    sheet_dict = (
        sheet_obj.model_dump()
        if hasattr(sheet_obj, "model_dump")
        else (sheet_obj.dict() if hasattr(sheet_obj, "dict") else dict(sheet_obj))
    )
    issues = audit_remaster_sheet(sheet_dict)
    print("\nLive Level 20 Centaur Summoner audit issues:", issues)
    assert isinstance(issues, list)
