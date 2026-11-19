import re
from typing import Dict, Any, List

PROFICIENCY_BONUSES = {
    "U": 0,
    "T": 2,
    "E": 4,
    "M": 6,
    "L": 8,
}

COMPANION_TIER_CAPS = {
    "young":    {"max_ac": 22, "max_hp": 45,  "max_mod": 12},
    "mature":   {"max_ac": 28, "max_hp": 90,  "max_mod": 16},
    "nimble":   {"max_ac": 38, "max_hp": 260, "max_mod": 32},
    "savage":   {"max_ac": 37, "max_hp": 280, "max_mod": 32},
    "familiar": {"max_ac": 42, "max_hp": 120, "max_mod": 34},
}

ATTR_PAIRS = [
    ("strength", "str"),
    ("dexterity", "dex"),
    ("constitution", "con"),
    ("intelligence", "int"),
    ("wisdom", "wis"),
    ("charisma", "cha"),
]


def clean_template_text(text: str) -> str:
    """Strips raw Foundry/template ternary strings, broken tags, and mid-sentence cutoffs."""
    if not text or not isinstance(text, str):
        return text or ""
    text = re.sub(r"\(ternary\([^)]+\)\)", "", text)
    text = re.sub(r"\[untyped\]|J?options:[a-zA-Z0-9_-]+\]?", "", text)
    text = re.sub(r"\s{2,}", " ", text).strip()
    if text and text[-1] not in ".!?)\"'":
        text = text.rstrip(",;:- ") + "..."
    return text


def recompute_proficiency_bonus(level: int, rank: str, attr_mod: int, item_bonus: int = 0, untrained_improv: bool = False) -> int:
    """Enforces exact PF2e Remaster proficiency math: Level + Rank + Attribute + Item."""
    rank = (rank or "U").upper()[0]
    if rank == "U":
        prof = level if untrained_improv else 0
    else:
        prof = level + PROFICIENCY_BONUSES.get(rank, 0)
    return prof + attr_mod + item_bonus


def sanitize_and_validate_sheet(sheet: Dict[str, Any]) -> Dict[str, Any]:
    """
    Runs immediately prior to final sheet rendering / PDF export.
    Normalizes math against Pydantic CharacterSheet fields, clamps companion outliers,
    flags feat/cause mismatches, and cleans raw template text.
    """
    warnings: List[str] = []
    level = max(1, min(20, int(sheet.get("level", 1))))

    # 1. Attribute Cap & Boost Sanity Check (supports both full field names and short aliases)
    attrs = sheet.get("attributes", {})
    max_possible_mod = 4 if level < 5 else (5 if level < 10 else (6 if level < 20 else 7))
    high_stats = 0
    short_mods: Dict[str, int] = {}

    for full_key, short_key in ATTR_PAIRS:
        raw_val = attrs[full_key] if full_key in attrs else attrs.get(short_key, 0)
        val = int(raw_val or 0)
        if val > max_possible_mod:
            warnings.append(f"Clamped {short_key.upper()} from +{val} to +{max_possible_mod} for level {level}.")
            val = max_possible_mod
        if val >= 6:
            high_stats += 1
        if full_key in attrs:
            attrs[full_key] = val
        if short_key in attrs:
            attrs[short_key] = val
        short_mods[short_key] = val

    if high_stats > 4:
        warnings.append(f"Attribute allocation warning: {high_stats} attributes at +6 or higher exceeds standard Remaster boost progression.")

    # 2. Recompute Skills from Base Formula (CharacterSheet uses 'all_skills')
    feats = sheet.get("feats") or []
    has_untrained_improv = any(
        "untrained improvisation" in str(f.get("name", "")).lower()
        for f in feats if isinstance(f, dict)
    )
    for skill in sheet.get("all_skills") or []:
        if not isinstance(skill, dict):
            continue
        stat_key = str(skill.get("attribute") or skill.get("ability") or "int").lower()[:3]
        attr_mod = short_mods.get(stat_key, 0)
        rank = skill.get("rank_letter") or "U"
        item_bonus = int(skill.get("item_bonus", 0) or 0)
        expected = recompute_proficiency_bonus(level, rank, attr_mod, item_bonus, has_untrained_improv)
        if skill.get("modifier") != expected:
            warnings.append(f"Adjusted {skill.get('name')} from {skill.get('modifier')} to {expected} ({rank}).")
            skill["modifier"] = expected

    # 3. Clamp Companion & Additional Partner Outliers (CharacterSheet uses 'hp', 'fortitude', 'reflex', 'will')
    partners: List[Dict[str, Any]] = []
    if isinstance(sheet.get("companion"), dict):
        partners.append(sheet["companion"])
    for p in sheet.get("additional_partners") or []:
        if isinstance(p, dict):
            partners.append(p)

    for entity in partners:
        ctype = str(entity.get("creature_type", "")).lower()
        stage = str(entity.get("stage", "")).lower()
        default_tier = "familiar" if ("familiar" in ctype or "pet" in ctype or "familiar" in stage) else "mature"
        tier = str(entity.get("tier") or stage or default_tier).lower()
        caps = next((v for k, v in COMPANION_TIER_CAPS.items() if k in tier), COMPANION_TIER_CAPS[default_tier])

        if int(entity.get("ac", 10) or 10) > caps["max_ac"]:
            warnings.append(f"Clamped {entity.get('name')} AC ({entity['ac']}) to {caps['max_ac']}.")
            entity["ac"] = caps["max_ac"]

        if int(entity.get("hp", 10) or 10) > caps["max_hp"]:
            warnings.append(f"Clamped {entity.get('name')} HP ({entity['hp']}) to {caps['max_hp']}.")
            entity["hp"] = caps["max_hp"]

        for field in ("perception", "fortitude", "reflex", "will"):
            if int(entity.get(field, 0) or 0) > caps["max_mod"]:
                warnings.append(f"Clamped {entity.get('name')} {field} (+{entity[field]}) to +{caps['max_mod']}.")
                entity[field] = caps["max_mod"]

        for strike in entity.get("strikes") or []:
            if not isinstance(strike, dict):
                continue
            for atk_field in ("attack_bonus", "map_second", "map_third"):
                raw_atk = strike.get(atk_field)
                if raw_atk is None:
                    continue
                try:
                    num_atk = int(str(raw_atk).replace("+", "").strip())
                    if num_atk > caps["max_mod"]:
                        strike[atk_field] = f"+{caps['max_mod']}" if isinstance(raw_atk, str) else caps["max_mod"]
                except ValueError:
                    pass

    # 4. Class / Cause vs. Feat Compatibility Check
    sub_obj = sheet.get("subclass")
    subclass = (sub_obj.get("name", "") if isinstance(sub_obj, dict) else str(sub_obj or "")).lower()
    if "liberator" in subclass:
        for feat in feats:
            if not isinstance(feat, dict):
                continue
            fname = str(feat.get("name", "")).lower()
            if "selfishness" in fname or "selfish shield" in fname:
                warnings.append(f"Cause mismatch: '{feat.get('name')}' requires Desecrator/Unholy Selfish Shield, incompatible with Liberator.")

    # 5. Text Hygiene Pass on Feats and Equipment Gear
    for item in feats:
        if isinstance(item, dict) and "description" in item:
            item["description"] = clean_template_text(item["description"])

    equip = sheet.get("equipment")
    if isinstance(equip, dict) and isinstance(equip.get("gear"), list):
        equip["gear"] = [
            clean_template_text(g) if isinstance(g, str) else g
            for g in equip["gear"]
        ]

    sheet["validation_warnings"] = warnings
    return sheet
