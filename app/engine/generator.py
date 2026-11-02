import json
import re
import random
from pathlib import Path
from typing import Dict, Any, List, Optional, Set
from app.engine.models import (
    CharacterSheet,
    AttributeModifiers,
    Defenses,
    Proficiency,
    FeatSummary,
    SubclassSummary,
)
from app.engine.names import generate_ancestry_name
from app.engine.equipment import resolve_equipment
from app.engine.skills import resolve_character_skills
from app.engine.spells import resolve_spellcasting
from app.engine.focus import resolve_focus_spells
from app.engine.companions import resolve_companion
from app.engine.eidolons import resolve_eidolon
from app.engine.familiars import resolve_familiar
from app.engine.constructs_undead import resolve_construct_companion, resolve_undead_companion
from app.engine.plants_familiars_summons import resolve_plant_companion, resolve_specific_familiar, resolve_summon_snapshot
from app.engine.subclasses import resolve_heritage, resolve_subclass
from app.engine.archetypes import pick_archetype

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"

ATTRIBUTES = ["str", "dex", "con", "int", "wis", "cha"]

RANK_MAP = {
    1: (2, "T"),
    2: (4, "E"),
    3: (6, "M"),
    4: (8, "L"),
}

GENERAL_FEATS_LVL3 = [
    {"id": "fleet", "name": "Fleet", "description": "Your Speed increases by 5 feet."},
    {"id": "toughness", "name": "Toughness", "description": "Your maximum HP increases by your level. The DC of recovery checks is 9 + dying value."},
    {"id": "diehard", "name": "Diehard", "description": "You die from the dying condition at dying 5, rather than dying 4."},
    {"id": "fast-recovery", "name": "Fast Recovery", "description": "You regain twice as many HP from resting and gain a +2 bonus against poison/disease."},
    {"id": "prescient-planner", "name": "Prescient Planner", "description": "You can pull standard equipment you predicted you'd need directly from your backpack."},
    {"id": "ancestral-paragon", "name": "Ancestral Paragon", "description": "You gain a 1st-level ancestry feat."},
    {"id": "untrained-improvisation", "name": "Untrained Improvisation", "description": "You add your level to untrained skill checks instead of 0."},
]

CLASS_FEATURES_LVL3 = {
    "fighter": {"name": "Bravery", "description": "Your proficiency rank in Will saves increases to expert. When you roll a success on a Will save against a fear effect, you get a critical success instead."},
    "rogue": {"name": "Deny Advantage", "description": "You aren't off-guard to hidden, undetected, or flanking creatures of your level or lower."},
    "barbarian": {"name": "Deny Advantage", "description": "You aren't off-guard to hidden, undetected, or flanking creatures of your level or lower."},
    "champion": {"name": "Divine Smite", "description": "Your champion reaction deals persistent damage equal to your Charisma modifier."},
    "ranger": {"name": "Iron Will", "description": "Your proficiency rank for Will saves increases to expert."},
    "monk": {"name": "Incredible Movement", "description": "You gain a +10-foot status bonus to your Speed whenever you're not wearing armor."},
}

def clean_pf2e_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"@UUID\[[^\]]+\]\{([^}]+)\}", r"\1", text)
    text = re.sub(r"@UUID\[(?:.*?\.)?([^\]\.]+?)\]", r"\1", text)
    text = re.sub(r"@Check\[[^\]]+\]\{([^}]+)\}", r"\1", text)
    text = re.sub(r"@Check\[[^\]]*type:([a-zA-Z]+)[^\]]*\]", r"\1 check", text)
    text = re.sub(r"@Damage\[[^\]]+\]\{([^}]+)\}", r"\1", text)
    text = re.sub(r"@Damage\[([^\]]+)\]", r"\1", text)
    text = re.sub(r"@[A-Za-z]+\[[^\]]+\]\{([^}]+)\}", r"\1", text)
    text = re.sub(r"@[A-Za-z]+\[[^\]]+\]", "", text)
    text = text.replace("[[", "").replace("]]", "")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    return text.strip()

def load_data(filename: str) -> Any:
    path = DATA_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Missing {filename}.")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

class PF2eGenerator:
    def __init__(self):
        self.ancestries = {a["name"].lower(): a for a in load_data("ancestries.json")}
        self.classes = {c["name"].lower(): c for c in load_data("classes.json")}
        self.backgrounds = {b["name"].lower(): b for b in load_data("backgrounds.json")}
        self.feats = load_data("feats.json")

    def _calc_prof(self, rank_val: int, level: int, attr_mod: int) -> Proficiency:
        prof_bonus, letter = RANK_MAP.get(rank_val, (2, "T"))
        return Proficiency(rank=prof_bonus, rank_letter=letter, modifier=prof_bonus + level + attr_mod)

    def generate(
        self,
        ancestry_name: Optional[str] = None,
        class_name: Optional[str] = None,
        char_name: Optional[str] = None,
        level: int = 1,
        use_dedication: bool = False
    ) -> CharacterSheet:
        level = max(1, min(4, level))

        # 1. Select Ancestry, Class, Background
        if ancestry_name and ancestry_name.lower() in self.ancestries:
            anc = self.ancestries[ancestry_name.lower()]
        else:
            anc = random.choice(list(self.ancestries.values()))

        if class_name and class_name.lower() in self.classes:
            cls = self.classes[class_name.lower()]
        else:
            cls = random.choice(list(self.classes.values()))

        bg = random.choice(list(self.backgrounds.values()))
        heritage_data = resolve_heritage(anc["name"])
        subclass_data = resolve_subclass(cls["name"])
        resolved_name = char_name.strip() if char_name and char_name.strip() else generate_ancestry_name(anc["name"])

        archetype_data = pick_archetype(cls["name"]) if use_dedication else None

        # 2. Track Attribute Boosts
        mods = {attr: 0 for attr in ATTRIBUTES}

        applied_anc_boosts: Set[str] = set()
        for boost_option in anc.get("boosts", []):
            valid_targets = [b.lower() for b in boost_option if b.lower() in ATTRIBUTES and b.lower() not in applied_anc_boosts]
            if not valid_targets:
                valid_targets = [a for a in ATTRIBUTES if a not in applied_anc_boosts]
            chosen_target = random.choice(valid_targets)
            mods[chosen_target] += 1
            applied_anc_boosts.add(chosen_target)

        for flaw_option in anc.get("flaws", []):
            for fl in flaw_option:
                fl = fl.lower()
                if fl in mods:
                    mods[fl] -= 1

        applied_bg_boosts: Set[str] = set()
        for boost_option in bg.get("boosts", []):
            valid_targets = [
                b.lower() for b in boost_option 
                if b.lower() in ATTRIBUTES 
                and b.lower() not in applied_bg_boosts 
                and mods[b.lower()] < 4
            ]
            if not valid_targets:
                valid_targets = [a for a in ATTRIBUTES if a not in applied_bg_boosts and mods[a] < 4]
            if valid_targets:
                chosen_target = random.choice(valid_targets)
                mods[chosen_target] += 1
                applied_bg_boosts.add(chosen_target)

        key_options = [k.lower() for k in cls.get("key_attributes", []) if k.lower() in ATTRIBUTES and mods[k.lower()] < 4]
        if not key_options:
            key_options = [k.lower() for k in cls.get("key_attributes", []) if k.lower() in ATTRIBUTES]
        key_attr = random.choice(key_options) if key_options else "str"
        if mods[key_attr] < 4:
            mods[key_attr] += 1

        free_boosts_applied: Set[str] = set()
        priority = [key_attr, "con", "dex", "wis", "str", "cha", "int"]
        for attr in priority:
            if len(free_boosts_applied) < 4 and attr not in free_boosts_applied and mods[attr] < 4:
                mods[attr] += 1
                free_boosts_applied.add(attr)

        for attr in ATTRIBUTES:
            if len(free_boosts_applied) < 4 and attr not in free_boosts_applied and mods[attr] < 4:
                mods[attr] += 1
                free_boosts_applied.add(attr)
            if mods[attr] > 4:
                mods[attr] = 4

        # 3. Defenses & Proficiencies
        fort_rank = cls.get("saving_throws", {}).get("fortitude", 1)
        ref_rank = cls.get("saving_throws", {}).get("reflex", 1)
        will_rank = cls.get("saving_throws", {}).get("will", 1)
        perception_rank = cls.get("perception", 1)

        if level >= 3 and cls["name"].lower() in ["fighter", "ranger"] and will_rank < 2:
            will_rank = 2

        fort_prof = self._calc_prof(fort_rank, level, mods["con"])
        ref_prof = self._calc_prof(ref_rank, level, mods["dex"])
        will_prof = self._calc_prof(will_rank, level, mods["wis"])
        perception_prof = self._calc_prof(perception_rank, level, mods["wis"])

        # 4. Equipment & HP
        equipment_loadout, calculated_ac, shield_bonus = resolve_equipment(
            cls["name"],
            str_mod=mods["str"],
            dex_mod=mods["dex"],
            level=level
        )

        con_mod = mods["con"]
        class_hp_per_lvl = cls.get("hp_per_level", 8)
        base_hp = anc.get("hp", 8) + ((class_hp_per_lvl + con_mod) * level)
        total_hp = max(1, base_hp)

        # 5. Feat Progression
        cls_name_lower = cls["name"].lower()
        chosen_feats: List[FeatSummary] = []

        # Heritage Feature with auto-resolved Versatile Heritage
        h_name = heritage_data["name"]
        h_desc = clean_pf2e_text(heritage_data["description"])
        if "Versatile" in h_name:
            v_choice = random.choice([
                {"name": "Fleet", "desc": "Your Speed increases by 5 feet."},
                {"name": "Toughness", "desc": "Your maximum HP increases by your level. Recovery check DC is 9 + dying value."},
                {"name": "Diehard", "desc": "You die from the dying condition at dying 5, rather than dying 4."},
                {"name": "Fast Recovery", "desc": "You regain twice as many HP from resting and gain a +2 bonus against poison/disease."}
            ])
            h_name = f"Versatile Heritage: {v_choice['name']}"
            h_desc = f"Selected General Feat: {v_choice['name']}. {v_choice['desc']}"

        chosen_feats.append(FeatSummary(
            id=f"heritage-{anc['name'].lower()}",
            name=h_name,
            category="Heritage",
            action_cost=None,
            traits=[anc['name'].lower()],
            description=h_desc
        ))

        # Subclass Feature
        if subclass_data:
            chosen_feats.append(FeatSummary(
                id=f"subclass-{cls['name'].lower()}",
                name=f"{subclass_data['title']}: {subclass_data['name']}",
                category="Class Feature",
                action_cost=None,
                traits=[cls['name'].lower()],
                description=clean_pf2e_text(subclass_data["description"])
            ))

        # Level 1 Class Feat
        lvl1_feats = [
            f for f in self.feats
            if f.get("category") == "class"
            and f.get("level") == 1
            and cls_name_lower in [t.lower() for t in f.get("traits", [])]
        ]
        if lvl1_feats:
            f1 = random.choice(lvl1_feats)
            chosen_feats.append(FeatSummary(
                id=f1["id"],
                name=f1["name"],
                category="Class (Level 1)",
                action_cost=f1.get("action_cost"),
                traits=f1.get("traits", []),
                description=clean_pf2e_text(f1.get("description", ""))
            ))

        # Level 2 Progression
        if level >= 2:
            if archetype_data:
                ded = archetype_data["level_2_dedication"]
                chosen_feats.append(FeatSummary(
                    id=ded["id"],
                    name=ded["name"],
                    category=f"Archetype ({archetype_data['name']})",
                    action_cost=ded.get("action_cost"),
                    traits=ded.get("traits", []),
                    description=clean_pf2e_text(ded["description"])
                ))
            else:
                lvl2_feats = [
                    f for f in self.feats
                    if f.get("category") == "class"
                    and f.get("level") == 2
                    and cls_name_lower in [t.lower() for t in f.get("traits", [])]
                ]
                if lvl2_feats:
                    f2 = random.choice(lvl2_feats)
                    chosen_feats.append(FeatSummary(
                        id=f2["id"],
                        name=f2["name"],
                        category="Class (Level 2)",
                        action_cost=f2.get("action_cost"),
                        traits=f2.get("traits", []),
                        description=clean_pf2e_text(f2.get("description", ""))
                    ))

            skill_feats_2 = [f for f in self.feats if f.get("category") == "skill" and f.get("level") in [1, 2]]
            if skill_feats_2:
                sf = random.choice(skill_feats_2)
                chosen_feats.append(FeatSummary(
                    id=sf["id"],
                    name=sf["name"],
                    category="Skill (Level 2)",
                    action_cost=sf.get("action_cost"),
                    traits=sf.get("traits", []),
                    description=clean_pf2e_text(sf.get("description", ""))
                ))

        # Level 3 Progression
        if level >= 3:
            gf = random.choice(GENERAL_FEATS_LVL3)
            if gf["id"] == "toughness":
                total_hp += level

            chosen_feats.append(FeatSummary(
                id=gf["id"],
                name=gf["name"],
                category="General (Level 3)",
                action_cost=None,
                traits=["general"],
                description=clean_pf2e_text(gf["description"])
            ))

            if cls_name_lower in CLASS_FEATURES_LVL3:
                cf = CLASS_FEATURES_LVL3[cls_name_lower]
                chosen_feats.append(FeatSummary(
                    id=f"class-feat-{cf['name'].lower().replace(' ', '-')}",
                    name=cf["name"],
                    category="Class Feature (Level 3)",
                    action_cost=None,
                    traits=[cls_name_lower],
                    description=clean_pf2e_text(cf["description"])
                ))

        # Level 4 Progression
        if level >= 4:
            if archetype_data:
                arch_lvl4 = random.choice(archetype_data["level_4_feats"])
                chosen_feats.append(FeatSummary(
                    id=arch_lvl4["id"],
                    name=arch_lvl4["name"],
                    category=f"Archetype ({archetype_data['name']})",
                    action_cost=arch_lvl4.get("action_cost"),
                    traits=arch_lvl4.get("traits", []),
                    description=clean_pf2e_text(arch_lvl4["description"])
                ))
            else:
                lvl4_feats = [
                    f for f in self.feats
                    if f.get("category") == "class"
                    and f.get("level") in [1, 2, 4]
                    and cls_name_lower in [t.lower() for t in f.get("traits", [])]
                    and f["name"] not in [cf.name for cf in chosen_feats]
                ]
                if lvl4_feats:
                    f4 = random.choice(lvl4_feats)
                    chosen_feats.append(FeatSummary(
                        id=f4["id"],
                        name=f4["name"],
                        category="Class (Level 4)",
                        action_cost=f4.get("action_cost"),
                        traits=f4.get("traits", []),
                        description=clean_pf2e_text(f4.get("description", ""))
                    ))

            skill_feats_4 = [
                f for f in self.feats 
                if f.get("category") == "skill" 
                and f.get("level") in [1, 2, 4]
                and f["name"] not in [cf.name for cf in chosen_feats]
            ]
            if skill_feats_4:
                sf4 = random.choice(skill_feats_4)
                chosen_feats.append(FeatSummary(
                    id=sf4["id"],
                    name=sf4["name"],
                    category="Skill (Level 4)",
                    action_cost=sf4.get("action_cost"),
                    traits=sf4.get("traits", []),
                    description=clean_pf2e_text(sf4.get("description", ""))
                ))

        # 6. Skills
        all_skills = resolve_character_skills(
            class_name=cls["name"],
            background_data=bg,
            attribute_mods=mods,
            level=level
        )

        # 7. Spellcasting
        spellcasting_data = resolve_spellcasting(
            class_name=cls["name"],
            attribute_mods=mods,
            level=level
        )

        # 8. Focus Spells & Pool
        focus_data = resolve_focus_spells(
            class_name=cls["name"],
            feats=chosen_feats,
            attribute_mods=mods,
            level=level
        )

        # 9. Partner Creature (Eidolon, Construct, Undead, Plant, Familiar, or Animal Companion)
        companion_data = None
        arch_name = archetype_data["name"].lower() if archetype_data else ""
        all_feat_str = " ".join([f.name.lower() for f in chosen_feats])

        if cls_name_lower == "summoner":
            companion_data = resolve_eidolon(master_hp=total_hp, level=level)
        elif cls_name_lower == "inventor":
            companion_data = resolve_construct_companion(master_int_mod=mods["int"], level=level)
        elif "undead master" in arch_name or "undead companion" in all_feat_str:
            companion_data = resolve_undead_companion(level=level)
        elif "plant companion" in all_feat_str or (cls_name_lower == "druid" and "leaf" in all_feat_str):
            companion_data = resolve_plant_companion(level=level)
        elif cls_name_lower == "witch" or "familiar" in all_feat_str:
            # At level 4+, roll a Specific Familiar upgrade 50% of the time
            if level >= 4 and random.random() < 0.5:
                companion_data = resolve_specific_familiar(
                    master_ac=calculated_ac,
                    master_fort=fort_prof.modifier,
                    master_ref=ref_prof.modifier,
                    master_will=will_prof.modifier,
                    master_perception=perception_prof.modifier,
                    level=level
                )
            else:
                companion_data = resolve_familiar(
                    master_ac=calculated_ac,
                    master_fort=fort_prof.modifier,
                    master_ref=ref_prof.modifier,
                    master_will=will_prof.modifier,
                    master_perception=perception_prof.modifier,
                    class_name=cls["name"],
                    level=level
                )
        else:
            companion_data = resolve_companion(
                class_name=cls["name"],
                feats=chosen_feats,
                archetype=archetype_data["name"] if archetype_data else None,
                level=level
            )

        return CharacterSheet(
            name=resolved_name,
            level=level,
            ancestry=anc["name"],
            heritage=heritage_data["name"],
            background=bg["name"],
            character_class=cls["name"],
            subclass=SubclassSummary(**subclass_data) if subclass_data else None,
            archetype=archetype_data["name"] if archetype_data else None,
            size=anc.get("size", "med"),
            speed=anc.get("speed", 25),
            attributes=AttributeModifiers(**mods),
            defenses=Defenses(
                ac=calculated_ac,
                shield_bonus=shield_bonus,
                hp=total_hp,
                fortitude=fort_prof,
                reflex=ref_prof,
                will=will_prof,
            ),
            perception=perception_prof,
            all_skills=all_skills,
            equipment=equipment_loadout,
            spellcasting=spellcasting_data,
            focus_spells=focus_data,
            companion=companion_data,
            feats=chosen_feats,
            traits=[anc["name"].lower(), cls["name"].lower()],
        )
