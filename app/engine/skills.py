import random
from typing import Dict, List, Set, Any
from app.engine.models import SkillEntry

# The 16 Core PF2e Skills and their governing attributes
CORE_SKILLS: Dict[str, str] = {
    "Acrobatics": "dex",
    "Arcana": "int",
    "Athletics": "str",
    "Crafting": "int",
    "Deception": "cha",
    "Diplomacy": "cha",
    "Intimidation": "cha",
    "Medicine": "wis",
    "Nature": "wis",
    "Occultism": "int",
    "Performance": "cha",
    "Religion": "wis",
    "Society": "int",
    "Stealth": "dex",
    "Survival": "wis",
    "Thievery": "dex"
}

# Standard PF2e Class Skill Allocations (Mandatory skills + base additional budget)
CLASS_SKILL_PROFILES: Dict[str, Dict[str, Any]] = {
    "barbarian": {
        "mandatory": ["Athletics"],
        "base_count": 3,
        "priority": ["Intimidation", "Survival", "Acrobatics"]
    },
    "bard": {
        "mandatory": ["Occultism", "Performance"],
        "base_count": 4,
        "priority": ["Deception", "Diplomacy", "Society", "Stealth"]
    },
    "champion": {
        "mandatory": ["Religion"],
        "base_count": 2,
        "priority": ["Athletics", "Diplomacy", "Intimidation", "Medicine"]
    },
    "cleric": {
        "mandatory": ["Religion"],
        "base_count": 2,
        "priority": ["Medicine", "Diplomacy", "Survival", "Society"]
    },
    "druid": {
        "mandatory": ["Nature"],
        "base_count": 2,
        "priority": ["Survival", "Medicine", "Athletics", "Crafting"]
    },
    "fighter": {
        "mandatory": [],
        "choice_pick": ["Acrobatics", "Athletics"],
        "base_count": 3,
        "priority": ["Athletics", "Acrobatics", "Intimidation", "Crafting"]
    },
    "monk": {
        "mandatory": [],
        "choice_pick": ["Acrobatics", "Athletics"],
        "base_count": 4,
        "priority": ["Acrobatics", "Athletics", "Stealth", "Religion"]
    },
    "ranger": {
        "mandatory": ["Nature", "Survival"],
        "base_count": 4,
        "priority": ["Athletics", "Stealth", "Acrobatics", "Medicine"]
    },
    "rogue": {
        "mandatory": ["Stealth"],
        "base_count": 7,
        "priority": ["Thievery", "Deception", "Acrobatics", "Diplomacy", "Intimidation", "Society"]
    },
    "sorcerer": {
        "mandatory": [],
        "base_count": 2,
        "priority": ["Deception", "Diplomacy", "Intimidation", "Arcana", "Occultism"]
    },
    "witch": {
        "mandatory": [],
        "base_count": 3,
        "priority": ["Arcana", "Occultism", "Nature", "Religion", "Crafting"]
    },
    "wizard": {
        "mandatory": ["Arcana"],
        "base_count": 2,
        "priority": ["Crafting", "Society", "Occultism", "Nature"]
    }
}

def resolve_character_skills(
    class_name: str,
    background_data: Dict[str, Any],
    attribute_mods: Dict[str, int],
    level: int = 1
) -> List[SkillEntry]:
    cls_key = class_name.lower()
    profile = CLASS_SKILL_PROFILES.get(cls_key, {
        "mandatory": [],
        "base_count": 3,
        "priority": ["Athletics", "Acrobatics", "Stealth"]
    })

    trained_set: Set[str] = set()
    lore_entries: List[SkillEntry] = []

    # 1. Background Skills
    bg_skills = background_data.get("trained_skills", [])
    for s in bg_skills:
        clean = s.title()
        if clean in CORE_SKILLS:
            trained_set.add(clean)

    # Background Lore
    bg_lore = background_data.get("trained_lore")
    if bg_lore:
        lore_name = f"Lore: {bg_lore.title()}"
        int_mod = attribute_mods.get("int", 0)
        lore_entries.append(SkillEntry(
            name=lore_name,
            attribute="int",
            rank=2,
            modifier=2 + level + int_mod
        ))

    # 2. Mandatory Class Skills
    for s in profile.get("mandatory", []):
        if s in CORE_SKILLS:
            trained_set.add(s)

    # Choice picks
    if "choice_pick" in profile:
        choices = [c for c in profile["choice_pick"] if c in CORE_SKILLS]
        if choices:
            choice = max(choices, key=lambda c: attribute_mods.get(CORE_SKILLS.get(c, "str"), 0))
            trained_set.add(choice)

    # 3. Class Free Skill Budget = Base Count + Int Modifier (minimum 1 free skill)
    int_mod = attribute_mods.get("int", 0)
    budget = max(1, profile.get("base_count", 3) + int_mod)

    # Candidate pool: preferred skills first, then rest of core skills
    candidates = [s for s in profile.get("priority", []) if s in CORE_SKILLS and s not in trained_set]
    remaining_core = [s for s in CORE_SKILLS.keys() if s not in trained_set and s not in candidates]
    random.shuffle(remaining_core)
    pool = candidates + remaining_core

    for skill in pool:
        if budget <= 0:
            break
        if skill not in trained_set and skill in CORE_SKILLS:
            trained_set.add(skill)
            budget -= 1

    # 4. Build SkillEntry objects
    skill_entries: List[SkillEntry] = []
    for skill in sorted(list(trained_set)):
        attr = CORE_SKILLS[skill]
        mod_val = attribute_mods.get(attr, 0)
        skill_entries.append(SkillEntry(
            name=skill,
            attribute=attr,
            rank=2,
            modifier=2 + level + mod_val
        ))

    return skill_entries + lore_entries
