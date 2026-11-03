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
    PartnerCreatureData,
)
from app.engine.names import generate_ancestry_name
from app.engine.equipment import resolve_equipment
from app.engine.skills import resolve_character_skills
from app.engine.spells import resolve_spellcasting
from app.engine.focus import resolve_focus_spells
from app.engine.subclasses import resolve_heritage, resolve_subclass
from app.engine.archetypes import pick_archetype, ARCHETYPES_CATALOG, resolve_dynamic_archetype
from app.engine.companions import resolve_companion
from app.engine.eidolons import resolve_eidolon
from app.engine.familiars import resolve_familiar
from app.engine.constructs_undead import resolve_construct_companion, resolve_undead_companion
from app.engine.plants_familiars_summons import resolve_plant_companion, resolve_specific_familiar

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

CLASS_FEATURES_LVL5 = {
    "fighter": {"name": "Fighter Weapon Mastery", "description": "Your proficiency rank increases to Master in simple and martial weapons of your chosen group (+6). Critical hits apply the critical specialization effect."},
    "barbarian": {"name": "Brutal Bulwark", "description": "Your proficiency rank for Fortitude saves increases to Master. Your melee strikes deal extra specialization damage."},
    "rogue": {"name": "Weapon Tricks", "description": "Your proficiency rank for simple weapons and martial finesse weapons increases to Expert (+4). You deal sneak attack with critical specialization."},
    "champion": {"name": "Weapon Expertise", "description": "Your proficiency rank increases to Expert in simple and martial weapons (+4). You inflict critical specialization effects on foes affected by your cause."},
    "ranger": {"name": "Ranger Weapon Expertise", "description": "Your proficiency rank for simple and martial weapons increases to Expert (+4). Critical hits trigger the weapon's critical specialization effect."},
    "monk": {"name": "Expert Strikes", "description": "Your proficiency rank for unarmed attacks increases to Expert (+4). You gain critical specialization effects with unarmed strikes."},
    "wizard": {"name": "Reflex Expertise", "description": "Your proficiency rank for Reflex saves increases to Expert (+4)."},
    "cleric": {"name": "Alertness", "description": "Your proficiency rank for Perception increases to Expert (+4)."},
    "druid": {"name": "Alertness", "description": "Your proficiency rank for Perception increases to Expert (+4)."},
    "sorcerer": {"name": "Alertness", "description": "Your proficiency rank for Perception increases to Expert (+4)."},
    "witch": {"name": "Reflex Expertise", "description": "Your proficiency rank for Reflex saves increases to Expert (+4)."},
    "bard": {"name": "Lightning Reflexes", "description": "Your proficiency rank for Reflex saves increases to Expert (+4)."}
}

CURATED_ANCESTRY_FEATS_LVL5 = {
    "dwarf": {"name": "Dwarven Reinforcement", "description": "You can strengthen mundane materials, increasing their Hardness and HP, and gain a +1 bonus to Crafting checks."},
    "elf": {"name": "Agile Escort", "description": "Your Speed increases by 5 feet, and you can Step twice when taking an action to escort an ally."},
    "human": {"name": "Sense Allies", "description": "You instinctively know the location of allies within 30 feet, ignoring concealment against them."},
    "goblin": {"name": "Kneecap", "description": "When you hit an off-guard foe with a Strike, the target takes a -10-foot circumstance penalty to its Speeds."},
    "gnome": {"name": "Animal Elocutionist", "description": "You can speak to all animals using Speak with Animals as an innate primal spell."},
    "halfling": {"name": "Halfling Ingenuity", "description": "You can attempt any skill check that requires trained proficiency even if you are untrained."},
    "orc": {"name": "Ferocious Charge", "description": "Stride up to twice your Speed and make a Strike with a +1 circumstance bonus to the attack roll."},
    "leshy": {"name": "Solar Nourishment", "description": "You can draw all your nourishment from sunlight and water, gaining resistance to negative effects."},
    "anadi": {"name": "Hybrid Shape", "description": "You can assume a hybrid form combining humanoid stance with spider climbing and fangs."},
    "automaton": {"name": "Reinforced Chassis", "description": "Your internal plating hardens, granting you resistance to physical damage."},
    "kobold": {"name": "Kobold Breath", "description": "You channel dragon blood to exhale an elemental blast in a 15-foot cone for 3d4 damage."}
}

ALL_SKILL_NAMES = [
    "Acrobatics", "Athletics", "Deception", "Diplomacy", "Intimidation",
    "Medicine", "Nature", "Occultism", "Performance", "Religion",
    "Society", "Stealth", "Survival", "Thievery"
]

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
def scale_existing_companion(companion_data: dict, old_level: int, target_level: int, master_hp: int) -> dict:
    """
    Scales an existing companion's numerical stats from old_level to target_level
    while preserving its name, species, sub-type, traits, and abilities.
    """
    comp = dict(companion_data)
    level_delta = target_level - old_level
    if level_delta <= 0:
        return comp

    creature_type = (comp.get("creature_type") or "").lower()

    # 1. Hit Points
    if "eidolon" in creature_type:
        comp["hp"] = master_hp
    else:
        # Standard animal / construct companion HP gain: ~8 HP per level
        comp["hp"] = comp.get("hp", 20) + (level_delta * 8)

    # 2. Level 4 Maturity Milestone Boost (Trained -> Expert bump of +2)
    stage_bump = 2 if (old_level < 4 and target_level >= 4 and "eidolon" not in creature_type) else 0

    # 3. Defenses (AC & Saves scale by level_delta + maturity bump)
    total_stat_boost = level_delta + stage_bump
    comp["ac"] = comp.get("ac", 16) + total_stat_boost
    comp["fortitude"] = comp.get("fortitude", 5) + total_stat_boost
    comp["reflex"] = comp.get("reflex", 5) + total_stat_boost
    comp["will"] = comp.get("will", 5) + total_stat_boost
    comp["perception"] = comp.get("perception", 4) + total_stat_boost

    # 4. Strikes
    updated_strikes = []
    for strike in comp.get("strikes", []):
        s = dict(strike)
        s["attack_bonus"] = s.get("attack_bonus", 5) + total_stat_boost
        if "map_second" in s:
            s["map_second"] = s.get("map_second", 0) + total_stat_boost
        if "map_third" in s:
            s["map_third"] = s.get("map_third", -5) + total_stat_boost
        updated_strikes.append(s)
    comp["strikes"] = updated_strikes

    # 5. Advance Stage Name at Level 4 for Animal Companions
    if target_level >= 4 and "Young" in comp.get("stage", ""):
        comp["stage"] = comp["stage"].replace("Young", "Mature")

    return comp
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
        background_name: Optional[str] = None,
        archetype_name: Optional[str] = None,
        char_name: Optional[str] = None,
        level: int = 1,
        use_dedication: bool = False
    ) -> CharacterSheet:
        level = max(1, min(6, int(level)))

        # 1. Select Ancestry, Class, Background
        if ancestry_name and ancestry_name.lower() in self.ancestries:
            anc = self.ancestries[ancestry_name.lower()]
        else:
            anc = random.choice(list(self.ancestries.values()))

        if class_name and class_name.lower() in self.classes:
            cls = self.classes[class_name.lower()]
        else:
            cls = random.choice(list(self.classes.values()))

        if background_name and background_name.strip():
            matched_bg = next((b for b in self.backgrounds.values() if b["name"].lower() == background_name.strip().lower()), None)
            bg = matched_bg if matched_bg else random.choice(list(self.backgrounds.values()))
        else:
            bg = random.choice(list(self.backgrounds.values()))
        heritage_data = resolve_heritage(anc["name"])
        subclass_data = resolve_subclass(cls["name"])
        resolved_name = char_name.strip() if char_name and char_name.strip() else generate_ancestry_name(anc["name"])
        if archetype_name and archetype_name.strip():
            archetype_data = resolve_dynamic_archetype(archetype_name.strip(), self.feats) if level >= 2 else None
        elif use_dedication and level >= 2:
            archetype_data = pick_archetype(cls["name"])
        else:
            archetype_data = None

        # 2. Track Attribute Boosts (Level 1)
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

        # 2b. Level 5 Attribute Boosts (4 distinct boosts to top attributes)
        if level >= 5:
            lvl5_boosts_applied: Set[str] = set()
            lvl5_priority = [key_attr, "con", "dex", "wis", "str", "int", "cha"]
            for attr in lvl5_priority:
                if len(lvl5_boosts_applied) < 4 and attr not in lvl5_boosts_applied:
                    mods[attr] += 1
                    lvl5_boosts_applied.add(attr)

        # 3. Defenses & Proficiencies
        fort_rank = cls.get("saving_throws", {}).get("fortitude", 1)
        ref_rank = cls.get("saving_throws", {}).get("reflex", 1)
        will_rank = cls.get("saving_throws", {}).get("will", 1)
        perception_rank = cls.get("perception", 1)

        # Scale saves & perception at Level 3 and Level 5
        if level >= 3 and cls["name"].lower() in ["fighter", "ranger"] and will_rank < 2:
            will_rank = 2
        if level >= 5:
            if cls["name"].lower() == "barbarian" and fort_rank < 3:
                fort_rank = 3
            elif cls["name"].lower() in ["cleric", "druid", "sorcerer"] and perception_rank < 2:
                perception_rank = 2
            elif cls["name"].lower() in ["wizard", "witch", "bard"] and ref_rank < 2:
                ref_rank = 2

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

        if level >= 5:
            for strike in equipment_loadout.strikes:
                extra_prof = 2
                strike.attack_bonus += extra_prof
                strike.map_second += extra_prof
                strike.map_third += extra_prof

        con_mod = mods["con"]
        class_hp_per_lvl = cls.get("hp_per_level", 8)
        base_hp = anc.get("hp", 8) + ((class_hp_per_lvl + con_mod) * level)
        total_hp = max(1, base_hp)

        # 5. Feat Progression
        cls_name_lower = cls["name"].lower()
        chosen_feats: List[FeatSummary] = []

        # Heritage Feature & Concrete Choice Resolution
        h_name = heritage_data["name"]
        h_desc = clean_pf2e_text(heritage_data["description"])
        extra_trained_skill: Optional[str] = None

        if "Versatile" in h_name:
            v_choice = random.choice([
                {"name": "Fleet", "desc": "Your Speed increases by 5 feet."},
                {"name": "Toughness", "desc": "Your maximum HP increases by your level. Recovery check DC is 9 + dying value."},
                {"name": "Diehard", "desc": "You die from the dying condition at dying 5, rather than dying 4."},
                {"name": "Fast Recovery", "desc": "You regain twice as many HP from resting and gain a +2 bonus against poison/disease."}
            ])
            h_name = f"Versatile Heritage: {v_choice['name']}"
            h_desc = f"Selected General Feat: {v_choice['name']}. {v_choice['desc']}"
        elif "Skilled" in h_name:
            chosen_skill = random.choice(ALL_SKILL_NAMES)
            extra_trained_skill = chosen_skill
            h_name = f"Skilled Heritage: {chosen_skill}"
            h_desc = f"Selected Trained Skill: {chosen_skill}. You become trained in {chosen_skill}, gaining a +2 proficiency bonus plus level and key attribute modifier."

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

        # Level 5 Progression
        if level >= 5:
            anc_name_lower = anc["name"].lower()
            lvl5_anc_feats = [
                f for f in self.feats
                if f.get("category") == "ancestry"
                and f.get("level") == 5
                and anc_name_lower in [t.lower() for t in f.get("traits", [])]
            ]

            if lvl5_anc_feats:
                af5 = random.choice(lvl5_anc_feats)
                chosen_feats.append(FeatSummary(
                    id=af5["id"],
                    name=af5["name"],
                    category="Ancestry (Level 5)",
                    action_cost=af5.get("action_cost"),
                    traits=af5.get("traits", []),
                    description=clean_pf2e_text(af5.get("description", ""))
                ))
            else:
                fallback_af = CURATED_ANCESTRY_FEATS_LVL5.get(
                    anc_name_lower,
                    {"name": f"{anc['name']} Resiliency", "description": "You draw deep upon your heritage to endure hardships, gaining a +1 circumstance bonus to saving throws."}
                )
                chosen_feats.append(FeatSummary(
                    id=f"anc-feat-{anc_name_lower}-5",
                    name=fallback_af["name"],
                    category="Ancestry (Level 5)",
                    action_cost=None,
                    traits=[anc_name_lower],
                    description=clean_pf2e_text(fallback_af["description"])
                ))

            if cls_name_lower in CLASS_FEATURES_LVL5:
                cf5 = CLASS_FEATURES_LVL5[cls_name_lower]
                chosen_feats.append(FeatSummary(
                    id=f"class-feat-{cf5['name'].lower().replace(' ', '-')}",
                    name=cf5["name"],
                    category="Class Feature (Level 5)",
                    action_cost=None,
                    traits=[cls_name_lower],
                    description=clean_pf2e_text(cf5["description"])
                ))

        # Level 6 Progression (Class Feat / Archetype Feat)
        if level >= 6:
            lvl6_class_feats = [
                f for f in self.feats
                if f.get("category") == "class"
                and f.get("level") in (4, 6)
                and cls_name_lower in [t.lower() for t in f.get("traits", [])]
            ]
            if lvl6_class_feats:
                cf6 = random.choice(lvl6_class_feats)
                chosen_feats.append(FeatSummary(
                    id=cf6["id"],
                    name=cf6["name"],
                    category="Class Feat (Level 6)",
                    action_cost=cf6.get("action_cost"),
                    traits=cf6.get("traits", []),
                    description=clean_pf2e_text(cf6.get("description", ""))
                ))

        # 6. Skills
        all_skills = resolve_character_skills(
            class_name=cls["name"],
            background_data=bg,
            attribute_mods=mods,
            level=level
        )

        if extra_trained_skill:
            for sk in all_skills:
                if sk.name.lower() == extra_trained_skill.lower() and sk.rank == 0:
                    sk.rank = 2
                    sk.rank_letter = "T"
                    sk.modifier += (2 + level)

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
            subclass_name=subclass_data["name"] if subclass_data else None,
            level=level
        )

        # 9. Partner Creature
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
            ancestry_description=clean_pf2e_text(anc.get("description", "")),
            heritage=heritage_data["name"],
            background=bg["name"],
            background_description=clean_pf2e_text(bg.get("description", "")),
            character_class=cls["name"],
            subclass=SubclassSummary(**subclass_data) if subclass_data else None,
            archetype=archetype_data["name"] if archetype_data else None,
            archetype_description=clean_pf2e_text(archetype_data.get("level_2_dedication", {}).get("description", "")) if archetype_data else None,
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

    def level_up(self, current_char: Dict[str, Any], target_level: int) -> CharacterSheet:
        target_level = max(1, min(6, int(target_level)))
        old_level = int(current_char.get("level", 1))

        # 1. Recover base info and core data
        anc_name = (current_char.get("ancestry") or "").strip().lower()
        cls_name = (current_char.get("character_class") or "").strip().lower()
        bg_name = (current_char.get("background") or "").strip().lower()

        anc = self.ancestries.get(anc_name) or next(
            (a for a in self.ancestries.values() if a["name"].lower() == anc_name),
            list(self.ancestries.values())[0]
        )
        cls = self.classes.get(cls_name) or next(
            (c for c in self.classes.values() if c["name"].lower() == cls_name),
            list(self.classes.values())[0]
        )
        bg = self.backgrounds.get(bg_name) or next(
            (b for b in self.backgrounds.values() if b["name"].lower() == bg_name),
            list(self.backgrounds.values())[0]
        )

        # 2. Extract current attributes
        raw_attrs = current_char.get("attributes", {})
        mods = {attr: raw_attrs.get(attr, 0) for attr in ATTRIBUTES}

        key_options = [k.lower() for k in cls.get("key_attributes", []) if k.lower() in ATTRIBUTES]
        key_attr = key_options[0] if key_options else "str"

        if old_level < 5 and target_level >= 5:
            lvl5_boosts_applied: Set[str] = set()
            lvl5_priority = [key_attr, "con", "dex", "wis", "str", "int", "cha"]
            for attr in lvl5_priority:
                if len(lvl5_boosts_applied) < 4 and attr not in lvl5_boosts_applied:
                    mods[attr] += 1
                    lvl5_boosts_applied.add(attr)

        # 3. Defenses & Proficiencies
        fort_rank = cls.get("saving_throws", {}).get("fortitude", 1)
        ref_rank = cls.get("saving_throws", {}).get("reflex", 1)
        will_rank = cls.get("saving_throws", {}).get("will", 1)
        perception_rank = cls.get("perception", 1)

        if target_level >= 3 and cls["name"].lower() in ["fighter", "ranger"] and will_rank < 2:
            will_rank = 2
        if target_level >= 5:
            if cls["name"].lower() == "barbarian" and fort_rank < 3:
                fort_rank = 3
            elif cls["name"].lower() in ["cleric", "druid", "sorcerer"] and perception_rank < 2:
                perception_rank = 2
            elif cls["name"].lower() in ["wizard", "witch", "bard"] and ref_rank < 2:
                ref_rank = 2

        fort_prof = self._calc_prof(fort_rank, target_level, mods["con"])
        ref_prof = self._calc_prof(ref_rank, target_level, mods["dex"])
        will_prof = self._calc_prof(will_rank, target_level, mods["wis"])
        perception_prof = self._calc_prof(perception_rank, target_level, mods["wis"])

        # 4. Equipment & Recalculated HP
        equipment_loadout, calculated_ac, shield_bonus = resolve_equipment(
            cls["name"],
            str_mod=mods["str"],
            dex_mod=mods["dex"],
            level=target_level
        )

        if target_level >= 5:
            for strike in equipment_loadout.strikes:
                extra_prof = 2
                strike.attack_bonus += extra_prof
                strike.map_second += extra_prof
                strike.map_third += extra_prof

        con_mod = mods["con"]
        class_hp_per_lvl = cls.get("hp_per_level", 8)
        base_hp = anc.get("hp", 8) + ((class_hp_per_lvl + con_mod) * target_level)
        total_hp = max(1, base_hp)

        # 5. Resolve Archetype
        archetype_data = None
        existing_arch_name = current_char.get("archetype")
        if target_level >= 2:
            archetype_data = pick_archetype(cls["name"])
            resolved_arch_name = existing_arch_name or (archetype_data["name"] if archetype_data else None)
        else:
            resolved_arch_name = None

        # 6. Preserve and advance feats
        existing_feats_raw = current_char.get("feats", [])
        chosen_feats: List[FeatSummary] = [FeatSummary(**f) for f in existing_feats_raw]
        existing_feat_names = {f.name for f in chosen_feats}
        cls_name_lower = cls["name"].lower()

        for lvl in range(old_level + 1, target_level + 1):
            if lvl == 2:
                if archetype_data and archetype_data["level_2_dedication"]["name"] not in existing_feat_names:
                    ded = archetype_data["level_2_dedication"]
                    chosen_feats.append(FeatSummary(
                        id=ded["id"],
                        name=ded["name"],
                        category=f"Archetype ({archetype_data['name']})",
                        action_cost=ded.get("action_cost"),
                        traits=ded.get("traits", []),
                        description=clean_pf2e_text(ded["description"])
                    ))
                    existing_feat_names.add(ded["name"])
                else:
                    lvl2_feats = [
                        f for f in self.feats
                        if f.get("category") == "class"
                        and f.get("level") == 2
                        and cls_name_lower in [t.lower() for t in f.get("traits", [])]
                        and f["name"] not in existing_feat_names
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
                        existing_feat_names.add(f2["name"])

                skill_feats_2 = [
                    f for f in self.feats
                    if f.get("category") == "skill"
                    and f.get("level") in [1, 2]
                    and f["name"] not in existing_feat_names
                ]
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
                    existing_feat_names.add(sf["name"])

            elif lvl == 3:
                gf_pool = [f for f in GENERAL_FEATS_LVL3 if f["name"] not in existing_feat_names]
                if gf_pool:
                    gf = random.choice(gf_pool)
                    chosen_feats.append(FeatSummary(
                        id=gf["id"],
                        name=gf["name"],
                        category="General (Level 3)",
                        action_cost=None,
                        traits=["general"],
                        description=clean_pf2e_text(gf["description"])
                    ))
                    existing_feat_names.add(gf["name"])

                if cls_name_lower in CLASS_FEATURES_LVL3:
                    cf = CLASS_FEATURES_LVL3[cls_name_lower]
                    if cf["name"] not in existing_feat_names:
                        chosen_feats.append(FeatSummary(
                            id=f"class-feat-{cf['name'].lower().replace(' ', '-')}",
                            name=cf["name"],
                            category="Class Feature (Level 3)",
                            action_cost=None,
                            traits=[cls_name_lower],
                            description=clean_pf2e_text(cf["description"])
                        ))
                        existing_feat_names.add(cf["name"])

            elif lvl == 4:
                if archetype_data:
                    arch_lvl4 = [f for f in archetype_data.get("level_4_feats", []) if f["name"] not in existing_feat_names]
                    if arch_lvl4:
                        af4 = random.choice(arch_lvl4)
                        chosen_feats.append(FeatSummary(
                            id=af4["id"],
                            name=af4["name"],
                            category=f"Archetype ({archetype_data['name']})",
                            action_cost=af4.get("action_cost"),
                            traits=af4.get("traits", []),
                            description=clean_pf2e_text(af4["description"])
                        ))
                        existing_feat_names.add(af4["name"])
                else:
                    lvl4_feats = [
                        f for f in self.feats
                        if f.get("category") == "class"
                        and f.get("level") in [1, 2, 4]
                        and cls_name_lower in [t.lower() for t in f.get("traits", [])]
                        and f["name"] not in existing_feat_names
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
                        existing_feat_names.add(f4["name"])

                skill_feats_4 = [
                    f for f in self.feats
                    if f.get("category") == "skill"
                    and f.get("level") in [1, 2, 4]
                    and f["name"] not in existing_feat_names
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
                    existing_feat_names.add(sf4["name"])

            elif lvl == 5:
                anc_name_lower = anc["name"].lower()
                lvl5_anc_feats = [
                    f for f in self.feats
                    if f.get("category") == "ancestry"
                    and f.get("level") == 5
                    and anc_name_lower in [t.lower() for t in f.get("traits", [])]
                    and f["name"] not in existing_feat_names
                ]
                if lvl5_anc_feats:
                    af5 = random.choice(lvl5_anc_feats)
                    chosen_feats.append(FeatSummary(
                        id=af5["id"],
                        name=af5["name"],
                        category="Ancestry (Level 5)",
                        action_cost=af5.get("action_cost"),
                        traits=af5.get("traits", []),
                        description=clean_pf2e_text(af5.get("description", ""))
                    ))
                    existing_feat_names.add(af5["name"])
                else:
                    fallback_af = CURATED_ANCESTRY_FEATS_LVL5.get(
                        anc_name_lower,
                        {"name": f"{anc['name']} Resiliency", "description": "You draw deep upon your heritage to endure hardships, gaining a +1 circumstance bonus to saving throws."}
                    )
                    chosen_feats.append(FeatSummary(
                        id=f"anc-feat-{anc_name_lower}-5",
                        name=fallback_af["name"],
                        category="Ancestry (Level 5)",
                        action_cost=None,
                        traits=[anc_name_lower],
                        description=clean_pf2e_text(fallback_af["description"])
                    ))
                    existing_feat_names.add(fallback_af["name"])

                if cls_name_lower in CLASS_FEATURES_LVL5:
                    cf5 = CLASS_FEATURES_LVL5[cls_name_lower]
                    if cf5["name"] not in existing_feat_names:
                        chosen_feats.append(FeatSummary(
                            id=f"class-feat-{cf5['name'].lower().replace(' ', '-')}",
                            name=cf5["name"],
                            category="Class Feature (Level 5)",
                            action_cost=None,
                            traits=[cls_name_lower],
                            description=clean_pf2e_text(cf5["description"])
                        ))
                        existing_feat_names.add(cf5["name"])

            elif lvl == 6:
                lvl6_class_feats = [
                    f for f in self.feats
                    if f.get("category") == "class"
                    and f.get("level") in (4, 6)
                    and cls_name_lower in [t.lower() for t in f.get("traits", [])]
                    and f["name"] not in existing_feat_names
                ]
                if lvl6_class_feats:
                    cf6 = random.choice(lvl6_class_feats)
                    chosen_feats.append(FeatSummary(
                        id=cf6["id"],
                        name=cf6["name"],
                        category="Class Feat (Level 6)",
                        action_cost=cf6.get("action_cost"),
                        traits=cf6.get("traits", []),
                        description=clean_pf2e_text(cf6.get("description", ""))
                    ))
                    existing_feat_names.add(cf6["name"])

        if any(f.name.lower() == "toughness" for f in chosen_feats):
            total_hp += target_level

        # 7. Skills
        all_skills = resolve_character_skills(
            class_name=cls["name"],
            background_data=bg,
            attribute_mods=mods,
            level=target_level
        )

        # 8. Spellcasting
        spellcasting_data = resolve_spellcasting(
            class_name=cls["name"],
            attribute_mods=mods,
            level=target_level
        )

        focus_data = resolve_focus_spells(
            class_name=cls["name"],
            feats=chosen_feats,
            attribute_mods=mods,
            subclass_name=current_char.get("subclass", {}).get("name") if current_char.get("subclass") else None,
            level=target_level
        )

        # 9. Companions (Preserve identity and scale stats in place)
        raw_companion = current_char.get("companion")
        if raw_companion and raw_companion.get("name"):
            scaled_dict = scale_existing_companion(
                companion_data=raw_companion,
                old_level=old_level,
                target_level=target_level,
                master_hp=total_hp
            )
            companion_data = PartnerCreatureData(**scaled_dict)
        else:
            companion_data = resolve_companion(
                class_name=cls["name"],
                feats=chosen_feats,
                archetype=resolved_arch_name,
                level=target_level
            )

        # 10. Assemble and Return
        subclass_obj = SubclassSummary(**current_char["subclass"]) if current_char.get("subclass") else None
        anc_desc = clean_pf2e_text(anc.get("description", "")) or current_char.get("ancestry_description", "")

        return CharacterSheet(
            name=current_char["name"],
            level=target_level,
            ancestry=anc["name"],
            ancestry_description=anc_desc,
            heritage=current_char["heritage"],
            background=current_char["background"],
            background_description=current_char.get("background_description") or clean_pf2e_text(bg.get("description", "")),
            character_class=cls["name"],
            subclass=subclass_obj,
            archetype=resolved_arch_name,
            archetype_description=current_char.get("archetype_description") or (clean_pf2e_text(archetype_data.get("level_2_dedication", {}).get("description", "")) if archetype_data else None),
            size=anc.get("size", current_char.get("size", "med")),
            speed=anc.get("speed", current_char.get("speed", 25)),
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
            traits=current_char.get("traits", [anc["name"].lower(), cls["name"].lower()]),
        )
