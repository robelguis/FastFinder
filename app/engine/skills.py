import json
from pathlib import Path
import re
from typing import List, Dict, Any, Optional, Set
import random
from app.engine.models import SkillEntry

_FEAT_PREREQ_CACHE: Optional[Dict[str, List[str]]] = None


def _get_feat_prereq_lookup() -> Dict[str, List[str]]:
    global _FEAT_PREREQ_CACHE
    if _FEAT_PREREQ_CACHE is not None:
        return _FEAT_PREREQ_CACHE
    lookup: Dict[str, List[str]] = {}
    feats_file = Path(__file__).resolve().parent.parent.parent / "data" / "feats.json"
    if feats_file.exists():
        try:
            raw = json.loads(feats_file.read_text(encoding="utf-8"))
            items = raw if isinstance(raw, list) else raw.get("feats", [])
            for f in items:
                if isinstance(f, dict) and f.get("name"):
                    prereqs = f.get("prerequisites") or []
                    if prereqs:
                        lookup[f["name"].strip().lower()] = [str(p) for p in prereqs]
        except Exception:
            pass
    _FEAT_PREREQ_CACHE = lookup
    return _FEAT_PREREQ_CACHE

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

    # Normalize string slug / pack JSON background into dict with description
    if isinstance(bg, str):
        slug = bg.strip().lower().replace(" ", "_")
        bg_json_path = Path("source_data/packs/pf2e/backgrounds") / f"{slug}.json"
        if bg_json_path.exists():
            raw_bg = json.loads(bg_json_path.read_text(encoding="utf-8"))
            desc_val = raw_bg.get("system", {}).get("description", {}).get("value", "")
            bg = {"name": raw_bg.get("name") or bg, "description": re.sub(r"<[^>]+>", " ", desc_val)}
        else:
            bg = {"name": bg, "description": ""}
    elif isinstance(bg, dict) and not bg.get("description") and isinstance(bg.get("system"), dict):
        desc_val = bg["system"].get("description", {}).get("value", "")
        if desc_val:
            bg = {**bg, "description": re.sub(r"<[^>]+>", " ", desc_val)}

    # 1. Extract and preserve Lore
    chosen_lore = existing_lore
    if not chosen_lore:
        lore_opts = bg.get("lore_options", [])
        if not lore_opts and bg.get("trained_lore"):
            t_lore = bg.get("trained_lore")
            if isinstance(t_lore, list):
                lore_opts = t_lore
            elif isinstance(t_lore, str) and t_lore.strip():
                lore_opts = [t_lore.strip()]

        if not lore_opts and bg.get("description"):
            plain_desc = re.sub(r"<[^>]+>", " ", str(bg.get("description", "")))
            plain_desc = re.sub(r"\s+", " ", plain_desc).strip()
            matches = re.findall(r"([A-Z][A-Za-z'\-]*(?:\s+(?:of|the|and|[A-Z][A-Za-z'\-]*))*\s+Lore)", plain_desc)
            blocked_bg_lores = {
                "lore",
                "additional lore",
                "your lore",
                "any lore",
                "that lore",
                "chosen lore",
                f"{str(bg.get('name', '')).lower()} lore",
            }
            filtered = []
            for m in matches:
                cleaned_m = re.sub(r"^(?:the|a|an|your|any)\s+", "", m.strip(), flags=re.IGNORECASE).strip()
                if cleaned_m and cleaned_m.lower() not in blocked_bg_lores and "additional" not in cleaned_m.lower():
                    filtered.append(cleaned_m)
            if filtered:
                lore_opts = filtered

        if lore_opts:
            chosen_lore = random.choice(lore_opts)
        else:
            chosen_lore = f"{bg.get('name', 'Settler')} Lore"

    if str(chosen_lore or "").strip().lower() in {"", "lore", "additional lore", "your lore", "any lore"}:
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
    CLASS_MANDATORY_SKILLS = {
        "alchemist": ["Crafting"],
        "animist": ["Religion"],
        "barbarian": ["Athletics"],
        "bard": ["Occultism", "Performance"],
        "champion": ["Religion"],
        "cleric": ["Religion"],
        "druid": ["Nature"],
        "exemplar": ["Religion"],
        "inventor": ["Crafting"],
        "investigator": ["Society"],
        "kineticist": ["Nature"],
        "magus": ["Arcana"],
        "oracle": ["Religion"],
        "psychic": ["Occultism"],
        "ranger": ["Nature", "Survival"],
        "rogue": ["Stealth"],
        "swashbuckler": ["Acrobatics"],
        "thaumaturge": ["Arcana", "Nature", "Occultism", "Religion"],
        "witch": ["Occultism"],
        "wizard": ["Arcana"],
    }
    class_req_skills = set(CLASS_MANDATORY_SKILLS.get(cls_name.lower(), []))
    arch_low = (planned_archetype or "").strip().lower()
    if "living monolith" in arch_low:
        class_req_skills.add("Crafting")
    elif "medic" in arch_low:
        class_req_skills.add("Medicine")
    elif "beastmaster" in arch_low or "mammoth" in arch_low:
        class_req_skills.add("Nature")
    elif "sentinel" in arch_low or "bastion" in arch_low or "mauler" in arch_low or "cavalier" in arch_low:
        class_req_skills.add("Athletics")
    elif "assassin" in arch_low or "shadowdancer" in arch_low:
        class_req_skills.add("Stealth")
    elif "marshal" in arch_low:
        class_req_skills.update({"Diplomacy"})

    req_skills_dict = kwargs.get("requested_skills") or {}
    for rk_name in req_skills_dict.keys():
        for std_s in ALL_PF2E_SKILLS:
            if std_s.lower() == str(rk_name).strip().lower():
                class_req_skills.add(std_s)
                break

    feat_names_lower = {
        (f.name if hasattr(f, "name") else (f.get("name") if isinstance(f, dict) else "")).lower()
        for f in all_feats
    }
    # Ensure background feats' required skills from feats.json prerequisites are trained
    prereq_lookup = _get_feat_prereq_lookup()
    for _bf in all_feats:
        _bcat = (getattr(_bf, "category", None) or (_bf.get("category") if isinstance(_bf, dict) else "") or "").lower()
        _bname = (getattr(_bf, "name", None) or (_bf.get("name") if isinstance(_bf, dict) else "") or "").lower()
        if "background" in _bcat:
            _base_bname = _bname.split("(", 1)[0].strip()
            for _pr in prereq_lookup.get(_bname) or prereq_lookup.get(_base_bname) or []:
                _pm = re.search(r"\btrained in ([^.\n;]+)", _pr.lower())
                if _pm:
                    for _opt in re.split(r",|\bor\b", _pm.group(1)):
                        _oc = _opt.strip().title()
                        if _oc in ALL_PF2E_SKILLS:
                            class_req_skills.add(_oc)
                            break
            if "natural medicine" in _bname:
                class_req_skills.add("Nature")
            elif "assurance" in _bname and "(" in _bname and ")" in _bname:
                _ak = _bname.split("(", 1)[1].rsplit(")", 1)[0].strip().title()
                if _ak in ALL_PF2E_SKILLS:
                    class_req_skills.add(_ak)

    trained_skills: Set[str] = set(class_req_skills)
    if existing_map:
        for name, rank_val in existing_map.items():
            if name in ALL_PF2E_SKILLS and rank_val >= 2:
                trained_skills.add(name)
    else:
        bg_skills = list(bg.get("skills") or [])
        if not bg_skills and bg.get("trained_skills"):
            bg_skills.extend(bg.get("trained_skills"))

        # Fallback: scan description for standard PF2e skill grants (e.g. "trained in the Arcana skill" or "trained in Athletics")
        desc = bg.get("description", "")
        if desc:
            for s in ALL_PF2E_SKILLS:
                if re.search(rf"\b{s}\s+skill\b", desc, re.IGNORECASE) or re.search(rf"\btrained\s+in\s+(?:the\s+)?{s}\b", desc, re.IGNORECASE):
                    bg_skills.append(s)

        mandatory = set()
        for bs in bg_skills:
            for s in ALL_PF2E_SKILLS:
                if s.lower() == bs.lower():
                    mandatory.add(s)

        # Total standard (non-Lore) skills granted by each class at Level 1 BEFORE +1 background and +INT
        CLASS_BASE_SKILL_COUNTS = {
            "rogue": 9,
            "thaumaturge": 7,
            "bard": 6,
            "investigator": 6,
            "ranger": 6,
            "swashbuckler": 6,
            "oracle": 5,
            "alchemist": 4,
            "barbarian": 4,
            "champion": 4,
            "cleric": 4,
            "commander": 4,
            "druid": 4,
            "exemplar": 4,
            "fighter": 4,
            "guardian": 4,
            "gunslinger": 4,
            "inventor": 4,
            "kineticist": 4,
            "monk": 4,
            "psychic": 4,
            "runesmith": 4,
            "sorcerer": 4,
            "summoner": 4,
            "witch": 4,
            "animist": 3,
            "magus": 3,
            "necromancer": 3,
            "wizard": 3,
        }
        base_count = (bg.get("class_skill_count") if isinstance(bg, dict) else None) or CLASS_BASE_SKILL_COUNTS.get(cls_name.lower(), 4)
        mandatory = mandatory.union(class_req_skills)
        total_picks = max(len(mandatory), base_count + 1 + int_mod)
        available_pool = [s for s in ALL_PF2E_SKILLS if s not in mandatory]
        random.shuffle(available_pool)
        if norm_mods.get("str", 0) >= 3 and "Athletics" in available_pool:
            available_pool.remove("Athletics")
            available_pool.insert(0, "Athletics")
        needed = max(0, total_picks - len(mandatory))
        trained_skills = mandatory.union(set(available_pool[:needed]))

    # Apply Multiclass Dedication skill trainings (Druid Dedication + Order skill, etc.)
    def _grant_trained_or_substitute(preferred_skill: str):
        if preferred_skill in ALL_PF2E_SKILLS and preferred_skill not in trained_skills:
            trained_skills.add(preferred_skill)
        else:
            untrained_pool = [s for s in ALL_PF2E_SKILLS if s not in trained_skills]
            if untrained_pool:
                trained_skills.add(random.choice(untrained_pool))

    for f in all_feats:
        fn = (f.name if hasattr(f, "name") else (f.get("name") if isinstance(f, dict) else "")).lower()
        fdesc = (f.description if hasattr(f, "description") else (f.get("description") if isinstance(f, dict) else "")).lower()
        if "druid dedication" in fn:
            _grant_trained_or_substitute("Nature")
            order_skill = "Survival"
            if "animal order" in fdesc:
                order_skill = "Athletics"
            elif "leaf order" in fdesc or "cultivation" in fdesc or "spore" in fdesc:
                order_skill = "Diplomacy"
            elif "storm order" in fdesc or "flame order" in fdesc:
                order_skill = "Acrobatics"
            elif "wild order" in fdesc or "untamed order" in fdesc:
                order_skill = "Intimidation"
            elif "stone order" in fdesc:
                order_skill = "Crafting"
            elif "wave order" in fdesc:
                order_skill = "Medicine"
            _grant_trained_or_substitute(order_skill)
        elif "bard dedication" in fn:
            _grant_trained_or_substitute("Occultism")
            _grant_trained_or_substitute("Performance")
        elif "cleric dedication" in fn or "oracle dedication" in fn or "champion dedication" in fn:
            _grant_trained_or_substitute("Religion")
        elif "wizard dedication" in fn or "magus dedication" in fn:
            _grant_trained_or_substitute("Arcana")
        elif "witch dedication" in fn or "psychic dedication" in fn:
            _grant_trained_or_substitute("Occultism")
        elif "alchemist dedication" in fn or "inventor dedication" in fn:
            _grant_trained_or_substitute("Crafting")
        elif "investigator dedication" in fn:
            _grant_trained_or_substitute("Society")
        elif "kineticist dedication" in fn:
            _grant_trained_or_substitute("Nature")
        elif "ranger dedication" in fn:
            _grant_trained_or_substitute("Survival")
        elif "rogue dedication" in fn:
            _grant_trained_or_substitute("Stealth")
        elif "barbarian dedication" in fn or "monk dedication" in fn or "fighter dedication" in fn or "swashbuckler dedication" in fn:
            _grant_trained_or_substitute("Athletics")

    # Apply feat-granted skill trainings (Harrower Dedication, Surki Lore)
    if any("harrower dedication" in fn for fn in feat_names_lower):
        if "Occultism" not in trained_skills:
            trained_skills.add("Occultism")
        else:
            untrained = [s for s in ALL_PF2E_SKILLS if s not in trained_skills]
            if untrained:
                trained_skills.add(untrained[0])

    if any("surki lore" in fn for fn in feat_names_lower):
        trained_skills.add("Survival")
        trad_skill = "Religion" if cls_name.lower() in ("cleric", "oracle", "champion") else (
            "Nature" if cls_name.lower() in ("druid", "ranger") else (
                "Occultism" if cls_name.lower() in ("bard", "psychic", "witch") else "Arcana"
            )
        )
        if trad_skill not in trained_skills:
            trained_skills.add(trad_skill)
        else:
            untrained = [s for s in ALL_PF2E_SKILLS if s not in trained_skills]
            if untrained:
                trained_skills.add(untrained[0])

    # Generic feat-granted skill trainings (e.g., Minotaur Lore -> Society & Stealth)
    _skill_lookup = {s.lower(): s for s in ALL_PF2E_SKILLS}
    feat_expert_skills = set()
    for _feat in all_feats:
        _fn_low = (getattr(_feat, "name", None) or (_feat.get("name") if isinstance(_feat, dict) else "") or "").lower()
        if "hobnobber" in _fn_low:
            trained_skills.add("Diplomacy")
        if "natural medicine" in _fn_low:
            trained_skills.add("Nature")
        if "yaoguai historian" in _fn_low:
            trained_skills.add("Occultism")
        _f_desc = (getattr(_feat, "description", None) or (_feat.get("description") if isinstance(_feat, dict) else "") or "")
        if not _f_desc:
            continue
        for _m_tr in re.finditer(
            r"(?:you become trained in|you gain the trained proficiency rank in)\s+([a-z]+)(?:\s+and\s+([a-z]+))?",
            _f_desc,
            flags=re.IGNORECASE,
        ):
            for _grp in (_m_tr.group(1), _m_tr.group(2)):
                if _grp and _grp.lower() in _skill_lookup:
                    _grant_trained_or_substitute(_skill_lookup[_grp.lower()])
        for _m_ex in re.finditer(
            r"you become an expert in\s+([a-z]+)(?:\s+and\s+([a-z]+))?",
            _f_desc,
            flags=re.IGNORECASE,
        ):
            for _grp in (_m_ex.group(1), _m_ex.group(2)):
                if _grp and _grp.lower() in _skill_lookup:
                    _sk_ex_name = _skill_lookup[_grp.lower()]
                    trained_skills.add(_sk_ex_name)
                    feat_expert_skills.add(_sk_ex_name)

    # 4. Calculate skill ranks and apply increases
    num_increases = get_skill_increases_count(cls_name, target_lvl)
    skill_ranks: Dict[str, int] = {
        s: (4 if s in feat_expert_skills else (2 if s in trained_skills else 0))
        for s in ALL_PF2E_SKILLS
    }

    if existing_map:
        # Restore existing increases from highest rank downward so Legendary/Master skills are never demoted
        boosted_names = sorted(
            [
                name for name in trained_skills
                if existing_map.get(name, 2) > 2
                and not (cls_name.lower() == "inventor" and name == "Crafting")
            ],
            key=lambda n: (-existing_map.get(n, 2), 0 if n in class_req_skills else 1, n),
        )

        increases_applied = 0
        # Re-apply boosts to the exact same skills up to the new num_increases limit
        for name in boosted_names:
            if increases_applied >= num_increases:
                break
            prev_val = existing_map.get(name, 2)

            # Can we restore Legendary? (Requires level 15+ and 3 increases)
            if prev_val >= 8 and target_lvl >= 15 and (num_increases - increases_applied) >= 3:
                skill_ranks[name] = 8
                increases_applied += 3
            # Can we restore Master? (Requires level 7+ and 2 increases)
            elif prev_val >= 6 and target_lvl >= 7 and (num_increases - increases_applied) >= 2:
                skill_ranks[name] = 6
                increases_applied += 2
            # Otherwise, can we restore Expert? (Requires level 2+ and 1 increase)
            elif prev_val >= 4 and target_lvl >= 2 and (num_increases - increases_applied) >= 1:
                skill_ranks[name] = 4
                increases_applied += 1

        def _inc_sort_key(sk_n: str) -> tuple:
            return (0 if sk_n in class_req_skills else 1, -norm_mods.get(SKILL_KEY_ABILITY.get(sk_n, "dex"), 0), sk_n)

        max_leg_core = 0 if target_lvl < 15 else (3 if cls_name.lower() == "inventor" else 4)
        remaining = num_increases - increases_applied
        while remaining > 0:
            cur_leg_core = sum(
                1 for s in ALL_PF2E_SKILLS
                if skill_ranks[s] >= 8 and not (cls_name.lower() == "inventor" and s == "Crafting")
            )
            if target_lvl >= 15 and cur_leg_core < max_leg_core:
                eligible_legendary = sorted(
                    [s for s in trained_skills if skill_ranks[s] == 6 and not (cls_name.lower() == "inventor" and s == "Crafting")],
                    key=_inc_sort_key,
                )
                if eligible_legendary:
                    skill_ranks[eligible_legendary[0]] = 8
                    remaining -= 1
                    continue
            eligible_master = sorted(
                [s for s in trained_skills if skill_ranks[s] == 4 and target_lvl >= 7],
                key=_inc_sort_key,
            )
            if eligible_master:
                skill_ranks[eligible_master[0]] = 6
                remaining -= 1
                continue
            eligible_expert = sorted(
                [s for s in trained_skills if skill_ranks[s] == 2 and target_lvl >= 2],
                key=_inc_sort_key,
            )
            if eligible_expert:
                skill_ranks[eligible_expert[0]] = 4
                remaining -= 1
                continue
            break
    else:
        # Fresh generation: build realistic PF2e vertical specialization (Legendary -> Master -> Expert)
        remaining = num_increases
        pool = list(trained_skills)
        random.shuffle(pool)
        # Prioritize class mandatory skills first
        pool.sort(key=lambda s: 0 if s in class_req_skills else 1)

        # Promote up to 3 core skills to Legendary (if level >= 15) / Master (if level >= 7)
        for sk in pool:
            if remaining <= 0:
                break
            if target_lvl >= 15 and remaining >= 3 and skill_ranks[sk] == 2:
                skill_ranks[sk] = 8
                remaining -= 3
            elif target_lvl >= 7 and remaining >= 2 and skill_ranks[sk] == 2:
                skill_ranks[sk] = 6
                remaining -= 2

        # Spend any remaining increases on Master (7+) or Expert (2+)
        while remaining > 0:
            eligible_master = [s for s in pool if skill_ranks[s] == 4 and target_lvl >= 7]
            if eligible_master:
                skill_ranks[eligible_master[0]] = 6
                remaining -= 1
                continue
            eligible_expert = [s for s in pool if skill_ranks[s] == 2 and target_lvl >= 2]
            if eligible_expert:
                skill_ranks[eligible_expert[0]] = 4
                remaining -= 1
                continue
            break

    # Class auto-scaling skills (Inventor Crafting: Expert at 3, Master at 7, Legendary at 15)
    if cls_name.lower() == "inventor":
        inv_craft = 8 if target_lvl >= 15 else (6 if target_lvl >= 7 else (4 if target_lvl >= 3 else 2))
        skill_ranks["Crafting"] = max(skill_ranks.get("Crafting", 0), inv_craft)

    # Ancestry & Archetype feat skill training & rank minimums
    if any("tanuki lore" in fn for fn in feat_names_lower):
        for t_sk in ("Deception", "Performance"):
            if skill_ranks.get(t_sk, 0) < 2:
                skill_ranks[t_sk] = 2
                trained_skills.add(t_sk)
            else:
                extra_untrained = [s for s in ALL_PF2E_SKILLS if skill_ranks.get(s, 0) == 0]
                if extra_untrained:
                    skill_ranks[extra_untrained[0]] = 2
                    trained_skills.add(extra_untrained[0])

    if any("provocator dedication" in fn for fn in feat_names_lower):
        skill_ranks["Performance"] = max(skill_ranks.get("Performance", 0), 4)
        trained_skills.add("Performance")
        if skill_ranks.get("Athletics", 0) >= skill_ranks.get("Acrobatics", 0):
            skill_ranks["Athletics"] = max(skill_ranks.get("Athletics", 0), 4)
            trained_skills.add("Athletics")
        else:
            skill_ranks["Acrobatics"] = max(skill_ranks.get("Acrobatics", 0), 4)
            trained_skills.add("Acrobatics")

    if any("knight vigilant dedication" in fn for fn in feat_names_lower):
        skill_ranks["Religion"] = max(skill_ranks.get("Religion", 0), 4)

    # Enforce PF2e Legendary skill cap (0 before level 15; max 4 at level 15+)
    max_legendary = 0 if target_lvl < 15 else 4
    protected_legendary = {"Crafting"} if cls_name.lower() == "inventor" and target_lvl >= 15 else set()
    leg_skills = [sk for sk in ALL_PF2E_SKILLS if skill_ranks.get(sk, 0) >= 8]
    if len(leg_skills) > max_legendary:
        # Keep protected class-scaled skills and previously Legendary skills up to max_legendary
        ranked_leg = sorted(
            leg_skills,
            key=lambda s: (
                0 if s in protected_legendary else 1,
                0 if existing_map.get(s, 0) >= 8 else 1,
                -norm_mods.get(SKILL_KEY_ABILITY.get(s, "dex"), 0),
                s,
            ),
        )
        for demoted in ranked_leg[max_legendary:]:
            skill_ranks[demoted] = 6 if target_lvl >= 7 else (4 if target_lvl >= 2 else 2)

    # 5. Build SkillEntry objects
    result_skills: List[SkillEntry] = []
    for sk_name in ALL_PF2E_SKILLS:
        rank_val = skill_ranks.get(sk_name, 0)
        attr_key = SKILL_KEY_ABILITY.get(sk_name, "dex")
        mod_val = norm_mods.get(attr_key, 0)

        if rank_val > 0:
            prof_bonus = rank_val + target_lvl
        elif has_untrained_improvisation:
            # PF2e Remaster: add full character level to untrained checks at all levels
            prof_bonus = target_lvl
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
        lore_prof = target_lvl
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

    # 6a0. Add Enigma Bard Bardic Lore (INT-based)
    if cls_name.lower() == "bard" and any("enigma" in str(v).lower() for v in kwargs.values()):
        if not any(s.name.lower() == "bardic lore" for s in result_skills):
            bl_rank = 8 if (target_lvl >= 15 and skill_ranks.get("Occultism", 0) >= 8) else (4 if (target_lvl >= 7 and skill_ranks.get("Occultism", 0) >= 6) else 2)
            result_skills.append(SkillEntry(
                name="Bardic Lore",
                rank=bl_rank,
                rank_letter=RANK_LETTER_MAP.get(bl_rank, "T"),
                modifier=(bl_rank + target_lvl) + norm_mods.get("int", 0),
                attribute="INT",
            ))

    # 6a. Add Thaumaturge Esoteric Lore (CHA-based, scales automatically at 3/7/15)
    if cls_name.lower() == "thaumaturge" or any("thaumaturge dedication" in fn for fn in feat_names_lower):
        if not any(s.name.lower() == "esoteric lore" for s in result_skills):
            es_rank = 2
            if cls_name.lower() == "thaumaturge":
                es_rank = 8 if target_lvl >= 15 else (6 if target_lvl >= 7 else (4 if target_lvl >= 3 else 2))
            es_rank = max(es_rank, existing_map.get("Esoteric Lore", 2))
            result_skills.append(SkillEntry(
                name="Esoteric Lore",
                rank=es_rank,
                rank_letter=RANK_LETTER_MAP.get(es_rank, "T"),
                modifier=(es_rank + target_lvl) + norm_mods.get("cha", 0),
                attribute="CHA",
            ))

    # 6b. Add Archetype / Ancestry Feat-Granted Lore (Harrower Dedication, Surki Lore)
    if any("harrower dedication" in fn for fn in feat_names_lower):
        if not any(s.name.lower() == "fortune-telling lore" for s in result_skills):
            ft_rank = existing_map.get("Fortune-Telling Lore", 2)
            result_skills.append(SkillEntry(
                name="Fortune-Telling Lore",
                rank=ft_rank,
                rank_letter=RANK_LETTER_MAP.get(ft_rank, "T"),
                modifier=(ft_rank + target_lvl) + norm_mods.get("int", 0),
                attribute="INT",
            ))

    if any("tanuki lore" in fn for fn in feat_names_lower):
        if not any(s.name.lower() == "tanuki lore" for s in result_skills):
            tl_rank = 8 if target_lvl >= 15 else (6 if target_lvl >= 7 else (4 if target_lvl >= 3 else 2))
            result_skills.append(SkillEntry(
                name="Tanuki Lore",
                rank=tl_rank,
                rank_letter=RANK_LETTER_MAP.get(tl_rank, "T"),
                modifier=(tl_rank + target_lvl) + norm_mods.get("int", 0),
                attribute="INT",
            ))

    if any("surki lore" in fn for fn in feat_names_lower):
        if not any(s.name.lower() == "surki lore" for s in result_skills):
            sl_rank = 8 if target_lvl >= 15 else (6 if target_lvl >= 7 else (4 if target_lvl >= 3 else 2))
            result_skills.append(SkillEntry(
                name="Surki Lore",
                rank=sl_rank,
                rank_letter=RANK_LETTER_MAP.get(sl_rank, "T"),
                modifier=(sl_rank + target_lvl) + norm_mods.get("int", 0),
                attribute="INT",
            ))

    # 7. Add Feat-Granted Lore (e.g. Additional Lore)
    for f in all_feats:
        f_name = f.name if hasattr(f, "name") else (f.get("name") if isinstance(f, dict) else "")
        if "additional lore" in f_name.lower() and "(" in f_name and ")" in f_name:
            feat_lore_name = f_name.split("(", 1)[1].rstrip(")").strip()
            if not feat_lore_name.lower().endswith("lore"):
                feat_lore_name = f"{feat_lore_name} Lore"

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

            existing_idx = next((i for i, s in enumerate(result_skills) if s.name.lower() == feat_lore_name.lower()), None)
            if existing_idx is not None:
                cur_s = result_skills[existing_idx]
                if cur_s.rank < al_rank:
                    result_skills[existing_idx] = SkillEntry(
                        name=cur_s.name,
                        rank=al_rank,
                        rank_letter=RANK_LETTER_MAP.get(al_rank, "T"),
                        modifier=(al_rank + target_lvl) + norm_mods.get("int", 0),
                        attribute=cur_s.attribute or "INT",
                    )
                continue

            result_skills.append(
                SkillEntry(
                    name=feat_lore_name,
                    rank=al_rank,
                    rank_letter=RANK_LETTER_MAP.get(al_rank, "T"),
                    modifier=al_total,
                    attribute="INT"
                )
            )

    # Dynamically extract and award Lore granted by Dedications and Feats
    if feats:
        DEDICATION_LORE_MAP = {
            "living monolith dedication": ("Ancient Osirion Lore", True),
            "hellknight armiger": ("Hell Lore", False),
            "mammoth lord": ("Mammoth Lore", False),
            "riftwarden": ("Planes Lore", False),
            "yaoguai historian": ("Yaoguai Lore", False),
        }


        lore_regex = re.compile(
            r"(?:become trained in|trained in|gain the|gain)\s+(?:your choice of\s+[^;.]+and\s+)?([A-Za-z][A-Za-z\s\-]+?\s+Lore)(?=[.,;\n]|\s+or\b|$)",
            re.IGNORECASE,
        )
        for f_obj in all_feats:
            f_nm = f_obj.get("name", "") if isinstance(f_obj, dict) else getattr(f_obj, "name", "")
            if "additional lore" in f_nm.lower():
                continue
            f_desc = f_obj.get("description", "") if isinstance(f_obj, dict) else getattr(f_obj, "description", "")
            found_lores = list(lore_regex.findall(f_desc))
            ded_match = DEDICATION_LORE_MAP.get(f_nm.strip().lower())
            if ded_match and ded_match[0] not in found_lores:
                found_lores.append(ded_match[0])
            for raw_lore in found_lores:
                clean_lore = re.sub(r"\s+", " ", raw_lore.strip())
                if len(clean_lore.split()) > 5 or any(
                    bad in clean_lore.lower()
                    for bad in ["another", "associated", "appropriate", "choice", "additional", "skill increase", "apply", "chosen", "subcategory"]
                ):
                    continue
                if clean_lore.lower().startswith("in "):
                    clean_lore = clean_lore[3:].strip()
                clean_lore = clean_lore.title()
                if not clean_lore.endswith(" Lore"):
                    clean_lore = f"{clean_lore} Lore"

                existing_idx = next((i for i, s in enumerate(result_skills) if s.name.lower() == clean_lore.lower()), None)
                already_trained_desc = "or expert if you were already trained" in f_desc.lower()
                if existing_idx is not None:
                    cur_entry = result_skills[existing_idx]
                    upgraded_rank = max(cur_entry.rank, 4 if already_trained_desc else 2)
                    if upgraded_rank > cur_entry.rank:
                        result_skills[existing_idx] = SkillEntry(
                            name=cur_entry.name,
                            rank=upgraded_rank,
                            rank_letter=RANK_LETTER_MAP.get(upgraded_rank, "E"),
                            modifier=(upgraded_rank + target_lvl) + norm_mods.get("int", 0),
                            attribute=cur_entry.attribute or "INT",
                        )
                else:
                    target_rank = 2
                    lore_prof = target_rank + target_lvl
                    lore_mod = lore_prof + norm_mods.get("int", 0)
                    result_skills.append(
                        SkillEntry(
                            name=clean_lore,
                            rank=target_rank,
                            rank_letter=RANK_LETTER_MAP.get(target_rank, "T"),
                            modifier=lore_mod,
                            attribute="INT"
                        )
                    )
    return result_skills
