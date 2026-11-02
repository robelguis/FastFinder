import random
from typing import Dict, Any, List
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
    "Thievery": "dex",
}

CLASS_TRAINED_SKILLS: Dict[str, List[str]] = {
    "fighter": ["Acrobatics", "Athletics"],
    "rogue": ["Stealth", "Thievery", "Deception", "Acrobatics"],
    "wizard": ["Arcana"],
    "cleric": ["Religion"],
    "barbarian": ["Athletics"],
    "bard": ["Performance", "Occultism"],
    "druid": ["Nature", "Survival"],
    "ranger": ["Nature", "Survival", "Athletics"],
    "champion": ["Religion", "Athletics"],
    "monk": ["Athletics", "Acrobatics"],
    "swashbuckler": ["Acrobatics"],
    "investigator": ["Society"],
    "thaumaturge": ["Arcana", "Occultism", "Religion", "Nature"],
    "psychic": ["Occultism"],
    "oracle": ["Religion"],
    "witch": ["Arcana", "Occultism"],
    "kineticist": ["Nature"],
    "alchemist": ["Crafting"],
    "gunslinger": ["Acrobatics"],
}

def resolve_character_skills(
    class_name: str,
    background_data: Dict[str, Any],
    attribute_mods: Dict[str, int],
    level: int = 1
) -> List[SkillEntry]:
    cls_key = class_name.lower()
    
    # 1. Base trained skills
    base_trained = list(CLASS_TRAINED_SKILLS.get(cls_key, ["Athletics"]))
    
    # 2. Background skill & Lore
    bg_skills = background_data.get("skills", [])
    for sk in bg_skills:
        sk_title = sk.title()
        if sk_title in CORE_SKILLS and sk_title not in base_trained:
            base_trained.append(sk_title)

    lore_name = background_data.get("lore")
    if not lore_name or lore_name.strip().lower() == "lore":
        bg_name = background_data.get("name", "").strip()
        lore_name = f"{bg_name} Lore" if bg_name else "Settlement Lore"
    else:
        if not lore_name.endswith("Lore"):
            lore_name = f"{lore_name} Lore" 
    
    # 3. Extra skill picks (2 + INT mod, min 1; Rogue/Investigator get 7)
    int_mod = attribute_mods.get("int", 0)
    extra_count = 7 + int_mod if cls_key in ["rogue", "investigator"] else 2 + int_mod
    extra_count = max(1, extra_count)

    remaining_pool = [s for s in CORE_SKILLS.keys() if s not in base_trained]
    random.shuffle(remaining_pool)
    trained_skills_set = set(base_trained + remaining_pool[:extra_count])

    # 4. Level 3 Skill Increase: promote 1 trained skill to Expert (rank 4)
    expert_skills_set = set()
    if level >= 3 and trained_skills_set:
        promoted = random.choice(list(trained_skills_set))
        expert_skills_set.add(promoted)

    skills_list: List[SkillEntry] = []
    for skill_name, attr in sorted(CORE_SKILLS.items()):
        attr_val = attribute_mods.get(attr, 0)
        if skill_name in expert_skills_set:
            rank = 4
            rank_letter = "E"
            modifier = rank + level + attr_val
        elif skill_name in trained_skills_set:
            rank = 2
            rank_letter = "T"
            modifier = rank + level + attr_val
        else:
            rank = 0
            rank_letter = "U"
            modifier = attr_val

        skills_list.append(SkillEntry(
            name=skill_name,
            attribute=attr.upper(),
            rank=rank,
            rank_letter=rank_letter,
            modifier=modifier
        ))

    # Append Lore skill (always trained, scales with INT)
    lore_attr_val = attribute_mods.get("int", 0)
    skills_list.append(SkillEntry(
        name=lore_name,
        attribute="INT",
        rank=2,
        rank_letter="T",
        modifier=2 + level + lore_attr_val
    ))

    return skills_list
