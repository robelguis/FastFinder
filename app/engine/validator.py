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
    "familiar":  {"max_ac": 42, "max_hp": 120, "max_mod": 34},
    "eidolon":   {"max_ac": 46, "max_hp": 450, "max_mod": 38},
    "construct": {"max_ac": 44, "max_hp": 350, "max_mod": 36},
    "companion": {"max_ac": 44, "max_hp": 350, "max_mod": 36},
}

ATTR_PAIRS = [
    ("strength", "str"),
    ("dexterity", "dex"),
    ("constitution", "con"),
    ("intelligence", "int"),
    ("wisdom", "wis"),
    ("charisma", "cha"),
]


def _fold_strike_damage_modifiers(dmg_str: str) -> str:
    """Collapses chained +/- integer modifiers on a leading dice expression (preserving any trailing notes)."""
    if not dmg_str or not isinstance(dmg_str, str):
        return dmg_str
    s = dmg_str.strip()
    m = re.match(r"^(\d+d\d+)\s*((?:\s*[+-]\s*\d+){2,})(.*)$", s)
    if not m:
        return s
    dice_part, tail, suffix = m.group(1), m.group(2), m.group(3)
    compact_tail = re.sub(r"\s+", "", tail)
    total_mod = sum(int(tok) for tok in re.findall(r"[+-]\d+", compact_tail))
    if total_mod > 0:
        folded = f"{dice_part}+{total_mod}"
    elif total_mod < 0:
        folded = f"{dice_part}{total_mod}"
    else:
        folded = dice_part
    return f"{folded}{suffix}"


def clean_template_text(text: str) -> str:
    """Strips raw Foundry/template strings, $ math wrappers, and mid-sentence/mid-word cutoffs."""
    if not text or not isinstance(text, str):
        return text or ""
    text = re.sub(r"\(ternary\([^)]+\)\)", "", text)
    text = re.sub(r"\[untyped\]|J?options:[a-zA-Z0-9_-]+\]?", "", text)
    # Unwrap $...$ math delimiters while preserving inner content, then strip stray $
    text = re.sub(r"\$([^$]+?)\$", r"\1", text)
    text = text.replace("$", "")
    text = re.sub(r"\s{2,}", " ", text).strip()

    # If already ending with ellipsis, clean up any split word right before '...'
    if text.endswith("..."):
        stem = text[:-3].rstrip()
        if stem and stem[-1].isalpha():
            last_space = stem.rfind(" ")
            if last_space > 0:
                candidate = stem[:last_space].rstrip(" ,;:-")
                if candidate:
                    text = candidate + "..."
        return text

    if text and text[-1] not in ".!?\"'":
        # Prefer trimming back to the last complete sentence if a full sentence exists
        last_punct = max(text.rfind(". "), text.rfind("! "), text.rfind("? "))
        if last_punct != -1:
            text = text[: last_punct + 1].strip()
        else:
            trimmed = text.rstrip(",;:- ")
            if trimmed and trimmed[-1].isalpha():
                sp = trimmed.rfind(" ")
                if sp > 0:
                    trimmed = trimmed[:sp].rstrip(",;:- ")
            text = (trimmed or text.rstrip(",;:- ")) + "..."
    # 1. Clean nested-paren formulas followed by [type]{label} or {label}
    text = re.sub(r"\((?:[^()\n]|\([^()\n]*\))*\)(?:\s*\[[^\]\n]+\])?\s*\{([^}\n]+)\}", r"\1", text)
    # 2. Clean formula tokens (your level, @actor.*) with optional [type] and {label}
    text = re.sub(r"\b(?:your level|@actor(?:\.[A-Za-z0-9_]+)+)(?:\s*\[[^\]\n]+\])?\s*\{([^}\n]+)\}", r"\1", text)
    # 3. Clean (Skill/Action) followed by key=val tokens and {label}
    text = re.sub(r"(\([A-Za-z][A-Za-z0-9_\s\-]*\))(?:\s+[a-zA-Z0-9_\-]+=[a-zA-Z0-9_\-]+)*\s*\{([^}\n]+)\}", r"\1", text)
    # 4. Clean remaining @actor.* attribute paths and stray braces
    text = re.sub(r"@actor(?:\.system)?\.abilities\.([a-z]{3})\.mod", lambda m: f"your {m.group(1).upper()} modifier", text)
    text = re.sub(r"@actor\.[A-Za-z0-9_.]+", "your level", text)
    text = re.sub(r"\{([^}\n]+)\}", r"\1", text)
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

    # 2b. Normalize chained flat modifiers on character strikes (e.g. '4d4+0+4' -> '4d4+4')
    equip_obj = sheet.get("equipment") if isinstance(sheet.get("equipment"), dict) else {}
    all_strikes = list(sheet.get("strikes") or []) + list(equip_obj.get("strikes") or [])
    for strike in all_strikes:
        if isinstance(strike, dict) and isinstance(strike.get("damage_dice"), str):
            folded = _fold_strike_damage_modifiers(strike["damage_dice"])
            if folded != strike["damage_dice"]:
                strike["damage_dice"] = folded

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
        if "eidolon" in ctype or "eidolon" in stage:
            default_tier = "eidolon"
        elif "familiar" in ctype or "pet" in ctype or "familiar" in stage:
            default_tier = "familiar"
        else:
            default_tier = "mature"
        if "construct" in ctype or "construct" in stage:
            default_tier = "construct"
        elif (
            "animal companion" in str(entity.get("sub_type", "")).lower()
            or "undead" in ctype
            or "specialized" in stage
            or "incredible" in stage
        ):
            default_tier = "companion"
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
    if isinstance(equip, dict):
        if isinstance(equip.get("gear"), list):
            equip["gear"] = [
                clean_template_text(g) if isinstance(g, str) else g
                for g in equip["gear"]
            ]
        if isinstance(equip.get("consumables"), list):
            for c in equip["consumables"]:
                if isinstance(c, dict) and isinstance(c.get("description"), str):
                    c["description"] = clean_template_text(c["description"])

    sheet["validation_warnings"] = warnings
    return sheet
