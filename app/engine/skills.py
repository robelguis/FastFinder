import re
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

ADDITIONAL_LORE_POOL = [
    "Underworld Lore", "Warfare Lore", "Engineering Lore", "Architecture Lore",
    "Academia Lore", "Hunting Lore", "Mercantile Lore", "Sailing Lore",
    "Scouting Lore", "Court Lore", "Herbalism Lore", "Labor Lore"
]

# Feats granting untyped/untrained level scaling to all untrained skills
UNTRAINED_SCALING_FEATS = {
    "untrained improvisation",
    "clever improviser"
}

# Feats granting auto-scaling Lore (Expert at 3, Master at 7, Legendary at 15)
AUTO_SCALING_LORE_FEATS = {
    "additional lore",
    "gnome obsession",
    "experienced professional"
}

# Archetype/Class feats that auto-scale a core skill to Expert (lv 3) / Master (lv 7) / Legendary (lv 15)
AUTO_SCALING_SKILL_FEATS: Dict[str, str] = {
    "acrobat dedication": "Acrobatics",
    "medic dedication": "Medicine",
    "wrestler dedication": "Athletics",
}

def resolve_character_skills(
    class_name: str,
    background_data: Dict[str, Any],
    attribute_mods: Dict[str, int],
    level: int = 1,
    feats: List[Any] = None
) -> List[SkillEntry]:
    cls_key = class_name.lower()

    # 1. Base trained skills from class
    base_trained = list(CLASS_TRAINED_SKILLS.get(cls_key, ["Athletics"]))

    # 2. Background skill & Lore
    raw_bg_skills = background_data.get("trained_skills", []) or background_data.get("skills", [])
    for sk in raw_bg_skills:
        sk_title = sk.strip().title()
        if sk_title in CORE_SKILLS and sk_title not in base_trained:
            base_trained.append(sk_title)

    # Resolve Lore name
    raw_lore = background_data.get("trained_lore") or background_data.get("lore") or ""
    desc = background_data.get("description", "")
    if not raw_lore:
        lore_matches = re.findall(r"([A-Z][a-zA-Z]+ Lore)", desc)
        if lore_matches:
            raw_lore = random.choice(lore_matches)
        else:
            bg_name = background_data.get("name", "").strip()
            raw_lore = f"{bg_name} Lore" if bg_name else "Settlement Lore"

    lore_name = raw_lore if raw_lore.endswith("Lore") else f"{raw_lore} Lore"

    # 3. Extra skill picks (2 + INT mod, min 1; Rogue/Investigator get 7)
    int_mod = attribute_mods.get("int", 0)
    extra_count = 7 + int_mod if cls_key in ["rogue", "investigator"] else 2 + int_mod
    extra_count = max(1, extra_count)

    remaining_pool = [s for s in CORE_SKILLS.keys() if s not in base_trained]
    random.shuffle(remaining_pool)
    trained_skills_set = set(base_trained + remaining_pool[:extra_count])

    # 4. Standard Level 3+ Skill Increase: promote 1 trained skill to Expert (rank 4)
    expert_skills_set = set()
    if level >= 3 and trained_skills_set:
        promoted = random.choice(list(trained_skills_set))
        expert_skills_set.add(promoted)

    # 5. Build base skill entries
    skills_dict: Dict[str, SkillEntry] = {}
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

        skills_dict[skill_name] = SkillEntry(
            name=skill_name,
            attribute=attr.upper(),
            rank=rank,
            rank_letter=rank_letter,
            modifier=modifier
        )

    # Normalize feat names
    feat_names = set()
    for f in (feats or []):
        fn = f.name.lower() if hasattr(f, "name") else str(f).lower()
        feat_names.add(fn)

    # 6. Apply Auto-Scaling Dedicated Feats (e.g., Acrobat Dedication -> Acrobatics)
    for feat_key, skill_target in AUTO_SCALING_SKILL_FEATS.items():
        if any(feat_key in fn for fn in feat_names):
            if skill_target in skills_dict:
                sk = skills_dict[skill_target]
                # Auto-scales: Lv 7+ -> Master (6), Lv 3+ -> Expert (4), else Trained (2)
                target_rank = 6 if level >= 7 else (4 if level >= 3 else 2)
                if sk.rank < target_rank:
                    sk.rank = target_rank
                    sk.rank_letter = {2: "T", 4: "E", 6: "M", 8: "L"}.get(target_rank, "T")
                    sk.modifier = sk.rank + level + attribute_mods.get(sk.attribute.lower(), 0)

    # 7. Apply Untrained Improvisation / Clever Improviser
    if any(any(uf in fn for uf in UNTRAINED_SCALING_FEATS) for fn in feat_names):
        improv_bonus = level if level >= 7 else (level // 2)
        for sk in skills_dict.values():
            if sk.rank == 0:
                sk.modifier += improv_bonus

    skills_list = list(skills_dict.values())

    # 8. Append Background Lore (trained, scales with INT)
    lore_attr_val = attribute_mods.get("int", 0)
    skills_list.append(SkillEntry(
        name=lore_name,
        attribute="INT",
        rank=2,
        rank_letter="T",
        modifier=2 + level + lore_attr_val
    ))

    # 9. Append Auto-Scaling Lore Feats (Additional Lore, Gnome Obsession, etc.)
    used_lores = {lore_name.lower()}
    for af in AUTO_SCALING_LORE_FEATS:
        if any(af in fn for fn in feat_names):
            available = [l for l in ADDITIONAL_LORE_POOL if l.lower() not in used_lores]
            chosen_lore = random.choice(available) if available else "Academia Lore"
            used_lores.add(chosen_lore.lower())

            # Auto-scales: 15+ -> L (8), 7+ -> M (6), 3+ -> E (4), else T (2)
            if level >= 15:
                al_rank, al_letter = 8, "L"
            elif level >= 7:
                al_rank, al_letter = 6, "M"
            elif level >= 3:
                al_rank, al_letter = 4, "E"
            else:
                al_rank, al_letter = 2, "T"

            skills_list.append(SkillEntry(
                name=chosen_lore,
                attribute="INT",
                rank=al_rank,
                rank_letter=al_letter,
                modifier=al_rank + level + lore_attr_val
            ))

    return skills_list
