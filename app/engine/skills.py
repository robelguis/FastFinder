import random
from typing import Dict, List, Set, Any
from app.engine.models import SkillEntry

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
    for s in background_data.get("trained_skills", []):
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
            rank_letter="T",
            modifier=2 + level + int_mod
        ))

    # 2. Class Mandatory Skills
    for s in profile.get("mandatory", []):
        if s in CORE_SKILLS:
            trained_set.add(s)

    # Class Choice picks
    if "choice_pick" in profile:
        choices = [c for c in profile["choice_pick"] if c in CORE_SKILLS]
        if choices:
            choice = max(choices, key=lambda c: attribute_mods.get(CORE_SKILLS.get(c, "str"), 0))
            trained_set.add(choice)

    # 3. Class Free Skill Budget = Base Count + Int Modifier (minimum 1)
    int_mod = attribute_mods.get("int", 0)
    budget = max(1, profile.get("base_count", 3) + int_mod)

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

    # 4. Compile the FULL list of all 16 skills (Trained & Untrained)
    all_skill_entries: List[SkillEntry] = []
    for skill_name, attr in sorted(CORE_SKILLS.items()):
        is_trained = skill_name in trained_set
        mod_val = attribute_mods.get(attr, 0)
        
        if is_trained:
            rank_bonus = 2
            rank_letter = "T"
            total_mod = rank_bonus + level + mod_val
        else:
            rank_bonus = 0
            rank_letter = "U"
            total_mod = mod_val  # PF2e Untrained = 0 rank + 0 level + attribute mod

        all_skill_entries.append(SkillEntry(
            name=skill_name,
            attribute=attr,
            rank=rank_bonus,
            rank_letter=rank_letter,
            modifier=total_mod
        ))

    return all_skill_entries + lore_entries
