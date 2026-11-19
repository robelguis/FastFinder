import re
from typing import Dict, Any, List

PROFICIENCY_BONUSES = {
    "U": 0,
    "T": 2,
    "E": 4,
    "M": 6,
    "L": 8,
}

# Expected max companion stats by tier so level-20 PC scaling never leaks into companions/familiars
COMPANION_TIER_CAPS = {
    "young":   {"max_ac": 22, "max_hp": 45,  "max_mod": 12},
    "mature":  {"max_ac": 28, "max_hp": 90,  "max_mod": 16},
    "nimble":  {"max_ac": 38, "max_hp": 260, "max_mod": 32},
    "savage":  {"max_ac": 37, "max_hp": 280, "max_mod": 32},
    "familiar":{"max_ac": 42, "max_hp": 120, "max_mod": 34},
}


def clean_template_text(text: str) -> str:
    """Strips raw Foundry/template ternary strings, broken tags, and mid-sentence cutoffs."""
    if not text:
        return ""
    # Strip raw Foundry inline math/ternary expressions like (ternary(gte(...)))
    text = re.sub(r"\(ternary\([^)]+\)\)", "", text)
    # Strip raw bracket tags like [untyped] or Joptions:area-damage]
    text = re.sub(r"\[untyped\]|J?options:[a-zA-Z0-9_-]+\]?", "", text)
    # Collapse duplicate whitespace
    text = re.sub(r"\s{2,}", " ", text).strip()
    # Fix dangling trailing commas/articles from truncated descriptions
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
    Normalizes math, clamps companion outliers, flags feat/cause mismatches, and cleans raw text.
    """
    warnings: List[str] = []
    level = max(1, min(20, int(sheet.get("level", 1))))

    # 1. Attribute Cap & Boost Sanity Check
    attrs = sheet.get("attributes", {})
    max_possible_mod = 4 if level < 5 else (5 if level < 10 else (6 if level < 20 else 7))
    high_stats = 0
    for stat in ("str", "dex", "con", "int", "wis", "cha"):
        val = int(attrs.get(stat, 0))
        if val > max_possible_mod:
            warnings.append(f"Clamped {stat.upper()} from +{val} to +{max_possible_mod} for level {level}.")
            val = max_possible_mod
        if val >= 6:
            high_stats += 1
        attrs[stat] = val

    if high_stats > 4:
        warnings.append(f"Attribute allocation warning: {high_stats} attributes at +6 or higher exceeds standard Remaster boost progression.")

    # 2. Recompute Skills from Base Formula (eliminates hardcoded drift)
    has_untrained_improv = any(
        "untrained improvisation" in str(f.get("name", "")).lower()
        for f in sheet.get("feats", [])
    )
    for skill in sheet.get("skills", []):
        stat_key = str(skill.get("ability", "int")).lower()
        attr_mod = attrs.get(stat_key, 0)
        rank = skill.get("rank", "U")
        item_bonus = int(skill.get("item_bonus", 0))
        expected = recompute_proficiency_bonus(level, rank, attr_mod, item_bonus, has_untrained_improv)
        if skill.get("total") != expected:
            warnings.append(f"Adjusted {skill.get('name')} from {skill.get('total')} to {expected} ({rank}).")
            skill["total"] = expected

    # 3. Clamp Companion & Familiar Outliers (prevents +84 Perception / 528 HP bugs)
    for key, default_tier in (("companion", "mature"), ("familiar", "familiar")):
        entity = sheet.get(key)
        if not entity:
            continue
        tier = str(entity.get("tier", default_tier)).lower()
        caps = COMPANION_TIER_CAPS.get(tier, COMPANION_TIER_CAPS[default_tier])

        if int(entity.get("ac", 10)) > caps["max_ac"]:
            warnings.append(f"Clamped {key} AC ({entity['ac']}) to {caps['max_ac']}.")
            entity["ac"] = caps["max_ac"]

        if int(entity.get("max_hp", 10)) > caps["max_hp"]:
            warnings.append(f"Clamped {key} Max HP ({entity['max_hp']}) to {caps['max_hp']}.")
            entity["max_hp"] = caps["max_hp"]

        for field in ("perception", "fort", "ref", "will"):
            if int(entity.get(field, 0)) > caps["max_mod"]:
                warnings.append(f"Clamped {key} {field} (+{entity[field]}) to +{caps['max_mod']}.")
                entity[field] = caps["max_mod"]

        for strike in entity.get("strikes", []):
            if int(strike.get("attack_bonus", 0)) > caps["max_mod"]:
                strike["attack_bonus"] = caps["max_mod"]

    # 4. Class / Cause vs. Feat Compatibility Check
    subclass = str(sheet.get("subclass", "")).lower()
    if "liberator" in subclass:
        for feat in sheet.get("feats", []):
            fname = str(feat.get("name", "")).lower()
            if "selfishness" in fname or "selfish shield" in fname:
                warnings.append(f"Cause mismatch: '{feat.get('name')}' requires Desecrator/Unholy Selfish Shield, incompatible with Liberator.")

    # 5. Text Hygiene Pass on Actions, Feats, and Gear
    for section in ("actions", "feats", "gear"):
        for item in sheet.get(section, []):
            if "description" in item:
                item["description"] = clean_template_text(item["description"])

    sheet["validation_warnings"] = warnings
    return sheet
