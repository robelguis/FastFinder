import re
from typing import Dict, Any, List

RANK_MAP = {
    "untrained": 0,
    "trained": 2,
    "expert": 4,
    "master": 6,
    "legendary": 8,
}

SKILL_NAMES = [
    "acrobatics", "arcana", "athletics", "crafting", "deception",
    "diplomacy", "intimidation", "lore", "medicine", "nature",
    "occultism", "performance", "religion", "society", "stealth",
    "survival", "thievery"
]

ATTR_KEYS = {
    "strength": "str", "str": "str",
    "dexterity": "dex", "dex": "dex",
    "constitution": "con", "con": "con",
    "intelligence": "int", "int": "int",
    "wisdom": "wis", "wis": "wis",
    "charisma": "cha", "cha": "cha",
}

def meets_prerequisites(
    feat: Dict[str, Any],
    skills_by_name: Dict[str, int],
    mods: Dict[str, int],
    existing_feat_names: List[str]
) -> bool:
    raw_prereqs = feat.get("prerequisites", [])
    if isinstance(raw_prereqs, dict):
        raw_prereqs = raw_prereqs.get("value", [])

    if not raw_prereqs:
        return True

    normalized_existing_feats = {f.lower().strip() for f in existing_feat_names}

    for req in raw_prereqs:
        if not isinstance(req, str):
            continue
        req_clean = req.strip()
        req_lower = req_clean.lower()

        # Attribute Check (e.g. "Strength +2", "Dexterity 14", "Wisdom +1")
        attr_match = re.search(r'\b(strength|dexterity|constitution|intelligence|wisdom|charisma|str|dex|con|int|wis|cha)\b\s*(\+?\d+)', req_lower)
        if attr_match:
            attr_token = attr_match.group(1)
            attr_name = ATTR_KEYS.get(attr_token)
            if attr_name:
                val = int(attr_match.group(2).replace("+", ""))
                required_mod = (val - 10) // 2 if val >= 10 else val
                if mods.get(attr_name, 0) < required_mod:
                    return False

        # Skill Rank Check (e.g. "trained in Athletics", "expert in Medicine or Nature")
        rank_match = re.search(r'\b(trained|expert|master|legendary)\b\s+in\s+([a-zA-Z\s/]+)', req_lower)
        if rank_match:
            required_rank_name = rank_match.group(1)
            target_skills_str = rank_match.group(2)
            required_rank = RANK_MAP.get(required_rank_name, 2)

            required_skills_found = [s for s in SKILL_NAMES if s in target_skills_str]
            if required_skills_found:
                has_any = any(skills_by_name.get(s, 0) >= required_rank for s in required_skills_found)
                if not has_any:
                    return False

        # Prerequisite Feat Check
        if not attr_match and not rank_match and len(req_clean) > 2:
            if not any(token in req_lower for token in ["member", "worshiper", "must", "access"]):
                if req_lower not in normalized_existing_feats:
                    return False

    return True
