from typing import Dict, Any, List, Tuple, Set

# Proficiency rank values: 0=U, 1=T, 2=E, 3=M, 4=L
CLASS_SAVE_PROGRESSION: Dict[str, Dict[str, Dict[int, int]]] = {
    "alchemist":    {"fortitude": {1: 2, 11: 3}, "reflex": {1: 2, 15: 3}, "will": {1: 1, 9: 2}, "perception": {1: 1, 9: 2}},
    "animist":      {"fortitude": {1: 1, 9: 2}, "reflex": {1: 1, 11: 2}, "will": {1: 2, 7: 3, 17: 4}, "perception": {1: 1, 5: 2}},
    "barbarian":    {"fortitude": {1: 2, 5: 3, 13: 4}, "reflex": {1: 1, 9: 2}, "will": {1: 1, 7: 2, 15: 3}, "perception": {1: 1, 7: 2, 17: 3}},
    "bard":         {"fortitude": {1: 1, 9: 2}, "reflex": {1: 1, 5: 2}, "will": {1: 2, 9: 3, 17: 4}, "perception": {1: 2, 11: 3}},
    "champion":     {"fortitude": {1: 2, 7: 3, 15: 4}, "reflex": {1: 1, 9: 2}, "will": {1: 2, 11: 3, 19: 4}, "perception": {1: 1, 11: 2}},
    "cleric":       {"fortitude": {1: 1, 9: 2}, "reflex": {1: 1, 11: 2}, "will": {1: 2, 9: 3, 19: 4}, "perception": {1: 1, 5: 2}},
    "commander":    {"fortitude": {1: 2, 9: 3}, "reflex": {1: 1, 11: 2}, "will": {1: 2, 7: 3, 15: 4}, "perception": {1: 2, 9: 3}},
    "druid":        {"fortitude": {1: 2, 11: 3}, "reflex": {1: 1, 5: 2}, "will": {1: 2, 9: 3}, "perception": {1: 1, 5: 2}},
    "exemplar":     {"fortitude": {1: 2, 7: 3, 15: 4}, "reflex": {1: 2, 11: 3}, "will": {1: 1, 9: 2}, "perception": {1: 2, 11: 3}},
    "fighter":      {"fortitude": {1: 2, 9: 3, 17: 4}, "reflex": {1: 2, 9: 3}, "will": {1: 1, 3: 2, 15: 3}, "perception": {1: 2, 7: 3, 13: 4}},
    "guardian":     {"fortitude": {1: 2, 7: 3, 13: 4}, "reflex": {1: 1, 9: 2}, "will": {1: 2, 11: 3, 17: 4}, "perception": {1: 2, 11: 3}},
    "gunslinger":   {"fortitude": {1: 2, 9: 3}, "reflex": {1: 2, 7: 3, 15: 4}, "will": {1: 1, 3: 2, 11: 3}, "perception": {1: 2, 7: 3, 13: 4}},
    "inventor":     {"fortitude": {1: 2, 9: 3}, "reflex": {1: 1, 5: 2, 15: 3}, "will": {1: 2, 11: 3}, "perception": {1: 1, 7: 2, 13: 3}},
    "investigator": {"fortitude": {1: 1, 9: 2}, "reflex": {1: 2, 7: 3, 15: 4}, "will": {1: 2, 11: 3, 17: 4}, "perception": {1: 2, 7: 3, 13: 4}},
    "kineticist":   {"fortitude": {1: 2, 7: 3, 15: 4}, "reflex": {1: 2, 11: 3}, "will": {1: 1, 9: 2, 17: 3}, "perception": {1: 1, 7: 2, 13: 3}},
    "magus":        {"fortitude": {1: 2, 9: 3}, "reflex": {1: 1, 5: 2}, "will": {1: 2, 11: 3}, "perception": {1: 1, 9: 2}},
    "monk":         {"fortitude": {1: 2, 7: 3, 15: 4}, "reflex": {1: 2, 7: 3, 15: 4}, "will": {1: 2, 11: 3, 19: 4}, "perception": {1: 1, 5: 2}},
    "necromancer":  {"fortitude": {1: 1, 9: 2}, "reflex": {1: 1, 11: 2}, "will": {1: 2, 7: 3, 17: 4}, "perception": {1: 1, 7: 2}},
    "oracle":       {"fortitude": {1: 1, 9: 2}, "reflex": {1: 1, 13: 2}, "will": {1: 2, 7: 3, 17: 4}, "perception": {1: 1, 11: 2}},
    "psychic":      {"fortitude": {1: 1, 9: 2}, "reflex": {1: 1, 5: 2}, "will": {1: 2, 11: 3, 17: 4}, "perception": {1: 1, 11: 2}},
    "ranger":       {"fortitude": {1: 2, 9: 3}, "reflex": {1: 2, 7: 3, 15: 4}, "will": {1: 1, 3: 2, 11: 3}, "perception": {1: 2, 7: 3, 15: 4}},
    "rogue":        {"fortitude": {1: 1, 9: 2}, "reflex": {1: 2, 7: 3, 13: 4}, "will": {1: 2, 11: 3, 17: 4}, "perception": {1: 2, 7: 3, 13: 4}},
    "runesmith":    {"fortitude": {1: 2, 9: 3}, "reflex": {1: 1, 11: 2}, "will": {1: 2, 7: 3, 15: 4}, "perception": {1: 1, 7: 2}},
    "sorcerer":     {"fortitude": {1: 1, 5: 2}, "reflex": {1: 1, 9: 2}, "will": {1: 2, 9: 3, 17: 4}, "perception": {1: 1, 11: 2}},
    "summoner":     {"fortitude": {1: 2, 9: 3}, "reflex": {1: 1, 11: 2}, "will": {1: 2, 7: 3, 15: 4}, "perception": {1: 1, 9: 2}},
    "swashbuckler": {"fortitude": {1: 1, 9: 2}, "reflex": {1: 2, 7: 3, 13: 4}, "will": {1: 2, 11: 3, 17: 4}, "perception": {1: 2, 11: 3}},
    "thaumaturge":  {"fortitude": {1: 2, 9: 3}, "reflex": {1: 1, 5: 2}, "will": {1: 2, 7: 3, 15: 4}, "perception": {1: 2, 7: 3, 13: 4}},
    "witch":        {"fortitude": {1: 1, 9: 2}, "reflex": {1: 1, 5: 2}, "will": {1: 2, 9: 3, 17: 4}, "perception": {1: 1, 11: 2}},
    "wizard":       {"fortitude": {1: 1, 9: 2}, "reflex": {1: 1, 5: 2}, "will": {1: 2, 9: 3, 17: 4}, "perception": {1: 1, 11: 2}},
}

WEAPON_EXPERT_LEVELS: Dict[str, int] = {
    "fighter": 1, "gunslinger": 1,
    "barbarian": 5, "champion": 5, "commander": 5, "exemplar": 5, "guardian": 5,
    "inventor": 5, "investigator": 5, "magus": 5, "monk": 5, "ranger": 5,
    "rogue": 5, "runesmith": 5, "swashbuckler": 5, "thaumaturge": 5,
    "alchemist": 7,
    "animist": 11, "bard": 11, "cleric": 11, "druid": 11, "necromancer": 11,
    "oracle": 11, "psychic": 11, "sorcerer": 11, "summoner": 11, "witch": 11, "wizard": 11,
}

WEAPON_MASTER_LEVELS: Dict[str, int] = {
    "fighter": 5, "gunslinger": 5,
    "barbarian": 13, "champion": 13, "commander": 13, "exemplar": 13, "guardian": 13,
    "inventor": 13, "investigator": 13, "magus": 13, "monk": 13, "ranger": 13,
    "rogue": 13, "runesmith": 13, "swashbuckler": 13, "thaumaturge": 13,
    "alchemist": 15,
}

def get_class_saving_throws(
    class_name: str,
    base_fort: int,
    base_ref: int,
    base_will: int,
    base_perception: int,
    level: int,
) -> Tuple[int, int, int, int]:
    cls_lower = class_name.lower()
    prog = CLASS_SAVE_PROGRESSION.get(cls_lower, {})

    def resolve_stat(stat_name: str, base: int) -> int:
        stat_prog = prog.get(stat_name, {})
        current = base
        for lvl in sorted(stat_prog.keys()):
            if level >= lvl:
                current = max(current, stat_prog[lvl])
        return current

    return (
        resolve_stat("fortitude", base_fort),
        resolve_stat("reflex", base_ref),
        resolve_stat("will", base_will),
        resolve_stat("perception", base_perception),
    )

def get_weapon_prof_bonus_delta(class_name: str, level: int) -> int:
    # Returns +2 for Expert, +4 for Master, +6 for Legendary over Trained (+2)
    cls_lower = class_name.lower()
    if cls_lower in ("fighter", "gunslinger") and level >= 13:
        return 6  # Legendary
    if level >= WEAPON_MASTER_LEVELS.get(cls_lower, 99):
        return 4  # Master
    if level >= WEAPON_EXPERT_LEVELS.get(cls_lower, 99):
        return 2  # Expert
    return 0

def get_weapon_spec_bonus(class_name: str, level: int) -> int:
    cls_lower = class_name.lower()
    # Casters get Weapon Specialization at 13; martials at 7, Greater at 15 (13 for fighter/gunslinger)
    casters = {"animist", "bard", "cleric", "druid", "necromancer", "oracle", "psychic", "sorcerer", "summoner", "witch", "wizard"}
    if cls_lower in casters:
        return 2 if level >= 13 else 0
    if cls_lower in ("fighter", "gunslinger"):
        if level >= 13:
            return 6
        return 3 if level >= 7 else 0
    if level >= 15:
        return 4
    return 2 if level >= 7 else 0

def apply_remaster_level_boosts(base_mods: Dict[str, int], key_attr: str, target_level: int) -> Dict[str, int]:
    # PF2e Remaster: 4 boosts at levels 5, 10, 15, 20; attributes >= +4 require 2 boosts per +1
    mods = dict(base_mods)
    partials: Set[str] = set()
    priority = [key_attr, "con", "dex", "wis", "str", "int", "cha"]

    for milestone in (5, 10, 15, 20):
        if target_level >= milestone:
            chosen_this_tier: Set[str] = set()
            for attr in priority:
                if len(chosen_this_tier) >= 4:
                    break
                if attr in chosen_this_tier:
                    continue
                chosen_this_tier.add(attr)
                if mods[attr] < 4:
                    mods[attr] += 1
                else:
                    if attr in partials:
                        mods[attr] += 1
                        partials.remove(attr)
                    else:
                        partials.add(attr)
    return mods
