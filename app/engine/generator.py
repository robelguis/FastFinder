from typing import Dict, Any, Optional, List
from app.engine.skills import resolve_character_skills

def recalculate_vitals(character: Dict[str, Any], target_level: int) -> Dict[str, Any]:
    """
    Recalculates level-dependent vitals such as HP, Perception, Class DC, and Saving Throws.
    """
    con_mod = character.get("ability_modifiers", {}).get("CON", 0)
    hp_per_lvl = character.get("class_hp_per_level", 8)
    ancestry_hp = character.get("ancestry_hp", 8)

    # HP = Ancestry HP + (Class HP + CON mod) * Level
    character["max_hp"] = ancestry_hp + ((hp_per_lvl + con_mod) * target_level)
    character["current_hp"] = character["max_hp"]

    # Perception scaling
    wis_mod = character.get("ability_modifiers", {}).get("WIS", 0)
    perc_rank = character.get("perception_rank_val", 2)  # Trained default
    character["perception"] = perc_rank + target_level + wis_mod

    # Class DC scaling (Key ability + Rank (Trained=2) + Level)
    key_ability = character.get("key_ability", "STR")
    key_mod = character.get("ability_modifiers", {}).get(key_ability, 0)
    character["class_dc"] = 10 + 2 + target_level + key_mod

    return character


def level_up(
    char_data: Dict[str, Any],
    target_level: int,
    use_dedication: bool = False,
    archetype: Optional[str] = None
) -> Dict[str, Any]:
    """
    Advances or regresses a character sheet to target_level while locking
    baseline trained skills, lore, and inventory items.
    """
    character_class = char_data.get("class", "Fighter")
    background = char_data.get("background", {})
    ability_mods = char_data.get("ability_modifiers", {})
    int_mod = ability_mods.get("INT", 0)

    # 1. Extract existing skills and chosen lore from character payload
    existing_skills = char_data.get("skills", [])
    
    existing_lore = char_data.get("lore")
    if not existing_lore and existing_skills:
        for sk in existing_skills:
            if isinstance(sk, dict) and (sk.get("is_lore") or "Lore" in sk.get("name", "")):
                existing_lore = sk.get("name")
                break

    # 2. Resolve skills with locked inputs
    resolved_skills_data = resolve_character_skills(
        character_class=character_class,
        background=background,
        ability_mods=ability_mods,
        target_level=target_level,
        int_mod=int_mod,
        existing_skills=existing_skills,
        existing_lore=existing_lore
    )

    # 3. Preserve equipped weapons & gear if present
    preserved_weapons = char_data.get("weapons", char_data.get("equipped_weapons", []))

    # 4. Reconstruct sheet with updated level, vitals, and preserved skills
    updated_character = char_data.copy()
    updated_character["level"] = target_level
    updated_character["skills"] = resolved_skills_data["skills"]
    updated_character["lore"] = resolved_skills_data["lore"]
    
    if preserved_weapons:
        updated_character["weapons"] = preserved_weapons

    # Recalculate level-dependent vitals
    updated_character = recalculate_vitals(updated_character, target_level)

    return updated_character
