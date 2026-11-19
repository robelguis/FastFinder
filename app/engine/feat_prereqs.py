
FEAT_FAMILIES = {
    "monk": [
        {"dragon stance", "dragon roar"},
        {"crane stance", "crane flutter", "crane wing"},
        {"tiger stance", "tiger slash"},
        {"wolf stance", "wolf drag"},
        {"mountain stance", "mountain stronghold", "mountain quake"},
        {"gorilla stance", "gorilla pound"},
        {"stumbling stance", "stumbling feint"},
        {"ironblood stance", "ironblood surge"},
        {"rain of embers stance", "blazing streak"},
        {"clinging shadows stance", "shadow's web"},
        {"monastic weaponry", "shooting stars", "peafowl stance", "pinning fire"},
        {"ki strike", "ki rush", "wholeness of body", "abundant step", "wind jumper", "ki blast"}
    ],
    "barbarian": [
        {"animal rage", "predator's pounce", "animal skin"},
        {"dragon rage", "dragon breath", "wings of the dragon"},
        {"giant's stature", "titan's stature", "giant stature"},
        {"spirit's wrath", "spirit guide", "spirit's fury"},
        {"raging intimidation", "scare to death", "terrifying howl"}
    ],
    "fighter": [
        {"double slice", "twin parry", "dual-weapon blitz", "flurry of blows"},
        {"power attack", "furious focus", "brutal finish"},
        {"point-blank shot", "double shot", "triple shot", "debilitating shot"},
        {"snagging strike", "combat grab", "dazing blow"}
    ],
    "swashbuckler": [
        {"confident finisher", "bleeding finisher", "unbalancing finisher", "finishing follow-through"},
        {"tumble behind", "acrobatic performer", "swaggering initiative"}
    ],
    "rogue": [
        {"sneak attack", "gang up", "nimble dodge", "sidestep", "twist the knife"},
        {"trap finder", "delay trap", "dismantle"}
    ]
}

import re
from typing import Dict, List, Set, Any, Optional

# Rank mappings
RANK_MAP = {
    "trained": 2,
    "expert": 4,
    "master": 6,
    "legendary": 8
}

# Thematic priority skills per class (for weighting skill selections and skill feats)
CLASS_PRIORITY_SKILLS: Dict[str, List[str]] = {
    "fighter": ["Athletics", "Acrobatics", "Intimidation"],
    "barbarian": ["Athletics", "Intimidation", "Survival"],
    "champion": ["Athletics", "Religion", "Diplomacy"],
    "monk": ["Athletics", "Acrobatics", "Stealth", "Religion"],
    "ranger": ["Nature", "Survival", "Stealth", "Athletics"],
    "rogue": ["Stealth", "Thievery", "Acrobatics", "Deception", "Diplomacy"],
    "swashbuckler": ["Acrobatics", "Diplomacy", "Deception", "Intimidation", "Athletics"],
    "investigator": ["Society", "Medicine", "Stealth", "Perception"],
    "cleric": ["Religion", "Medicine", "Diplomacy"],
    "druid": ["Nature", "Survival", "Medicine"],
    "bard": ["Performance", "Occultism", "Deception", "Diplomacy"],
    "wizard": ["Arcana", "Society", "Crafting"],
    "witch": ["Arcana", "Occultism", "Nature", "Religion"],
    "sorcerer": ["Deception", "Diplomacy", "Intimidation"],
    "oracle": ["Religion", "Diplomacy", "Occultism"],
    "psychic": ["Occultism", "Deception", "Diplomacy"],
    "thaumaturge": ["Arcana", "Occultism", "Religion", "Nature", "Esoteric Lore"],
    "kineticist": ["Nature", "Athletics", "Acrobatics"],
    "alchemist": ["Crafting", "Medicine", "Nature"],
    "gunslinger": ["Acrobatics", "Crafting", "Intimidation"]
}


KINETICIST_ELEMENTS = {"air", "earth", "fire", "metal", "water", "wood"}

def extract_gate_elements(subclass_name: str) -> set:
    """Extract set of active elements from a Kineticist Kinetic Gate subclass name."""
    if not subclass_name:
        return set()
    name_lower = subclass_name.lower()
    return {elem for elem in KINETICIST_ELEMENTS if elem in name_lower}

def is_kineticist_feat_allowed(feat: Dict[str, Any], gate_elements: set) -> bool:
    """Check if a Kineticist impulse or class feat is compatible with active gate elements."""
    traits = {t.lower() for t in feat.get("traits", [])}
    required_elements = traits.intersection(KINETICIST_ELEMENTS)
    
    # Non-elemental kineticist feats (e.g. Weapon Infusion, Versatile Blast) are universal
    if not required_elements:
        return True
        
    # All elemental traits on the feat/impulse must be in the Kineticist's gate
    return required_elements.issubset(gate_elements)


def _get_known_subclasses() -> Set[str]:
    """Reads every subclass option name (and stripped base token) from CLASS_SUBCLASSES[cls]['options']."""
    names: Set[str] = set()
    try:
        from app.engine.subclasses import CLASS_SUBCLASSES
        for cfg in (CLASS_SUBCLASSES or {}).values():
            if isinstance(cfg, dict):
                for opt in cfg.get("options") or []:
                    if isinstance(opt, dict) and isinstance(opt.get("name"), str):
                        n = opt["name"].strip().lower()
                        if len(n) >= 4:
                            names.add(n)
                        core = re.sub(r"\s*\([^)]*\)", "", n).strip()
                        if len(core) >= 4:
                            names.add(core)
    except Exception:
        pass
    return names


def _extract_prereq_clauses(feat: Dict[str, Any]) -> List[str]:
    """Collects structured prerequisites and any 'Prerequisites ...' clause from description."""
    raw = feat.get("prerequisites") or feat.get("prerequisite") or []
    clauses = [str(raw)] if isinstance(raw, str) else [str(p) for p in raw if p]
    desc = str(feat.get("description") or "")
    m = re.search(r"\bprerequisites?\s*:?\s*([^.\n]+)", desc, re.IGNORECASE)
    if m:
        for part in re.split(r"[;]", m.group(1)):
            if part.strip():
                clauses.append(part.strip())
    return clauses


def _match_single_term(
    term: str,
    skill_ranks: Dict[str, int],
    owned_lower: Set[str],
    attribute_mods: Dict[str, int],
    active_blob: str,
) -> bool:
    """Evaluates a single atomic prerequisite term (skill, attribute, subclass, or owned feat/feature)."""
    t_clean = term.strip().rstrip(".")
    if "assassin dedication" in t_clean.lower() and ("rogue dedication" in owned_lower or "rogue" in active_blob):
        return True
    t_lower = t_clean.lower()
    if not t_lower:
        return True

    # 1. Generic skill checks ("trained in at least one skill", "trained in Lore", Recall Knowledge skills)
    if "recall knowledge" in t_lower:
        rk_m = re.search(r"\b(trained|expert|master|legendary)\b", t_lower)
        req_r = RANK_MAP.get(rk_m.group(1), 2) if rk_m else 2
        rk_skills = ("arcana", "crafting", "lore", "medicine", "nature", "occultism", "religion", "society")
        return any(any(rk in k.lower() for rk in rk_skills) and v >= req_r for k, v in skill_ranks.items())
    if "trained in at least one skill" in t_lower:
        return any(v >= 2 for v in skill_ranks.values())
    if re.fullmatch(r"(trained|expert|master|legendary)\s+in\s+lore", t_lower):
        req_r = RANK_MAP.get(t_lower.split()[0], 2)
        return any("lore" in k.lower() and v >= req_r for k, v in skill_ranks.items())

    # 2. Skill rank check: "trained in Medicine", "expert in Occultism"
    skill_match = re.search(r"\b(trained|expert|master|legendary)\s+in\s+([A-Za-z\s]+)$", t_lower)
    if skill_match:
        req_rank = RANK_MAP.get(skill_match.group(1), 2)
        req_skill = skill_match.group(2).strip().lower()
        return skill_ranks.get(req_skill, 0) >= req_rank

    # 3. Attribute check: Remaster ("Constitution +2") or Legacy ("Strength 14")
    remaster_attr = re.search(r"\b(strength|dexterity|constitution|intelligence|wisdom|charisma)\s*([+-]\d+)\b", t_lower)
    if remaster_attr:
        attr_key = remaster_attr.group(1)[:3]
        target_mod = int(remaster_attr.group(2))
        return attribute_mods.get(attr_key, 0) >= target_mod

    legacy_attr = re.search(r"\b(strength|dexterity|constitution|intelligence|wisdom|charisma)\s+(\d+)\b", t_lower)
    if legacy_attr:
        attr_key = legacy_attr.group(1)[:3]
        target_mod = (int(legacy_attr.group(2)) - 10) // 2
        return attribute_mods.get(attr_key, 0) >= target_mod

    # 4. Armor / proficiency / generic trait phrases
    if t_lower in {"medium armor", "heavy armor", "light armor", "unarmored defense", "martial weapons", "simple weapons"} or any(
        phrase in t_lower for phrase in ("follower of a specific religion", "laws of mortality", "deity who grants", "patron deity")
    ):
        return True

    # 5. Subclass-granted reactions/features
    subclass_feature_map = {
        "selfish shield": "desecrator",
        "glimpse of redemption": "redeemer",
        "retributive strike": "paladin",
        "liberating step": "liberator",
        "iron command": "tyrant",
        "destructive vengeance": "antipaladin",
        "flash of grandeur": "grandeur",
    }
    if t_lower in subclass_feature_map:
        return subclass_feature_map[t_lower] in active_blob

    # 6. Strip trailing subclass category noun ("mastermind racket" -> "mastermind", "enigma muse" -> "enigma")
    stripped_sub = re.sub(
        r"\s+(cause|instinct|order|racket|muse|style|doctrine|mystery|patron|methodology|way|study|field|practice|eidolon|bloodline|conscious mind|subconscious mind|innovation|hybrid study|patron theme|implement)$",
        "",
        t_lower,
    ).strip()

    # Check active subclass/archetype/class blob
    if active_blob and (
        re.search(r"\b" + re.escape(t_lower) + r"\b", active_blob)
        or (len(stripped_sub) >= 4 and re.search(r"\b" + re.escape(stripped_sub) + r"\b", active_blob))
    ):
        return True

    # Check owned feats / features
    for owned in owned_lower:
        owned_core = re.sub(r"\s*\([^)]*\)", "", owned).strip()
        if t_lower == owned or t_lower == owned_core or (len(t_lower) >= 5 and t_lower in owned):
            return True

    return False


def _check_subclass_compatibility(
    feat: Dict[str, Any],
    prereqs: List[str],
    owned_lower: Set[str],
    subclass_name: str = "",
    archetype_name: str = "",
) -> bool:
    """Sanctification polarity guard (Holy vs. Unholy causes/options)."""
    active_blob = f"{(subclass_name or '').lower()} {(archetype_name or '').lower()}".strip()
    prereq_blob = " ".join(p.lower() for p in prereqs if p)
    if not prereq_blob:
        return True

    if "holy" in active_blob and "unholy" not in active_blob:
        if re.search(r"\bunholy\b", prereq_blob):
            return False
    elif "unholy" in active_blob:
        if re.search(r"\bholy\b", prereq_blob):
            return False
    return True


def check_feat_prerequisites(
    feat: Dict[str, Any],
    skill_ranks: Dict[str, int],
    owned_feat_names: Set[str],
    attribute_mods: Dict[str, int],
    character_level: int,
    subclass_name: str = "",
    archetype_name: str = ""
) -> bool:
    skill_ranks = {str(k).strip().lower(): int(v) for k, v in (skill_ranks or {}).items()}
    """Validates whether a character meets all prerequisites for a feat (including Remaster modifiers, OR/AND lists, and subclasses)."""
    prereqs = _extract_prereq_clauses(feat)
    owned_lower = {f.lower().strip() for f in owned_feat_names}
    class_traits = [t.lower() for t in (feat.get("traits") or [])]
    active_blob = f"{(subclass_name or '').lower()} {(archetype_name or '').lower()} {' '.join(class_traits)}".strip()

    if not _check_subclass_compatibility(
        feat=feat,
        prereqs=prereqs,
        owned_lower=owned_lower,
        subclass_name=subclass_name,
        archetype_name=archetype_name,
    ):
        return False

    for p in prereqs:
        p_clean = p.strip()
        p_lower = p_clean.lower()

        # 0. Companion / Familiar / Eidolon gating
        if "animal companion" in p_lower or "steed" in feat.get("name", "").lower():
            has_ac = any(k in o for o in owned_lower for k in ("animal companion", "plant companion", "cavalier dedication", "beastmaster dedication"))
            if not has_ac:
                return False
        if "familiar" in p_lower and "familiar" not in feat.get("name", "").lower():
            has_fam = any(k in o for o in owned_lower for k in ("familiar", "leaf order", "witch"))
            if not has_fam:
                return False
        if "eidolon" in p_lower:
            has_eid = any(k in o for o in owned_lower for k in ("eidolon", "summoner"))
            if not has_eid:
                return False

        # Expand multi-skill OR lists: "trained in Arcana, Nature, Occultism, or Religion"
        multi_skill = re.match(r"^(trained|expert|master|legendary)\s+in\s+(.+\bor\b.+)$", p_lower)
        if multi_skill:
            rank_word = multi_skill.group(1)
            options = [x.strip() for x in re.split(r",|\bor\b", multi_skill.group(2)) if x.strip()]
            if any(_match_single_term(f"{rank_word} in {opt}", skill_ranks, owned_lower, attribute_mods, active_blob) for opt in options):
                continue
            return False

        # Expand "trained in Acrobatics and medium armor"
        if " and " in p_lower and p_lower.startswith(("trained in ", "expert in ", "master in ", "legendary in ")):
            parts = [x.strip() for x in p_lower.split(" and ") if x.strip()]
            if all(_match_single_term(part, skill_ranks, owned_lower, attribute_mods, active_blob) for part in parts):
                continue
            return False

        # Expand general OR alternatives: "empiricism or interrogation methodology", "Gunslinger or Dual-Weapon Warrior Dedication"
        if " or " in p_lower:
            # Propagate trailing category noun if omitted on first branch ("empiricism or interrogation methodology")
            suffix_m = re.search(r"\s+(cause|instinct|order|racket|muse|style|doctrine|mystery|patron|methodology|way|study|dedication)$", p_lower)
            suffix = f" {suffix_m.group(1)}" if suffix_m else ""
            branches = [b.strip() for b in re.split(r",|\bor\b", p_lower) if b.strip()]
            expanded = [b if (not suffix or b.endswith(suffix.strip())) else f"{b}{suffix}" for b in branches]
            if any(_match_single_term(b, skill_ranks, owned_lower, attribute_mods, active_blob) for b in expanded):
                continue
            return False

        # Single atomic prerequisite term (handles both capitalized and lowercase terms!)
        if not _match_single_term(p_clean, skill_ranks, owned_lower, attribute_mods, active_blob):
            return False

    return True


def calculate_feat_weight(
    feat: Dict[str, Any],
    class_name: str,
    owned_feat_names: Set[str],
    skill_ranks: Dict[str, int]
) -> float:
    """Calculates selection weight with bonuses for class flavor and feat chains."""
    cls_key = class_name.lower()
    weight = 1.0

    prereqs = feat.get("prerequisites") or feat.get("prerequisite") or []
    if isinstance(prereqs, str):
        prereqs = [prereqs]

    owned_lower = {f.lower().strip() for f in owned_feat_names}

    # 1. Feat Chain Bonus (Prior parent feat owned -> 6x weight)
    for p in prereqs:
        p_lower = p.lower().strip()
        for owned in owned_lower:
            base_owned = re.sub(r"\s*\([^)]*\)", "", owned).strip()
            if p_lower == owned or p_lower == base_owned or p_lower in owned:
                weight *= 6.0
                break

        # 1b. Thematic Feat Family Affinity (Stances, Ki chains, Styles -> 10x weight)
    families = FEAT_FAMILIES.get(cls_key, [])
    feat_name_lower = feat.get("name", "").lower().strip()
    clean_feat_name = re.sub(r"\s*\([^)]*\)", "", feat_name_lower).strip()

    for fam in families:
        # Check if candidate feat belongs to this family
        in_fam = any(m in clean_feat_name for m in fam)
        if in_fam:
            # Check if any currently owned feat belongs to this same family
            for owned in owned_lower:
                clean_owned = re.sub(r"\s*\([^)]*\)", "", owned).strip()
                if any(m in clean_owned for m in fam):
                    weight *= 10.0
                    break
            break

    # 1c. Hard-depress redundant base stances if already in a stance family
    is_candidate_stance = "stance" in clean_feat_name or "stance" in [t.lower() for t in feat.get("traits", [])]
    if is_candidate_stance:
        owned_stances = [o for o in owned_lower if "stance" in o]
        if owned_stances:
            # Check if this stance shares an established feat family with an owned stance
            shares_family = False
            for fam in families:
                if any(m in clean_feat_name for m in fam):
                    if any(any(m in ost for m in fam) for ost in owned_stances):
                        shares_family = True
                        break
            # If not in the same stance tree, drop weight to virtually 0 so it is never picked
            if not shares_family:
                return 0.0

    # 1d. Monk Ki Discipline Selection Balancing
    if cls_key == "monk":
        is_ki_candidate = any(k in clean_feat_name for k in ["ki", "qi", "wholeness", "abundant"]) or "focus" in [t.lower() for t in feat.get("traits", [])]
        has_ki_feat = any(any(k in o for k in ["ki", "qi", "wholeness", "abundant"]) for o in owned_lower)
        
        # At initial selection (no ki feats owned yet), boost Ki candidate to contend against large stance pool
        if is_ki_candidate and not has_ki_feat:
            weight *= 8.0
            
        # If the monk has already begun walking the Ki path, prioritize scaling the discipline
        elif is_ki_candidate and has_ki_feat:
            weight *= 35.0
            # Explicit progression priority per milestone tier
            if "wholeness of body" in clean_feat_name and not any("wholeness" in o for o in owned_lower):
                weight *= 3.0
            elif "abundant step" in clean_feat_name and not any("abundant" in o for o in owned_lower):
                weight *= 3.0
            elif "ki rush" in clean_feat_name and not any("rush" in o for o in owned_lower):
                weight *= 2.0

    # 2. Class Skill Thematic Bonus (3x weight if feat uses class-priority skill)
    priority_skills = CLASS_PRIORITY_SKILLS.get(cls_key, [])
    feat_traits = [t.lower() for t in feat.get("traits", [])]
    desc = feat.get("description", "").lower()

    for p_skill in priority_skills:
        p_skill_lower = p_skill.lower()
        if p_skill_lower in feat_traits or f"in {p_skill_lower}" in desc or f"{p_skill_lower} check" in desc:
            weight *= 2.5
            break

    # 3. Class Trait Match for Class Feats
    if cls_key in feat_traits:
        weight *= 2.0

    return max(0.1, weight)
