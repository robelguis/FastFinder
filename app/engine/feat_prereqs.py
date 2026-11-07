
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

def check_feat_prerequisites(
    feat: Dict[str, Any],
    skill_ranks: Dict[str, int],
    owned_feat_names: Set[str],
    attribute_mods: Dict[str, int],
    character_level: int
) -> bool:
    """Validates whether a character meets all prerequisites for a feat."""
    prereqs = feat.get("prerequisites") or feat.get("prerequisite") or []
    if isinstance(prereqs, str):
        prereqs = [prereqs]

    owned_lower = {f.lower().strip() for f in owned_feat_names}

    for p in prereqs:
        p_clean = p.strip()
        p_lower = p_clean.lower()

        # 1. Skill rank check: e.g. "trained in Medicine", "expert in Athletics"
        skill_match = re.search(r"(trained|expert|master|legendary)\s+in\s+([A-Za-z\s]+)", p_lower)
        if skill_match:
            req_rank_name = skill_match.group(1)
            req_skill = skill_match.group(2).strip().title()
            req_rank = RANK_MAP.get(req_rank_name, 2)

            curr_rank = skill_ranks.get(req_skill, 0)
            if curr_rank < req_rank:
                return False
            continue

        # 2. Feat prerequisite check: e.g. "Nimble Dodge", "Battle Medicine"
        # Match against owned feats (accounting for subchoice suffixes like "(Forest)")
        feat_matched = False
        for owned in owned_lower:
            base_owned = re.sub(r"\s*\([^)]*\)", "", owned).strip()
            if p_lower == owned or p_lower == base_owned or p_lower in owned:
                feat_matched = True
                break
        
        # If the requirement isn't an attribute/general rule and not matched as owned feat:
        if not feat_matched:
            # Check for attribute requirements like "Strength 14" (+2 mod)
            attr_match = re.search(r"(strength|dexterity|constitution|intelligence|wisdom|charisma)\s+(\d+)", p_lower)
            if attr_match:
                attr_name = attr_match.group(1)[:3]
                target_score = int(attr_match.group(2))
                target_mod = (target_score - 10) // 2
                if attribute_mods.get(attr_name, 0) < target_mod:
                    return False
                continue

            # Check if this is an explicit feat requirement
            # Feat names in PF2e compendium prerequisites are capitalized titles
            if p_clean and p_clean[0].isupper() and " " in p_clean and not p_lower.startswith("trained"):
                if not feat_matched:
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
