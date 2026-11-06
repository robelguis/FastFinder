from typing import List, Dict, Any, Optional, Set
import random
from app.engine.models import SkillEntry

ALL_PF2E_SKILLS = [
    "Acrobatics", "Arcana", "Athletics", "Crafting", "Deception",
    "Diplomacy", "Intimidation", "Medicine", "Nature", "Occultism",
    "Performance", "Religion", "Society", "Stealth", "Survival", "Thievery"
]

SKILL_KEY_ABILITY = {
    "Acrobatics": "dex", "Arcana": "int", "Athletics": "str", "Crafting": "int",
    "Deception": "cha", "Diplomacy": "cha", "Intimidation": "cha", "Medicine": "wis",
    "Nature": "wis", "Occultism": "int", "Performance": "cha", "Religion": "wis",
    "Society": "int", "Stealth": "dex", "Survival": "wis", "Thievery": "dex"
}

RANK_LETTER_MAP = {
    0: "U",
    2: "T",
    4: "E",
    6: "M",
    8: "L"
}

RANK_INT_MAP = {
    "untrained": 0, "u": 0,
    "trained": 2, "t": 2,
    "expert": 4, "e": 4,
    "master": 6, "m": 6,
    "legendary": 8, "l": 8
}


def get_skill_increases_count(character_class: str, target_level: int) -> int:
    if target_level < 2:
        return 0
    cls_lower = (character_class or "").lower()
    if cls_lower in ["rogue", "investigator"]:
        return max(0, target_level - 1)
    else:
        return sum(1 for lvl in range(3, target_level + 1, 2) if lvl <= 19)


def resolve_character_skills(
    class_name: Optional[str] = None,
    background_data: Optional[Dict[str, Any]] = None,
    attribute_mods: Optional[Dict[str, int]] = None,
    level: Optional[int] = None,
    feats: Optional[List[Any]] = None,
    planned_archetype: Optional[str] = None,
    existing_skills: Optional[List[Any]] = None,
    existing_lore: Optional[str] = None,
    **kwargs
) -> List[SkillEntry]:
    """
    Resolves skill proficiencies and Lore, returning a list of SkillEntry objects.
    Maintains full compatibility with all parameter name aliases.
    Locks previously chosen trained skills and Lore when leveling up or down.
    Applies Untrained Improvisation scaling to Untrained checks if present in feats.
    """
    cls_name = class_name or kwargs.get("character_class", "Fighter")
    bg = background_data or kwargs.get("background", {})
    mods = attribute_mods or kwargs.get("ability_mods", {})
    target_lvl = level or kwargs.get("target_level", 1)

    norm_mods = {str(k).lower(): v for k, v in mods.items()}
    int_mod = norm_mods.get("int", kwargs.get("int_mod", 0))

    # Detect Untrained Improvisation feat
    all_feats = feats or kwargs.get("chosen_feats", [])
    has_untrained_improvisation = any(
        (f.name if hasattr(f, "name") else (f.get("name") if isinstance(f, dict) else "")).lower() == "untrained improvisation"
        for f in all_feats
    )

    # 1. Extract and preserve Lore
    chosen_lore = existing_lore
    if not chosen_lore:
        lore_opts = bg.get("lore_options", [])
        if lore_opts:
            chosen_lore = random.choice(lore_opts)
        else:
            chosen_lore = f"{bg.get('name', 'Settler')} Lore"

    # 2. Map existing skills
    existing_map: Dict[str, int] = {}
    if existing_skills:
        for sk in existing_skills:
            if isinstance(sk, dict):
                name = sk.get("name")
                raw_rank = sk.get("rank")
                if isinstance(raw_rank, int):
                    rank_val = raw_rank
                else:
                    rank_val = RANK_INT_MAP.get(str(raw_rank).lower(), 0)
                if name:
                    existing_map[name] = rank_val
            elif hasattr(sk, "name"):
                rank_val = getattr(sk, "rank", 0)
                existing_map[sk.name] = rank_val

    # 3. Determine baseline trained skills
    trained_skills: Set[str] = set()
    if existing_map:
        for name, rank_val in existing_map.items():
            if name in ALL_PF2E_SKILLS and rank_val >= 2:
                trained_skills.add(name)
    else:
        bg_skills = bg.get("skills", [])
        mandatory = set()
        for bs in bg_skills:
            for s in ALL_PF2E_SKILLS:
                if s.lower() == bs.lower():
                    mandatory.add(s)

        base_count = bg.get("class_skill_count", 3)
        total_picks = max(1, base_count + int_mod)

        available_pool = [s for s in ALL_PF2E_SKILLS if s not in mandatory]
        random.shuffle(available_pool)
        needed = max(0, total_picks - len(mandatory))
        trained_skills = mandatory.union(set(available_pool[:needed]))

    # 4. Calculate skill ranks and apply increases
    num_increases = get_skill_increases_count(cls_name, target_lvl)
    skill_ranks: Dict[str, int] = {s: (2 if s in trained_skills else 0) for s in ALL_PF2E_SKILLS}

    if existing_map:
        # Determine prioritised skills that already had increases
        boosted_names = [name for name in trained_skills if existing_map.get(name, 2) > 2]
        
        increases_applied = 0
        # Re-apply boosts to the exact same skills up to the new num_increases limit
        for name in boosted_names:
            if increases_applied >= num_increases:
                break
            prev_val = existing_map.get(name, 2)
            
            # Can we restore Master? (Requires level 7+ and 2 increases)
            if prev_val >= 6 and target_lvl >= 7 and (num_increases - increases_applied) >= 2:
                skill_ranks[name] = 6
                increases_applied += 2
            # Otherwise, can we restore Expert? (Requires level 2+ and 1 increase)
            elif prev_val >= 4 and target_lvl >= 2 and (num_increases - increases_applied) >= 1:
                skill_ranks[name] = 4
                increases_applied += 1

        remaining = num_increases - increases_applied
        while remaining > 0:
            eligible_expert = [s for s in trained_skills if skill_ranks[s] == 2 and target_lvl >= 2]
            if eligible_expert:
                pick = eligible_expert[0]
                skill_ranks[pick] = 4
                remaining -= 1
                continue
            eligible_master = [s for s in trained_skills if skill_ranks[s] == 4 and target_lvl >= 7]
            if eligible_master:
                pick = eligible_master[0]
                skill_ranks[pick] = 6
                remaining -= 1
                continue
            break
    else:
        remaining = num_increases
        while remaining > 0:
            eligible = [s for s in trained_skills if skill_ranks[s] == 2 and target_lvl >= 2]
            if not eligible:
                break
            pick = random.choice(eligible)
            skill_ranks[pick] = 4
            remaining -= 1

    # 5. Build SkillEntry objects
    result_skills: List[SkillEntry] = []
    for sk_name in ALL_PF2E_SKILLS:
        rank_val = skill_ranks.get(sk_name, 0)
        attr_key = SKILL_KEY_ABILITY.get(sk_name, "dex")
        mod_val = norm_mods.get(attr_key, 0)

        if rank_val > 0:
            prof_bonus = rank_val + target_lvl
        elif has_untrained_improvisation:
            # Remaster: add level at 7+, half level (rounded down) below 7
            prof_bonus = target_lvl if target_lvl >= 7 else (target_lvl // 2)
        else:
            prof_bonus = 0

        total_mod = prof_bonus + mod_val

        result_skills.append(
            SkillEntry(
                name=sk_name,
                rank=rank_val,
                rank_letter=RANK_LETTER_MAP.get(rank_val, "U"),
                modifier=total_mod,
                attribute=attr_key.upper()
            )
        )

    # 6. Add Background Lore SkillEntry
    lore_rank = existing_map.get(chosen_lore, 2)
    if lore_rank > 0:
        lore_prof = lore_rank + target_lvl
    elif has_untrained_improvisation:
        lore_prof = target_lvl if target_lvl >= 7 else (target_lvl // 2)
    else:
        lore_prof = 0
    lore_total = lore_prof + norm_mods.get("int", 0)

    result_skills.append(
        SkillEntry(
            name=chosen_lore,
            rank=lore_rank,
            rank_letter=RANK_LETTER_MAP.get(lore_rank, "T" if lore_rank > 0 else "U"),
            modifier=lore_total,
            attribute="INT"
        )
    )

    # 7. Add Feat-Granted Lore (e.g. Additional Lore)
    for f in all_feats:
        f_name = f.name if hasattr(f, "name") else (f.get("name") if isinstance(f, dict) else "")
        if "additional lore" in f_name.lower() and "(" in f_name and ")" in f_name:
            feat_lore_name = f_name.split("(", 1)[1].rstrip(")").strip()
            if not feat_lore_name.lower().endswith("lore"):
                feat_lore_name = f"{feat_lore_name} Lore"

            # Prevent duplicate if already added
            if any(s.name.lower() == feat_lore_name.lower() for s in result_skills):
                continue

            # Additional Lore auto-scaling: Trained (1-2), Expert (3-6), Master (7-14), Legendary (15+)
            if target_lvl >= 15:
                al_rank = 8
            elif target_lvl >= 7:
                al_rank = 6
            elif target_lvl >= 3:
                al_rank = 4
            else:
                al_rank = 2

            al_prof = al_rank + target_lvl
            al_total = al_prof + norm_mods.get("int", 0)

            result_skills.append(
                SkillEntry(
                    name=feat_lore_name,
                    rank=al_rank,
                    rank_letter=RANK_LETTER_MAP.get(al_rank, "T"),
                    modifier=al_total,
                    attribute="INT"
                )
            )

    return result_skills
