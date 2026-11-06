from typing import List, Dict, Any, Optional
import random

# Standard PF2e Skill List (excluding Lore)
ALL_PF2E_SKILLS = [
    "Acrobatics", "Arcana", "Athletics", "Crafting", "Deception",
    "Diplomacy", "Intimidation", "Medicine", "Nature", "Occultism",
    "Performance", "Religion", "Society", "Stealth", "Survival", "Thievery"
]

PROFICIENCY_RANK_MAP = {
    "Untrained": 0,
    "Trained": 2,
    "Expert": 4,
    "Master": 6,
    "Legendary": 8
}

RANK_NAME_MAP = {v: k for k, v in PROFICIENCY_RANK_MAP.items()}

SKILL_KEY_ABILITY = {
    "Acrobatics": "DEX", "Arcana": "INT", "Athletics": "STR", "Crafting": "INT",
    "Deception": "CHA", "Diplomacy": "CHA", "Intimidation": "CHA", "Medicine": "WIS",
    "Nature": "WIS", "Occultism": "INT", "Performance": "CHA", "Religion": "WIS",
    "Society": "INT", "Stealth": "DEX", "Survival": "WIS", "Thievery": "DEX"
}


def get_skill_increases_count(character_class: str, target_level: int) -> int:
    """
    Returns the total number of Skill Increases earned up to target_level.
    Rogues and Investigators gain skill increases at every level starting at level 2.
    Standard classes gain skill increases at odd levels 3, 5, 7, 9, 11, 13, 15, 17, 19.
    """
    if target_level < 2:
        return 0

    cls_lower = (character_class or "").lower()
    if cls_lower in ["rogue", "investigator"]:
        return max(0, target_level - 1)
    else:
        return sum(1 for lvl in range(3, target_level + 1, 2) if lvl <= 19)


def resolve_character_skills(
    character_class: str,
    background: Dict[str, Any],
    ability_mods: Dict[str, int],
    target_level: int,
    int_mod: int,
    existing_skills: Optional[List[Dict[str, Any]]] = None,
    existing_lore: Optional[str] = None
) -> Dict[str, Any]:
    """
    Resolves skill proficiencies and Lore.
    Preserves existing trained skills, ranks, and chosen lore during level adjustments.
    """
    # 1. Determine Lore
    if existing_lore:
        chosen_lore = existing_lore
    else:
        lore_options = background.get("lore_options", [])
        if lore_options:
            chosen_lore = random.choice(lore_options)
        else:
            chosen_lore = f"{background.get('name', 'Settler')} Lore"

    # Map existing skills if present: { "Athletics": {"rank": "Trained", ...} }
    existing_map = {}
    if existing_skills:
        for sk in existing_skills:
            if isinstance(sk, dict) and "name" in sk:
                existing_map[sk["name"]] = sk

    # 2. Extract or pick baseline trained skills (Level 1 baseline)
    trained_skills = set()
    if existing_map:
        for name, sk_data in existing_map.items():
            if name != chosen_lore and sk_data.get("rank") in ["Trained", "Expert", "Master", "Legendary"]:
                trained_skills.add(name)
    else:
        class_trained = set(background.get("mandatory_skills", []))
        base_count = background.get("class_skill_count", 3)
        total_picks = max(1, base_count + int_mod)

        available_pool = [s for s in ALL_PF2E_SKILLS if s not in class_trained]
        random.shuffle(available_pool)
        
        needed = max(0, total_picks - len(class_trained))
        selected_free = set(available_pool[:needed])
        trained_skills = class_trained.union(selected_free)

    # 3. Handle Skill Increases for target_level (Expert, Master, Legendary)
    num_increases = get_skill_increases_count(character_class, target_level)
    
    skill_ranks: Dict[str, int] = {}
    for sk in ALL_PF2E_SKILLS:
        skill_ranks[sk] = 2 if sk in trained_skills else 0

    lore_rank = 2

    if existing_map:
        previously_boosted = []
        for name in trained_skills:
            prev_rank_str = existing_map.get(name, {}).get("rank", "Trained")
            prev_val = PROFICIENCY_RANK_MAP.get(prev_rank_str, 2)
            if prev_val > 2:
                previously_boosted.append((name, prev_val))

        increases_applied = 0
        for name, prev_val in previously_boosted:
            needed_increases = 1 if prev_val == 4 else (2 if prev_val == 6 else 3)
            if increases_applied + needed_increases <= num_increases:
                if prev_val == 4 and target_level >= 2:
                    skill_ranks[name] = 4
                    increases_applied += 1
                elif prev_val == 6 and target_level >= 7:
                    skill_ranks[name] = 6
                    increases_applied += 2
                elif prev_val == 8 and target_level >= 15:
                    skill_ranks[name] = 8
                    increases_applied += 3
        
        remaining_increases = num_increases - increases_applied
        while remaining_increases > 0:
            eligible_for_expert = [
                s for s in trained_skills 
                if skill_ranks[s] == 2 and target_level >= 2
            ]
            if eligible_for_expert:
                boost_target = random.choice(eligible_for_expert)
                skill_ranks[boost_target] = 4
                remaining_increases -= 1
                continue

            eligible_for_master = [
                s for s in trained_skills 
                if skill_ranks[s] == 4 and target_level >= 7
            ]
            if eligible_for_master:
                boost_target = random.choice(eligible_for_master)
                skill_ranks[boost_target] = 6
                remaining_increases -= 1
                continue

            break
    else:
        remaining = num_increases
        while remaining > 0:
            eligible = [s for s in trained_skills if skill_ranks[s] == 2 and target_level >= 2]
            if not eligible:
                break
            chosen = random.choice(eligible)
            skill_ranks[chosen] = 4
            remaining -= 1

    # 4. Construct final skill payload with calculated modifiers
    final_skills = []
    for sk_name in ALL_PF2E_SKILLS:
        rank_val = skill_ranks.get(sk_name, 0)
        rank_name = RANK_NAME_MAP.get(rank_val, "Untrained")
        key_ab = SKILL_KEY_ABILITY[sk_name]
        ab_mod = ability_mods.get(key_ab, 0)
        
        prof_bonus = (rank_val + target_level) if rank_val > 0 else 0
        total_mod = prof_bonus + ab_mod

        final_skills.append({
            "name": sk_name,
            "rank": rank_name,
            "ability": key_ab,
            "item_bonus": 0,
            "total": total_mod
        })

    # Add Lore
    lore_ab_mod = ability_mods.get("INT", 0)
    lore_prof_bonus = lore_rank + target_level
    final_skills.append({
        "name": chosen_lore,
        "rank": RANK_NAME_MAP.get(lore_rank, "Trained"),
        "ability": "INT",
        "item_bonus": 0,
        "total": lore_prof_bonus + lore_ab_mod,
        "is_lore": True
    })

    return {
        "skills": final_skills,
        "lore": chosen_lore
    }
