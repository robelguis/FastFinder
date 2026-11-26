import json
import random
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Tuple

from app.engine.feat_prereqs import check_feat_prerequisites
from app.engine.progression import (
    WEAPON_EXPERT_LEVELS,
    WEAPON_MASTER_LEVELS,
    get_weapon_prof_bonus_delta,
    get_weapon_spec_bonus,
)
from app.engine.strikes import is_ranged_strike

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"

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


# =============================================================================
# Phase 1: Standalone PF2e Remaster Invariant Checker & Fuzz Auditor
# =============================================================================

_RANK_LETTER_TO_BONUS = {"U": 0, "T": 2, "E": 4, "M": 6, "L": 8}
_RANK_BONUS_TO_LETTER = {0: "U", 2: "T", 4: "E", 6: "M", 8: "L"}

_LVL1_CLASS_FEAT_CLASSES = {
    "alchemist", "barbarian", "champion", "commander", "exemplar", "fighter",
    "guardian", "gunslinger", "inventor", "investigator", "kineticist",
    "magus", "monk", "ranger", "rogue", "runesmith", "swashbuckler", "thaumaturge",
}

_STANDARD_SKILLS = {
    "acrobatics", "arcana", "athletics", "crafting", "deception",
    "diplomacy", "intimidation", "medicine", "nature", "occultism",
    "performance", "religion", "society", "stealth", "survival", "thievery",
}

_SKILL_TO_ATTR = {
    "acrobatics": "dex", "arcana": "int", "athletics": "str", "crafting": "int",
    "deception": "cha", "diplomacy": "cha", "intimidation": "cha", "medicine": "wis",
    "nature": "wis", "occultism": "int", "performance": "cha", "religion": "wis",
    "society": "int", "stealth": "dex", "survival": "wis", "thievery": "dex",
}

_NON_SLOT_FEATURE_PREFIXES = (
    "class feature",
    "archetype feature",
    "archetype action",
    "background action",
)

_RE_STRIKE_RUNE_PREFIX = re.compile(r"^(?:\+(\d+)\s+)?(?:(?:Greater|Major)\s+)?(?:Striking\s+)?", re.IGNORECASE)
_RE_SLOT_LEVEL = re.compile(r"\(Level\s+(\d+)", re.IGNORECASE)

_CACHED_FEATS: Optional[Tuple[Dict[str, Dict[str, Any]], Dict[str, Dict[str, Any]]]] = None
_CACHED_WEAPONS: Optional[Dict[str, Dict[str, Any]]] = None


@dataclass
class ValidationIssue:
    """Represents a single PF2e Remaster rule or math invariant violation."""
    category: str  # feat_slots | feat_prereqs | skill_sync | strike_math | synthetic_feats
    code: str
    message: str


@dataclass
class ValidationResult:
    """Aggregated invariant check outcome for one CharacterSheet."""
    passed: bool
    issues: List[ValidationIssue] = field(default_factory=list)
    summary: Dict[str, int] = field(default_factory=dict)


def _load_feat_catalog() -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Dict[str, Any]]]:
    global _CACHED_FEATS
    if _CACHED_FEATS is not None:
        return _CACHED_FEATS
    by_id: Dict[str, Dict[str, Any]] = {}
    by_name: Dict[str, Dict[str, Any]] = {}
    feats_path = DATA_DIR / "feats.json"
    if feats_path.exists():
        raw = json.loads(feats_path.read_text(encoding="utf-8"))
        feats_list = raw if isinstance(raw, list) else raw.get("feats", [])
        for f in feats_list:
            if not isinstance(f, dict):
                continue
            fid = f.get("id")
            fname = (f.get("name") or "").strip().lower()
            if fid:
                by_id[str(fid)] = f
            if fname:
                by_name.setdefault(fname, f)
    _CACHED_FEATS = (by_id, by_name)
    return _CACHED_FEATS


def _load_weapon_catalog() -> Dict[str, Dict[str, Any]]:
    global _CACHED_WEAPONS
    if _CACHED_WEAPONS is not None:
        return _CACHED_WEAPONS
    lookup: Dict[str, Dict[str, Any]] = {}
    eq_path = DATA_DIR / "equipment.json"
    if eq_path.exists():
        raw = json.loads(eq_path.read_text(encoding="utf-8"))
        if isinstance(raw, list):
            for item in raw:
                if not isinstance(item, dict):
                    continue
                itype = str(item.get("type") or "").lower()
                cat = str(item.get("category") or "").lower()
                if itype == "weapon" or cat in ("simple", "martial", "advanced", "unarmed"):
                    nm = str(item.get("name") or "").strip().lower()
                    if nm and nm not in lookup:
                        lookup[nm] = item
    _CACHED_WEAPONS = lookup
    return _CACHED_WEAPONS


def _as_dict(obj: Any) -> Dict[str, Any]:
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if hasattr(obj, "dict"):
        return obj.dict()
    return dict(obj)


def _lookup_catalog_feat(
    feat_dict: Dict[str, Any],
    by_id: Dict[str, Dict[str, Any]],
    by_name: Dict[str, Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    fid = str(feat_dict.get("id") or "")
    fname = str(feat_dict.get("name") or "").strip().lower()
    base_name = fname.split("(", 1)[0].strip()
    if fid and fid in by_id:
        return by_id[fid]
    if fname and fname in by_name:
        return by_name[fname]
    if base_name and base_name in by_name:
        return by_name[base_name]
    return None


def _classify_feat_slot(feat_dict: Dict[str, Any], catalog_feat: Optional[Dict[str, Any]]) -> str:
    cat = str(feat_dict.get("category") or "").strip().lower()
    if any(cat.startswith(pref) for pref in _NON_SLOT_FEATURE_PREFIXES):
        return "feature"
    if "background" in cat:
        return "background"
    if "ancestry" in cat:
        return "ancestry"
    if "skill" in cat:
        return "skill"
    if "general" in cat:
        return "general"
    if "class" in cat or "archetype" in cat:
        return "class_or_archetype"
    if catalog_feat:
        ccat = str(catalog_feat.get("category") or "").lower()
        if ccat in ("ancestry", "skill", "general"):
            return ccat
        if ccat == "class":
            return "class_or_archetype"
    return "other"


def _is_dedication_entry(feat_dict: Dict[str, Any]) -> bool:
    name = str(feat_dict.get("name") or "").strip().lower()
    traits = [str(t).strip().lower() for t in (feat_dict.get("traits") or [])]
    return "dedication" in name or "dedication" in traits


def _archetype_key_from_name(feat_name: str) -> str:
    low = (feat_name or "").strip().lower()
    if "dedication" in low:
        low = low.split("dedication", 1)[0].strip()
    return " ".join(low.split())


def _feat_belongs_to_archetype(feat_dict: Dict[str, Any], arch_key: str) -> bool:
    if not arch_key or _is_dedication_entry(feat_dict):
        return False
    name = str(feat_dict.get("name") or "").strip().lower()
    cat = str(feat_dict.get("category") or "").strip().lower()
    traits = [str(t).strip().lower() for t in (feat_dict.get("traits") or [])]
    if "archetype" not in cat and "archetype" not in traits:
        return False
    return arch_key in name or arch_key in cat or any(arch_key in t for t in traits)


def _check_feat_slots(
    data: Dict[str, Any],
    by_id: Dict[str, Dict[str, Any]],
    by_name: Dict[str, Dict[str, Any]],
) -> List[ValidationIssue]:
    issues: List[ValidationIssue] = []
    level = int(data.get("level") or 1)
    cls_lower = str(data.get("character_class") or "").strip().lower()
    heritage_lower = str(data.get("heritage") or "").strip().lower()
    feats = [_as_dict(f) for f in (data.get("feats") or [])]

    counts = {"ancestry": 0, "class_or_archetype": 0, "skill": 0, "general": 0, "background": 0}
    bonus_feats = []
    feat_names_lower = {str(f.get("name") or "").strip().lower() for f in feats}

    for f in feats:
        cat_raw = str(f.get("category") or "").strip().lower()
        if "(bonus)" in cat_raw or "/bonus)" in cat_raw:
            bonus_feats.append(f)
            continue
        catalog_feat = _lookup_catalog_feat(f, by_id, by_name)
        bucket = _classify_feat_slot(f, catalog_feat)
        if bucket in counts:
            counts[bucket] += 1

    if bonus_feats:
        names = ", ".join(str(b.get("name")) for b in bonus_feats)
        issues.append(ValidationIssue(
            "feat_slots",
            "bonus_prereq_feat_injected",
            f"Injected {len(bonus_feats)} free bonus feat(s) outside legal slots: {names}",
        ))

    has_ancestral_paragon = any(fn == "ancestral paragon" for fn in feat_names_lower)
    expected_anc = 1 + sum(1 for m in (5, 9, 13, 17) if level >= m) + (1 if has_ancestral_paragon else 0)
    if counts["ancestry"] != expected_anc:
        issues.append(ValidationIssue(
            "feat_slots",
            "ancestry_slot_mismatch",
            f"Level {level} expected {expected_anc} ancestry feat(s), found {counts['ancestry']}",
        ))

    # Background grants 1 feat (unless background only grants a custom Background Action)
    has_bg_action = any(
        str(f.get("category") or "").strip().lower().startswith("background action")
        for f in feats
    )
    if counts["background"] == 0 and not has_bg_action:
        issues.append(ValidationIssue(
            "feat_slots",
            "missing_background_feat",
            "Missing Level 1 background feat",
        ))
    elif counts["background"] > 1:
        issues.append(ValidationIssue(
            "feat_slots",
            "extra_background_feat",
            f"Expected at most 1 background feat, found {counts['background']}",
        ))

    has_natural_ambition = any("natural ambition" in fn for fn in feat_names_lower)
    expected_l1_class = (1 if cls_lower in _LVL1_CLASS_FEAT_CLASSES else 0) + (1 if has_natural_ambition else 0)
    ancient_elf_bonus = 1 if "ancient elf" in heritage_lower else 0
    expected_class = expected_l1_class + (level // 2) + ancient_elf_bonus
    if counts["class_or_archetype"] != expected_class:
        code = "extra_class_feat" if counts["class_or_archetype"] > expected_class else "missing_class_feat"
        issues.append(ValidationIssue(
            "feat_slots",
            code,
            f"Level {level} {data.get('character_class')} expected {expected_class} class/archetype feat(s), found {counts['class_or_archetype']}",
        ))

    expected_skill = max(0, level - 1) if cls_lower in ("rogue", "investigator") else (level // 2)
    if counts["skill"] != expected_skill:
        code = "extra_skill_feat" if counts["skill"] > expected_skill else "missing_skill_feat"
        issues.append(ValidationIssue(
            "feat_slots",
            code,
            f"Level {level} {data.get('character_class')} expected {expected_skill} skill feat(s), found {counts['skill']}",
        ))

    versatile_bonus = 1 if "versatile human" in heritage_lower else 0
    expected_general = sum(1 for m in (3, 7, 11, 15, 19) if level >= m) + versatile_bonus
    if counts["general"] != expected_general:
        code = "extra_general_feat" if counts["general"] > expected_general else "missing_general_feat"
        issues.append(ValidationIssue(
            "feat_slots",
            code,
            f"Level {level} expected {expected_general} general feat(s), found {counts['general']}",
        ))

    return issues


def _extract_attr_mods(data: Dict[str, Any]) -> Dict[str, int]:
    raw_attrs = data.get("attributes") or {}
    out: Dict[str, int] = {}
    for full_k, short_k in ATTR_PAIRS:
        if full_k in raw_attrs and raw_attrs[full_k] is not None:
            out[short_k] = int(raw_attrs[full_k])
        elif short_k in raw_attrs and raw_attrs[short_k] is not None:
            out[short_k] = int(raw_attrs[short_k])
        else:
            out[short_k] = 0
    return out


def _check_feat_prerequisites_and_dedications(
    data: Dict[str, Any],
    by_id: Dict[str, Dict[str, Any]],
    by_name: Dict[str, Dict[str, Any]],
) -> List[ValidationIssue]:
    issues: List[ValidationIssue] = []
    level = int(data.get("level") or 1)
    feats = [_as_dict(f) for f in (data.get("feats") or [])]

    sub_obj = data.get("subclass")
    sub_label = sub_obj.get("name", "") if isinstance(sub_obj, dict) else str(sub_obj or "")
    arch_obj = data.get("archetype")
    arch_label = arch_obj.get("name", "") if isinstance(arch_obj, dict) else str(arch_obj or "")

    attr_mods = _extract_attr_mods(data)
    skill_ranks = {
        str(sk.get("name") or "").title(): int(sk.get("rank") or 0)
        for sk in (data.get("all_skills") or [])
        if isinstance(sk, dict) and sk.get("name")
    }
    perc_obj = data.get("perception") or {}
    perc_rank = int(perc_obj.get("rank") or 2) if isinstance(perc_obj, dict) else 2

    all_feat_names = [str(f.get("name") or "").strip() for f in feats if f.get("name")]
    seen_names: Set[str] = set()
    active_dedications: List[Tuple[str, int]] = []  # (arch_key, index_in_feats)

    for idx, f in enumerate(feats):
        fname = str(f.get("name") or "").strip()
        fn_low = fname.lower()
        cat_raw = str(f.get("category") or "").strip()
        cat_low = cat_raw.lower()

        if any(cat_low.startswith(pref) for pref in _NON_SLOT_FEATURE_PREFIXES):
            continue

        # Unresolved subchoices / placeholders
        if fn_low == "additional lore" or "chosen lore" in fn_low or "tbd" in fn_low or "undefined" in fn_low:
            issues.append(ValidationIssue(
                "feat_prereqs",
                "unresolved_feat_subchoice",
                f"Feat '{fname}' has an unresolved subchoice or placeholder",
            ))

        # Duplicate non-repeatable feat
        if fn_low in seen_names:
            issues.append(ValidationIssue(
                "feat_prereqs",
                "duplicate_feat",
                f"Duplicate feat '{fname}'",
            ))
        seen_names.add(fn_low)

        # Dedication two-feat rule check (sequential order)
        if _is_dedication_entry(f):
            arch_key = _archetype_key_from_name(fname)
            if active_dedications:
                prev_key, prev_idx = active_dedications[-1]
                if prev_key == arch_key:
                    issues.append(ValidationIssue(
                        "feat_prereqs",
                        "duplicate_dedication",
                        f"Duplicate dedication '{fname}'",
                    ))
                else:
                    qualifying = [
                        prev_f for prev_f in feats[prev_idx + 1:idx]
                        if _feat_belongs_to_archetype(prev_f, prev_key)
                    ]
                    if len(qualifying) < 2:
                        issues.append(ValidationIssue(
                            "feat_prereqs",
                            "dedication_two_feat_violation",
                            f"'{fname}' taken after '{prev_key}' dedication with only {len(qualifying)}/2 archetype feats",
                        ))
            active_dedications.append((arch_key, idx))

        # Catalog prerequisite & level checks
        catalog_feat = _lookup_catalog_feat(f, by_id, by_name)
        if not catalog_feat:
            continue

        feat_lvl = int(catalog_feat.get("level") or 1)
        heritage_lower = str(data.get("heritage") or "").strip().lower()
        is_ancient_elf_ded = (
            "ancient elf" in heritage_lower
            and "dedication" in fn_low
            and "multiclass" in [str(t).lower() for t in (f.get("traits") or catalog_feat.get("traits") or [])]
            and feat_lvl == 2
        )
        if feat_lvl > level and not is_ancient_elf_ded:
            issues.append(ValidationIssue(
                "feat_prereqs",
                "feat_above_character_level",
                f"Feat '{fname}' (level {feat_lvl}) exceeds character level {level}",
            ))

        slot_m = _RE_SLOT_LEVEL.search(cat_raw)
        if slot_m:
            slot_lvl = int(slot_m.group(1))
            if feat_lvl > slot_lvl:
                issues.append(ValidationIssue(
                    "feat_prereqs",
                    "feat_above_slot_level",
                    f"Feat '{fname}' (level {feat_lvl}) placed in lower-level slot '{cat_raw}'",
                ))

        other_owned = {o for o in all_feat_names if o.lower() != fn_low}
        langs_set = {str(l).strip() for l in (data.get("languages") or []) if l}
        if not check_feat_prerequisites(
            catalog_feat,
            skill_ranks=skill_ranks,
            owned_feat_names=other_owned,
            attribute_mods=attr_mods,
            character_level=level,
            subclass_name=sub_label,
            archetype_name=arch_label,
            perception_rank=perc_rank,
            languages=langs_set,
        ):
            issues.append(ValidationIssue(
                "feat_prereqs",
                "unmet_feat_prerequisites",
                f"Feat '{fname}' ({cat_raw}) failed prerequisites {catalog_feat.get('prerequisites')}",
            ))

    return issues


def _check_skills_and_lores(data: Dict[str, Any]) -> List[ValidationIssue]:
    issues: List[ValidationIssue] = []
    level = int(data.get("level") or 1)
    cls_lower = str(data.get("character_class") or "").strip().lower()
    attrs = _extract_attr_mods(data)
    feats = [_as_dict(f) for f in (data.get("feats") or [])]
    skills = [_as_dict(s) for s in (data.get("all_skills") or [])]

    has_untrained_improv = any(
        "untrained improvisation" in str(f.get("name") or "").lower()
        for f in feats
    )

    skill_by_low: Dict[str, Dict[str, Any]] = {}
    legendary_count = 0
    bad_skill_tokens = ("chosen lore", "tbd", "ternary(", "gte(", "undefined", "at least one skill", "a skill with", "recall knowledge")

    for sk in skills:
        sname = str(sk.get("name") or "").strip()
        slow = sname.lower()
        if not sname or any(tok in slow for tok in bad_skill_tokens):
            issues.append(ValidationIssue(
                "skill_sync",
                "placeholder_skill",
                f"Invalid/placeholder skill entry '{sname}'",
            ))
            continue
        skill_by_low[slow] = sk

        rank_val = int(sk.get("rank") or 0)
        rank_letter = str(sk.get("rank_letter") or "U").upper()
        expected_letter = _RANK_BONUS_TO_LETTER.get(rank_val)
        if expected_letter is None or expected_letter != rank_letter:
            issues.append(ValidationIssue(
                "skill_sync",
                "skill_rank_letter_mismatch",
                f"Skill '{sname}' has rank={rank_val} vs rank_letter='{rank_letter}'",
            ))

        stat_key = str(sk.get("attribute") or _SKILL_TO_ATTR.get(slow, "int")).lower()[:3]
        attr_mod = attrs.get(stat_key, 0)
        item_bonus = int(sk.get("item_bonus") or 0)
        expected_mod = recompute_proficiency_bonus(level, rank_letter, attr_mod, item_bonus, has_untrained_improv)
        actual_mod = sk.get("modifier")
        if actual_mod != expected_mod:
            issues.append(ValidationIssue(
                "skill_sync",
                "skill_modifier_mismatch",
                f"Skill '{sname}' ({rank_letter}) modifier is {actual_mod}, expected {expected_mod}",
            ))

        if rank_val >= 4 and level < 2:
            issues.append(ValidationIssue("skill_sync", "illegal_expert_below_lvl2", f"Skill '{sname}' is Expert at level {level} (< 2)"))
        if rank_val >= 6 and level < 7:
            issues.append(ValidationIssue("skill_sync", "illegal_master_below_lvl7", f"Skill '{sname}' is Master at level {level} (< 7)"))
        if rank_val >= 8 and level < 15:
            issues.append(ValidationIssue("skill_sync", "illegal_legendary_below_lvl15", f"Skill '{sname}' is Legendary at level {level} (< 15)"))
        if rank_val >= 8:
            legendary_count += 1

    if legendary_count > 4:
        issues.append(ValidationIssue(
            "skill_sync",
            "too_many_legendary_skills",
            f"Character has {legendary_count} Legendary skills (standard cap is 4)",
        ))

    # Additional Lore auto-scaling: T (1-2), E (3-6), M (7-14), L (15+)
    expected_al_rank = 8 if level >= 15 else (6 if level >= 7 else (4 if level >= 3 else 2))
    for f in feats:
        fname = str(f.get("name") or "").strip()
        fn_low = fname.lower()
        fdesc = str(f.get("description") or "")

        if "additional lore" in fn_low and "(" in fname and ")" in fname:
            lore_topic = fname.split("(", 1)[1].rsplit(")", 1)[0].strip()
            lore_name = lore_topic if lore_topic.lower().endswith("lore") else f"{lore_topic} Lore"
            sk = skill_by_low.get(lore_name.lower())
            if not sk:
                issues.append(ValidationIssue(
                    "skill_sync",
                    "missing_additional_lore",
                    f"Feat '{fname}' present, but '{lore_name}' missing from skills",
                ))
            elif int(sk.get("rank") or 0) < expected_al_rank:
                issues.append(ValidationIssue(
                    "skill_sync",
                    "unscaled_additional_lore",
                    f"'{lore_name}' rank is {sk.get('rank')} at level {level}, expected >= {expected_al_rank}",
                ))

        # Known feat/dedication skill & lore grants
        if "living monolith dedication" in fn_low:
            sk = skill_by_low.get("ancient osirion lore")
            if not sk or int(sk.get("rank") or 0) < 2:
                issues.append(ValidationIssue("skill_sync", "missing_feat_granted_lore", "Living Monolith Dedication missing trained Ancient Osirion Lore"))
        if "hobnobber" in fn_low:
            sk = skill_by_low.get("diplomacy")
            if not sk or int(sk.get("rank") or 0) < 2:
                issues.append(ValidationIssue("skill_sync", "missing_feat_granted_skill", "Hobnobber requires/grants trained Diplomacy"))
        if "natural medicine" in fn_low:
            sk = skill_by_low.get("nature")
            if not sk or int(sk.get("rank") or 0) < 2:
                issues.append(ValidationIssue("skill_sync", "missing_feat_granted_skill", "Natural Medicine requires trained Nature"))
        if "yaoguai historian" in fn_low:
            for req_sk in ("occultism", "yaoguai lore"):
                sk = skill_by_low.get(req_sk)
                if not sk or int(sk.get("rank") or 0) < 2:
                    issues.append(ValidationIssue("skill_sync", "missing_feat_granted_skill", f"Yaoguai Historian missing trained {req_sk.title()}"))

        # Generic "you become trained in <standard skill>" check
        for m in re.finditer(r"you become trained in\s+([a-z]+)(?:\s+and\s+([a-z]+))?", fdesc, re.IGNORECASE):
            for grp in (m.group(1), m.group(2)):
                if not grp:
                    continue
                g_low = grp.strip().lower()
                if g_low in _STANDARD_SKILLS:
                    sk = skill_by_low.get(g_low)
                    if not sk or int(sk.get("rank") or 0) < 2:
                        issues.append(ValidationIssue(
                            "skill_sync",
                            "missing_feat_granted_skill",
                            f"Feat '{fname}' grants trained {g_low.title()}, but skill rank is {sk.get('rank') if sk else 0}",
                        ))

    # Thaumaturge Esoteric Lore scaling
    if cls_lower == "thaumaturge":
        es = skill_by_low.get("esoteric lore")
        exp_es = 8 if level >= 15 else (6 if level >= 7 else (4 if level >= 3 else 2))
        if not es or int(es.get("rank") or 0) < exp_es:
            issues.append(ValidationIssue(
                "skill_sync",
                "missing_or_unscaled_esoteric_lore",
                f"Level {level} Thaumaturge Esoteric Lore rank is {es.get('rank') if es else 0}, expected >= {exp_es}",
            ))

    return issues


def _parse_int_str(val: Any) -> Optional[int]:
    if val is None:
        return None
    try:
        return int(str(val).replace("+", "").strip())
    except (ValueError, TypeError):
        return None


def _check_strike_math(
    data: Dict[str, Any],
    weapon_catalog: Dict[str, Dict[str, Any]],
) -> List[ValidationIssue]:
    issues: List[ValidationIssue] = []
    level = int(data.get("level") or 1)
    cls_lower = str(data.get("character_class") or "").strip().lower()
    attrs = _extract_attr_mods(data)
    equip = data.get("equipment") if isinstance(data.get("equipment"), dict) else {}
    strikes = [_as_dict(s) for s in (equip.get("strikes") or [])]

    seen_base_names: Set[str] = set()
    weapon_prof = 2 + get_weapon_prof_bonus_delta(cls_lower, level)
    expected_potency = 3 if level >= 16 else (2 if level >= 10 else (1 if level >= 2 else 0))
    expected_dice_count = 4 if level >= 19 else (3 if level >= 12 else (2 if level >= 4 else 1))
    expected_spec = get_weapon_spec_bonus(cls_lower, level)

    for st in strikes:
        raw_name = str(st.get("name") or "").strip()
        if not raw_name:
            continue
        name_low = raw_name.lower()
        clean_base = _RE_STRIKE_RUNE_PREFIX.sub("", raw_name).strip().lower()

        # Check singular/plural Horn vs Horns or exact duplicate strikes
        if clean_base in seen_base_names or (clean_base == "horn" and "horns" in seen_base_names) or (clean_base == "horns" and "horn" in seen_base_names):
            issues.append(ValidationIssue(
                "strike_math",
                "duplicate_strike",
                f"Duplicate strike entry '{raw_name}'",
            ))
        seen_base_names.add(clean_base)

        atk_val = _parse_int_str(st.get("attack_bonus"))
        map2_val = _parse_int_str(st.get("map_second"))
        map3_val = _parse_int_str(st.get("map_third"))
        traits_low = [str(t).lower() for t in (st.get("traits") or [])]
        is_agile = "agile" in traits_low

        if atk_val is not None and map2_val is not None and map3_val is not None:
            step = 4 if is_agile else 5
            if map2_val != atk_val - step or map3_val != atk_val - (2 * step):
                issues.append(ValidationIssue(
                    "strike_math",
                    "strike_map_mismatch",
                    f"Strike '{raw_name}' MAP ({atk_val}/{map2_val}/{map3_val}) inconsistent with agile={is_agile}",
                ))

        # 1. Kineticist Elemental Blast
        if name_low.startswith("elemental blast"):
            imp_prof = 8 if level >= 19 else (6 if level >= 15 else (4 if level >= 7 else 2))
            gate_att = 3 if level >= 17 else (2 if level >= 11 else (1 if level >= 3 else 0))
            expected_blast_atk = level + imp_prof + attrs["con"] + gate_att
            if atk_val != expected_blast_atk:
                issues.append(ValidationIssue(
                    "strike_math",
                    "kineticist_blast_attack_mismatch",
                    f"'{raw_name}' attack +{atk_val} != expected +{expected_blast_atk} (L{level}+prof{imp_prof}+CON{attrs['con']}+item{gate_att})",
                ))
            expected_blast_dice = 1 + (level - 1) // 4
            dmg_str = str(st.get("damage_dice") or "")
            m_dice = re.match(r"^(\d+)d\d+", dmg_str.strip())
            if m_dice and int(m_dice.group(1)) != expected_blast_dice:
                issues.append(ValidationIssue(
                    "strike_math",
                    "kineticist_blast_dice_mismatch",
                    f"'{raw_name}' dice '{dmg_str}' expected {expected_blast_dice}d at level {level}",
                ))
            continue

        # 2. Alchemical Bombs
        if any(b in name_low for b in ("alchemist's fire", "bottled lightning", "acid flask", "frost vial")):
            bomb_item = 3 if "(major)" in name_low else (2 if "(greater)" in name_low else (1 if "(moderate)" in name_low else 0))
            expected_bomb_atk = level + weapon_prof + attrs["dex"] + bomb_item
            if atk_val != expected_bomb_atk:
                issues.append(ValidationIssue(
                    "strike_math",
                    "bomb_attack_mismatch",
                    f"'{raw_name}' attack +{atk_val} != expected +{expected_bomb_atk} (L{level}+prof{weapon_prof}+DEX{attrs['dex']}+item{bomb_item})",
                ))
            continue

        # 3. Weapons & Unarmed strikes
        w_info = weapon_catalog.get(clean_base) or {}
        w_traits = [str(t).lower() for t in (w_info.get("traits") or [])] + traits_low
        is_finesse = "finesse" in w_traits
        is_ranged = is_ranged_strike(clean_base, w_traits, weapon_entry=w_info)
        stat_mod = attrs["dex"] if is_ranged else (max(attrs["str"], attrs["dex"]) if is_finesse else attrs["str"])

        m_pot = re.match(r"^\+(\d+)\s+", raw_name)
        name_potency = int(m_pot.group(1)) if m_pot else 0

        # Check attack bonus against actual weapon potency vs expected level potency
        expected_atk_with_name_pot = level + weapon_prof + stat_mod + name_potency
        expected_atk_with_lvl_pot = level + weapon_prof + stat_mod + expected_potency
        if atk_val is not None and atk_val != expected_atk_with_lvl_pot:
            if atk_val == expected_atk_with_name_pot and name_potency != expected_potency:
                issues.append(ValidationIssue(
                    "strike_math",
                    "missing_or_wrong_potency_rune",
                    f"Strike '{raw_name}' has +{name_potency} potency at level {level} (expected +{expected_potency})",
                ))
            else:
                issues.append(ValidationIssue(
                    "strike_math",
                    "strike_attack_mismatch",
                    f"Strike '{raw_name}' attack +{atk_val} != expected +{expected_atk_with_lvl_pot} (L{level}+prof{weapon_prof}+stat{stat_mod}+pot{expected_potency})",
                ))

        # Check damage dice count & Weapon Specialization flat bonus
        dmg_str = str(st.get("damage_dice") or "").strip()
        m_dmg = re.match(r"^(\d+)d(\d+)\s*([+-]\s*\d+)?", dmg_str)
        if m_dmg:
            dice_num = int(m_dmg.group(1))
            if dice_num != expected_dice_count and "rage strike" not in name_low:
                issues.append(ValidationIssue(
                    "strike_math",
                    "strike_striking_dice_mismatch",
                    f"Strike '{raw_name}' damage '{dmg_str}' has {dice_num} dice at level {level} (expected {expected_dice_count})",
                ))
            flat_mod = int(m_dmg.group(3).replace(" ", "")) if m_dmg.group(3) else 0
            is_thrown = any(t.startswith("thrown") for t in w_traits)
            is_propulsive = any(t.startswith("propulsive") for t in w_traits)
            if is_ranged and not is_thrown:
                exp_stat_dmg = (attrs["str"] // 2 if attrs["str"] >= 0 else attrs["str"]) if is_propulsive else 0
            else:
                exp_stat_dmg = attrs["str"]
            expected_flat = exp_stat_dmg + expected_spec
            if flat_mod != expected_flat and "rage strike" not in name_low:
                issues.append(ValidationIssue(
                    "strike_math",
                    "strike_damage_mod_mismatch",
                    f"Strike '{raw_name}' damage '{dmg_str}' flat mod {flat_mod:+d} != expected {expected_flat:+d} (stat{exp_stat_dmg:+d}+spec{expected_spec:+d})",
                ))

    return issues


def _check_synthetic_feats(
    data: Dict[str, Any],
    by_id: Dict[str, Dict[str, Any]],
    by_name: Dict[str, Dict[str, Any]],
) -> List[ValidationIssue]:
    issues: List[ValidationIssue] = []
    feats = [_as_dict(f) for f in (data.get("feats") or [])]

    for f in feats:
        fid = str(f.get("id") or "")
        fname = str(f.get("name") or "").strip()
        cat_low = str(f.get("category") or "").strip().lower()

        if any(cat_low.startswith(pref) for pref in _NON_SLOT_FEATURE_PREFIXES):
            continue

        if fid.startswith(("anc-feat-", "req-feat-")):
            issues.append(ValidationIssue(
                "synthetic_feats",
                "synthetic_placeholder_feat",
                f"Synthetic placeholder feat '{fname}' (id='{fid}', category='{f.get('category')}')",
            ))
            continue

        if not _lookup_catalog_feat(f, by_id, by_name):
            issues.append(ValidationIssue(
                "synthetic_feats",
                "non_catalog_feat",
                f"Feat '{fname}' (id='{fid}', category='{f.get('category')}') not found in feats.json",
            ))

    return issues


def audit_character_sheet(sheet: Any) -> ValidationResult:
    """
    Standalone PF2e Remaster Invariant Checker.
    Validates feat slots, feat/dedication prerequisites, skill/lore sync,
    strike/blast math, and absence of synthetic placeholder feats.
    """
    data = _as_dict(sheet)
    by_id, by_name = _load_feat_catalog()
    weapon_catalog = _load_weapon_catalog()

    issues: List[ValidationIssue] = []
    issues.extend(_check_feat_slots(data, by_id, by_name))
    issues.extend(_check_feat_prerequisites_and_dedications(data, by_id, by_name))
    issues.extend(_check_skills_and_lores(data))
    issues.extend(_check_strike_math(data, weapon_catalog))
    issues.extend(_check_synthetic_feats(data, by_id, by_name))

    summary: Dict[str, int] = {
        "feat_slots": 0,
        "feat_prereqs": 0,
        "skill_sync": 0,
        "strike_math": 0,
        "synthetic_feats": 0,
    }
    for iss in issues:
        summary[iss.category] = summary.get(iss.category, 0) + 1

    return ValidationResult(passed=(len(issues) == 0), issues=issues, summary=summary)


def run_fuzz_audit(
    num_builds: int = 50,
    min_level: int = 1,
    max_level: int = 15,
    seed: int = 2026,
) -> Dict[str, Any]:
    """Generates randomized builds across classes/levels and scores them with audit_character_sheet."""
    from app.engine.generator import PF2eGenerator
    from app.engine.subclasses import CLASS_SUBCLASSES

    rng = random.Random(seed)
    gen = PF2eGenerator()
    all_classes = sorted(CLASS_SUBCLASSES.keys())
    ancestries = [
        "Human", "Dwarf", "Elf", "Gnome", "Goblin", "Halfling",
        "Leshy", "Orc", "Yaoguai", "Tengu", "Kitsune", "Catfolk",
        "Centaur", "Minotaur", "Lizardfolk", "Automaton",
    ]
    archetypes = [
        "", "Beastmaster", "Bastion", "Sentinel", "Wizard",
        "Medic", "Cavalier", "Blessed One", "Rogue", "Archer",
        "Living Monolith", "Marshal",
    ]

    passed_builds = 0
    failed_builds = 0
    crashes: List[Dict[str, Any]] = []
    category_build_failures: Dict[str, int] = {
        "feat_slots": 0,
        "feat_prereqs": 0,
        "skill_sync": 0,
        "strike_math": 0,
        "synthetic_feats": 0,
    }
    category_issue_totals: Dict[str, int] = dict(category_build_failures)
    code_counts: Dict[str, int] = {}
    code_examples: Dict[str, List[str]] = {}

    for i in range(1, num_builds + 1):
        cls_key = all_classes[(i - 1) % len(all_classes)]
        cls_title = cls_key.replace("_", " ").title()
        options = CLASS_SUBCLASSES[cls_key].get("options") or []
        sub_opt = rng.choice(options)["name"] if options else ""
        ancestry = rng.choice(ancestries)
        level = rng.randint(min_level, max_level)
        arch = rng.choice(archetypes) if level >= 2 and rng.random() < 0.45 else ""
        label = f"#{i} L{level} {ancestry} {cls_title} ({sub_opt})" + (f" [{arch}]" if arch else "")

        try:
            sheet = gen.generate(
                ancestry_name=ancestry,
                class_name=cls_title,
                subclass_name=sub_opt,
                archetype_name=arch,
                use_dedication=bool(arch),
                level=level,
            )
        except Exception as exc:
            failed_builds += 1
            crashes.append({"build": label, "error": f"{type(exc).__name__}: {exc}"})
            continue

        result = audit_character_sheet(sheet)
        if result.passed:
            passed_builds += 1
            continue

        failed_builds += 1
        seen_cats: Set[str] = set()
        for iss in result.issues:
            category_issue_totals[iss.category] = category_issue_totals.get(iss.category, 0) + 1
            if iss.category not in seen_cats:
                category_build_failures[iss.category] = category_build_failures.get(iss.category, 0) + 1
                seen_cats.add(iss.category)
            code_counts[iss.code] = code_counts.get(iss.code, 0) + 1
            ex_list = code_examples.setdefault(iss.code, [])
            if len(ex_list) < 3:
                ex_list.append(f"{label}: {iss.message}")

    return {
        "total_builds": num_builds,
        "min_level": min_level,
        "max_level": max_level,
        "passed_builds": passed_builds,
        "failed_builds": failed_builds,
        "crashes": crashes,
        "category_build_failures": category_build_failures,
        "category_issue_totals": category_issue_totals,
        "code_counts": dict(sorted(code_counts.items(), key=lambda kv: -kv[1])),
        "code_examples": code_examples,
    }


def format_fuzz_report(report: Dict[str, Any]) -> str:
    """Formats a run_fuzz_audit() scorecard into a human-readable summary."""
    lines = [
        f"PF2e Remaster Fuzz Audit ({report['total_builds']} builds, Levels {report['min_level']}-{report['max_level']})",
        f"Passed: {report['passed_builds']}/{report['total_builds']} | Failed: {report['failed_builds']}/{report['total_builds']} | Crashes: {len(report['crashes'])}",
        "",
        "Failures by Category (builds affected / total issues):",
    ]
    for cat, bcount in sorted(report["category_build_failures"].items(), key=lambda kv: -kv[1]):
        icount = report["category_issue_totals"].get(cat, 0)
        lines.append(f"  - {cat}: {bcount} builds ({icount} issues)")
    lines.append("")
    lines.append("Top Violation Codes:")
    for code, cnt in list(report["code_counts"].items())[:12]:
        lines.append(f"  - {code}: {cnt}")
        for ex in report["code_examples"].get(code, [])[:2]:
            lines.append(f"      e.g. {ex}")
    if report["crashes"]:
        lines.append("")
        lines.append("Crashes:")
        for c in report["crashes"][:5]:
            lines.append(f"  - {c['build']}: {c['error']}")
    return "\n".join(lines)


if __name__ == "__main__":
    print(format_fuzz_report(run_fuzz_audit(num_builds=50, min_level=1, max_level=15)))
