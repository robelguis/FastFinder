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
