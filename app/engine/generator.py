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
from app.engine.feat_prereqs import check_feat_prerequisites, calculate_feat_weight
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

CLASS_FEATURES_LVL1 = {
    "rogue": {
        "name": "Sneak Attack",
        "description": "When your Strike hits an off-guard target and deals damage, you deal an extra {sneak_dice} precision damage."
    },
    "swashbuckler": {
        "name": "Panache & Finisher",
        "description": "When you have panache, your Strikes deal +{panache_flat} precision damage. Using a Finisher ends panache and deals +{finisher_dice} precision damage."
    },
    "investigator": {
        "name": "Devise a Stratagem",
        "description": "You assess a foe's defenses. Once per round (1 action or free action against your lead), roll a d20 and use it for your next Strike against that creature with your Intelligence modifier to attack."
    },
    "thaumaturge": {
        "name": "Exploit Vulnerability",
        "description": "You identify a mortal weakness in your target, dealing mortal weakness or personal antithesis bonus damage."
    }
}

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

def safe_action_cost(val):
    if val is None:
        return None
    if isinstance(val, int):
        return val
    if isinstance(val, str):
        import re
        m = re.search(r"\d+", val)
        if m:
            return int(m.group())
        if any(w in val.lower() for w in ["reaction", "free"]):
            return 0
    return None

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

TERRAIN_TYPES = [
    "Aquatic", "Arctic", "Desert", "Forest",
    "Mountain", "Plains", "Sky", "Swamp", "Underground"
]

def resolve_feat_subchoices(feat_name: str, existing_feat_names: set) -> str:
    fn_lower = feat_name.lower()

    if "wilderness spotter" in fn_lower and "(" not in feat_name:
        taken = [
            fn.split("(")[-1].replace(")", "").strip().title()
            for fn in existing_feat_names
            if "wilderness spotter" in fn.lower() and "(" in fn
        ]
        available = [t for t in TERRAIN_TYPES if t not in taken]
        chosen = random.choice(available) if available else random.choice(TERRAIN_TYPES)
        return f"{feat_name} ({chosen})"

    if "terrain stalker" in fn_lower and "(" not in feat_name:
        stalker_opts = ["Rubble", "Snow", "Underbrush"]
        return f"{feat_name} ({random.choice(stalker_opts)})"

    return feat_name


def pick_weighted_feat(candidates, class_name, owned_names, skill_ranks, mods, char_level):
    valid = [
        f for f in candidates
        if f["name"] not in owned_names
        and check_feat_prerequisites(f, skill_ranks, owned_names, mods, char_level)
    ]
    if not valid:
        # Fallback to general pool without prereqs if list is starved
        valid = [f for f in candidates if f["name"] not in owned_names]
    if not valid:
        return None
    weights = [calculate_feat_weight(f, class_name, owned_names, skill_ranks) for f in valid]
    return random.choices(valid, weights=weights, k=1)[0]

BACKGROUND_CUSTOM_ACTIONS = {
    "hunt the razer's pawn": {
        "name": "Hunt the Razer's Pawn",
        "action_cost": 1,
        "traits": ["Concentrate", "Exploration", "Secret"],
        "description": "You study the demeanor, iconography, or residual essence of a creature to determine if it is an agent or pawn of Treerazer. Attempt a Religion check against the creature's Deception DC. On a success, you learn whether the creature is allied with, dominated by, or in the service of Treerazer or his cult."
    }
}

class PF2eGenerator:
    def __init__(self):
        self.ancestries = {a["name"].lower(): a for a in load_data("ancestries.json")}
        self.classes = {c["name"].lower(): c for c in load_data("classes.json")}
        self.backgrounds = {b["name"].lower(): b for b in load_data("backgrounds.json")}
        raw_feats = load_data("feats.json")
        # Sanitize feat compendium: filter out empty traits, joke/test entries, and malformed records
        self.feats = [
            f for f in raw_feats
            if f.get("name")
            and f.get("traits")
            and len(f.get("traits", [])) > 0
            and f.get("name") not in ["Speedrun Strats"]
        ]

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
        level = max(1, min(7, int(level)))

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
        raw_arch = archetype_name.strip() if archetype_name and archetype_name.strip() else ""
        if raw_arch.lower() in ["", "any", "any archetype", "none", "random"]:
            clean_arch_input = None
        else:
            clean_arch_input = raw_arch

        archetype_data = None
        if clean_arch_input:
            archetype_data = resolve_dynamic_archetype(clean_arch_input, self.feats)

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

        # Resolve archetype if dedication toggle is enabled and no specific archetype was forced
        if not archetype_data and use_dedication and level >= 2:
            archetype_data = pick_archetype(cls["name"], {}, mods)

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
        if level >= 7:
            if cls["name"].lower() in ["ranger", "rogue"] and perception_rank < 3:
                perception_rank = 3
            elif cls["name"].lower() == "barbarian" and will_rank < 2:
                will_rank = 2
            elif cls["name"].lower() == "champion" and fort_rank < 3:
                fort_rank = 3

        fort_prof = self._calc_prof(fort_rank, level, mods["con"])
        ref_prof = self._calc_prof(ref_rank, level, mods["dex"])
        will_prof = self._calc_prof(will_rank, level, mods["wis"])
        perception_prof = self._calc_prof(perception_rank, level, mods["wis"])

        # 4. Equipment & HP
        equipment_loadout, calculated_ac, shield_bonus = resolve_equipment(
            cls["name"],
            str_mod=mods["str"],
            dex_mod=mods["dex"],
            level=level,
            ancestry_name=anc["name"]
        )

        if level >= 5:
            for strike in equipment_loadout.strikes:
                extra_prof = 2
                strike.attack_bonus += extra_prof
                strike.map_second += extra_prof
                strike.map_third += extra_prof
        if level >= 7:
            for strike in equipment_loadout.strikes:
                # Weapon Specialization (+2 damage)
                if "+2" not in strike.damage_dice and "Weapon Spec" not in strike.damage_dice:
                    strike.damage_dice = f"{strike.damage_dice} + 2" 

        con_mod = mods["con"]
        class_hp_per_lvl = cls.get("hp_per_level", 8)
        base_hp = anc.get("hp", 8) + ((class_hp_per_lvl + con_mod) * level)
        bonus_speed = 0
        total_hp = max(1, base_hp)

        # 5. Feat Progression
        cls_name_lower = cls["name"].lower()
        chosen_feats: List[FeatSummary] = []
                        # Extract background skill feat if present
        bg_desc = bg.get("description", "")
        bg_feat_match = re.search(r"@UUID\[[^\]]*feats-srd\.Item\.([^\]]+)\]", bg_desc) or re.search(r"Item\.([^\]]+)\]\s+skill feat", bg_desc)
        bg_feat_name = bg_feat_match.group(1).strip() if bg_feat_match else None
        if bg_feat_name:
            chosen_feats.append(FeatSummary(
                id=f"feat-bg-{bg_feat_name.lower().replace(' ', '-')}",
                name=bg_feat_name,
                category="Background Feat",
                action_cost=None,
                traits=["General", "Skill"],
                description=f"Granted by the {bg['name']} background."
            ))

        # Extract background custom actions (e.g. gain the @UUID[...actionspf2e.Item.Hunt the Razer's Pawn] action)
        # Avoid standard inline actions like Seek or Sense Motive
        action_match = (
            re.search(r"gain the\s+@UUID\[[^\]]*actionspf2e\.Item\.([^\]]+)\]\s+action", bg_desc, re.IGNORECASE)
            or re.search(r"gain the\s+([A-Z][a-zA-Z0-9'\s\-]+?)\s+action", bg_desc, re.IGNORECASE)
        )
        if action_match:
            action_name = action_match.group(1).strip()
            action_key = action_name.lower()
            if action_key not in ["seek", "sense motive"]:
                clean_action_id = action_key.replace(" ", "-").replace("'", "")
                if action_key in BACKGROUND_CUSTOM_ACTIONS:
                    c_act = BACKGROUND_CUSTOM_ACTIONS[action_key]
                    chosen_feats.append(FeatSummary(
                        id=f"feat-bg-action-{clean_action_id}",
                        name=c_act["name"],
                        category="Background Action",
                        action_cost=c_act.get("action_cost"),
                        traits=c_act.get("traits", ["Background"]),
                        description=c_act["description"]
                    ))
                else:
                    chosen_feats.append(FeatSummary(
                        id=f"feat-bg-action-{clean_action_id}",
                        name=action_name,
                        category="Background Action",
                        action_cost=None,
                        traits=["Background"],
                        description=f"Special action granted by the {bg['name']} background."
                    ))

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

        # Level 1 Core Identity Features (Sneak Attack, Panache, Stratagem)
        if cls_name_lower in CLASS_FEATURES_LVL1:
            base_cf1 = CLASS_FEATURES_LVL1[cls_name_lower]
            s_dice = "2d6" if level >= 5 else "1d6"
            f_dice = "3d6" if level >= 5 else "2d6"
            p_flat = "3" if level >= 5 else "2"
            desc = base_cf1["description"].format(sneak_dice=s_dice, finisher_dice=f_dice, panache_flat=p_flat)
            chosen_feats.append(FeatSummary(
                id=f"{cls_name_lower}-lvl1-feature",
                name=base_cf1["name"],
                category="Class Feature (Level 1)",
                action_cost=None,
                traits=[cls_name_lower],
                description=desc
            ))

        # Level 1 Class Feat
        lvl1_feats = [
            f for f in self.feats
            if f.get("category") == "class"
            and f.get("level") == 1
            and cls_name_lower in [t.lower() for t in f.get("traits", [])]
        ]
        if lvl1_feats:
            skill_ranks_tmp = {s.name: s.rank for s in (all_skills if "all_skills" in locals() else [])}
            f1 = pick_weighted_feat(lvl1_feats, cls["name"], {f.name for f in chosen_feats}, skill_ranks_tmp, mods, 1) or random.choice(lvl1_feats)
            chosen_feats.append(FeatSummary(
                id=f1["id"],
                name=f1["name"],
                category="Class (Level 1)",
                action_cost=safe_action_cost(f1.get("action_cost")),
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
                    skill_ranks_tmp = {s.name: s.rank for s in (all_skills if "all_skills" in locals() else [])}
                    f2 = pick_weighted_feat(lvl2_feats, cls["name"], {f.name for f in chosen_feats}, skill_ranks_tmp, mods, 2) or random.choice(lvl2_feats)
                    chosen_feats.append(FeatSummary(
                        id=f2["id"],
                        name=f2["name"],
                        category="Class (Level 2)",
                        action_cost=safe_action_cost(f2.get("action_cost")),
                        traits=f2.get("traits", []),
                        description=clean_pf2e_text(f2.get("description", ""))
                    ))

            # Derive skill ranks for prerequisite validation
            skill_ranks = {s.name: s.rank for s in (all_skills if "all_skills" in locals() else [])}
            owned_names = {f.name for f in chosen_feats}

            skill_feats_2 = [f for f in self.feats if f.get("category") == "skill" and f.get("level") in [1, 2]]
            sf = pick_weighted_feat(skill_feats_2, cls["name"], owned_names, skill_ranks, mods, 2)
            if sf:
                resolved_feat_name2 = resolve_feat_subchoices(sf["name"], owned_names)
                chosen_feats.append(FeatSummary(
                    id=sf["id"],
                    name=resolved_feat_name2,
                    category="Skill (Level 2)",
                    action_cost=sf.get("action_cost"),
                    traits=sf.get("traits", []),
                    description=clean_pf2e_text(sf.get("description", ""))
                ))
                owned_names.add(resolved_feat_name2)

        # Level 3 Progression
        if level >= 3:
            gf = random.choice(GENERAL_FEATS_LVL3)
            gf_name = gf["name"]
            gf_desc = clean_pf2e_text(gf["description"])

            if gf["id"] == "toughness":
                total_hp += level
            elif gf["id"] == "fleet":
                bonus_speed += 5
            elif gf["id"] == "ancestral-paragon":
                anc_trait = anc["name"].lower()
                owned_f_names = {f.name.lower() for f in chosen_feats}
                avail_anc_feats = [
                    f for f in self.feats
                    if f.get("category") == "ancestry"
                    and f.get("level") == 1
                    and anc_trait in [t.lower() for t in f.get("traits", [])]
                    and f["name"].lower() not in owned_f_names
                ]
                if not avail_anc_feats:
                    avail_anc_feats = [
                        f for f in self.feats
                        if f.get("category") == "ancestry"
                        and f.get("level") == 1
                        and f["name"].lower() not in owned_f_names
                    ]
                if avail_anc_feats:
                    sub_f = random.choice(avail_anc_feats)
                    gf_name = f"Ancestral Paragon: {sub_f['name']}"
                    gf_desc = f"Selected 1st-level Ancestry Feat: {sub_f['name']}. You gain a 1st-level ancestry feat.\n\n[{sub_f['name']}]: {clean_pf2e_text(sub_f.get('description', ''))}"
                    if "speed" in sub_f["name"].lower() or "nimble" in sub_f["name"].lower():
                        bonus_speed += 5

            chosen_feats.append(FeatSummary(
                id=gf["id"],
                name=gf_name,
                category="General (Level 3)",
                action_cost=None,
                traits=["general"],
                description=gf_desc
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
                        action_cost=safe_action_cost(f4.get("action_cost")),
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
                resolved_name4 = resolve_feat_subchoices(sf4["name"], {f.name for f in chosen_feats})
                chosen_feats.append(FeatSummary(
                    id=sf4["id"],
                    name=resolved_name4,
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
                skill_ranks_tmp = {s.name: s.rank for s in (all_skills if "all_skills" in locals() else [])}
                cf6 = pick_weighted_feat(lvl6_class_feats, cls["name"], {f.name for f in chosen_feats}, skill_ranks_tmp, mods, 6) or random.choice(lvl6_class_feats)
                chosen_feats.append(FeatSummary(
                    id=cf6["id"],
                    name=cf6["name"],
                    category="Class Feat (Level 6)",
                    action_cost=safe_action_cost(cf6.get("action_cost")),
                    traits=cf6.get("traits", []),
                    description=clean_pf2e_text(cf6.get("description", ""))
                ))

            skill_ranks = {s.name: s.rank for s in (all_skills if "all_skills" in locals() else [])}
            owned_names = {f.name for f in chosen_feats}
            skill_feats_6 = [
                f for f in self.feats
                if f.get("category") == "skill"
                and f.get("level") in [1, 2, 4, 6]
            ]
            sf6 = pick_weighted_feat(skill_feats_6, cls["name"], owned_names, skill_ranks, mods, 6)
            if sf6:
                resolved_name6 = resolve_feat_subchoices(sf6["name"], owned_names)
                chosen_feats.append(FeatSummary(
                    id=sf6["id"],
                    name=resolved_name6,
                    category="Skill (Level 6)",
                    action_cost=sf6.get("action_cost"),
                    traits=sf6.get("traits", []),
                    description=clean_pf2e_text(sf6.get("description", ""))
                ))
                owned_names.add(resolved_name6)

        # Level 7 Progression (General Feat & Weapon Specialization Feature)
        if level >= 7:
            gf_pool_7 = [f for f in GENERAL_FEATS_LVL3 if f["name"] not in owned_names]
            if gf_pool_7:
                gf7 = random.choice(gf_pool_7)
                chosen_feats.append(FeatSummary(
                    id=f"{gf7['id']}-7",
                    name=gf7["name"],
                    category="General (Level 7)",
                    action_cost=None,
                    traits=["general"],
                    description=clean_pf2e_text(gf7["description"])
                ))
                owned_names.add(gf7["name"])

            chosen_feats.append(FeatSummary(
                id="class-feat-weapon-specialization",
                name="Weapon Specialization",
                category="Class Feature (Level 7)",
                action_cost=None,
                traits=[cls_name_lower],
                description="You have learned how to inflict greater injuries with your favored weapons. You deal 2 additional damage with weapons and unarmed attacks in which you are trained."
            ))
            owned_names.add("Weapon Specialization")


        # Determine planned archetype to seed prerequisites backwards
        planned_arch = archetype_name.strip() if archetype_name and archetype_name.strip() else None

        # Ensure planned multiclass archetype minimum attributes (+2 / 14) are satisfied
        if planned_arch:
            arch_lower = planned_arch.lower()
            if "champion" in arch_lower:
                mods["str"] = max(mods.get("str", 0), 2)
                mods["cha"] = max(mods.get("cha", 0), 2)
            elif "rogue" in arch_lower:
                mods["dex"] = max(mods.get("dex", 0), 2)

        # 6. Skills
        all_skills = resolve_character_skills(
            class_name=cls["name"],
            background_data=bg,
            attribute_mods=mods,
            level=level,
            feats=chosen_feats,
            planned_archetype=planned_arch
        )

        if extra_trained_skill:
            for sk in all_skills:
                if sk.name.lower() == extra_trained_skill.lower() and sk.rank == 0:
                    sk.rank = 2
                    sk.rank_letter = "T"
                    sk.modifier += (2 + level)

        # 7. Partner Creatures (collect all concurrent partners, e.g., Eidolon + Beastmaster)
        collected_partners = []
        arch_name = archetype_data["name"].lower() if archetype_data else ""
        all_feat_str = " ".join([f.name.lower() for f in chosen_feats])

        # 7a. Class-intrinsic partners
        if cls_name_lower == "summoner":
            eidolon_partner = resolve_eidolon(master_hp=total_hp, level=level)
            collected_partners.append(eidolon_partner)
            if not subclass_data and eidolon_partner:
                subclass_data = {"name": eidolon_partner.name, "title": "Eidolon", "description": f"{eidolon_partner.creature_type} partner"}
                subclass_obj = SubclassSummary(title="Eidolon", name=eidolon_partner.name, description=f"{eidolon_partner.creature_type} partner")
        elif cls_name_lower == "inventor":
            collected_partners.append(resolve_construct_companion(master_int_mod=mods["int"], level=level))
        elif cls_name_lower == "witch":
            if level >= 4 and random.random() < 0.5:
                collected_partners.append(resolve_specific_familiar(
                    master_ac=calculated_ac,
                    master_fort=fort_prof.modifier,
                    master_ref=ref_prof.modifier,
                    master_will=will_prof.modifier,
                    master_perception=perception_prof.modifier,
                    level=level
                ))
            else:
                collected_partners.append(resolve_familiar(
                    master_ac=calculated_ac,
                    master_fort=fort_prof.modifier,
                    master_ref=ref_prof.modifier,
                    master_will=will_prof.modifier,
                    master_perception=perception_prof.modifier,
                    class_name=cls["name"],
                    level=level
                ))

        # 9b. Archetype / Feat companions (Undead Master, Plant, Animal Companion, Familiar)
        # Archetype companions are only active at Level 2+ once the Dedication feat is taken
        has_undead_master = (level >= 2 and archetype_data and "undead master" in arch_name)
        has_beastmaster = (level >= 2 and archetype_data and "beastmaster" in arch_name)

        if has_undead_master or "undead companion" in all_feat_str:
            collected_partners.append(resolve_undead_companion(level=level))
        elif "plant companion" in all_feat_str or (cls_name_lower == "druid" and "leaf" in all_feat_str):
            collected_partners.append(resolve_plant_companion(level=level))
        elif has_beastmaster or "animal companion" in all_feat_str:
            comp = resolve_companion(
                class_name=cls["name"],
                feats=chosen_feats,
                archetype=archetype_data["name"] if (archetype_data and level >= 2) else None,
                level=level
            )
            if comp:
                collected_partners.append(comp)
        elif "familiar" in all_feat_str and cls_name_lower != "witch":
            collected_partners.append(resolve_familiar(
                master_ac=calculated_ac,
                master_fort=fort_prof.modifier,
                master_ref=ref_prof.modifier,
                master_will=will_prof.modifier,
                master_perception=perception_prof.modifier,
                class_name=cls["name"],
                level=level
            ))

        primary_companion = collected_partners[0] if collected_partners else None
        extra_partners = collected_partners[1:] if len(collected_partners) > 1 else []

        # 8. Spellcasting
        sub_name = subclass_data["name"] if subclass_data else None
        spellcasting_data = resolve_spellcasting(
            class_name=cls["name"],
            attribute_mods=mods,
            level=level,
            subclass_name=sub_name
        )

        # 9. Focus Spells & Pool
        focus_data = resolve_focus_spells(
            class_name=cls["name"],
            feats=chosen_feats,
            attribute_mods=mods,
            subclass_name=sub_name,
            level=level
        )

        # Resolve Languages (de-duplicated & distinct)
        COMMON_LANG_POOL = [
            "Common", "Dwarven", "Elven", "Gnomish", "Goblin", "Halfling", 
            "Orcish", "Draconic", "Sylvan", "Undercommon", "Jotun", "Necril", 
            "Aklo", "Celestial", "Abyssal", "Infernal", "Shadowtongue", "Iruxi"
        ]

        assigned_langs = []
        assigned_lower = set()

        def add_language(lang_name: str):
            clean_name = (lang_name or "").strip().title()
            if not clean_name:
                return
            if clean_name.lower() in assigned_lower:
                # Collision: pick a distinct fallback not yet assigned
                fallback_choices = [l for l in COMMON_LANG_POOL if l.lower() not in assigned_lower]
                if fallback_choices:
                    chosen = random.choice(fallback_choices)
                    assigned_langs.append(chosen)
                    assigned_lower.add(chosen.lower())
            else:
                assigned_langs.append(clean_name)
                assigned_lower.add(clean_name.lower())

        # 1. Ancestry base languages
        raw_anc_langs = anc.get("languages", ["Common"])
        if isinstance(raw_anc_langs, list):
            for l in raw_anc_langs:
                add_language(l)
        else:
            add_language("Common")

        if "common" not in assigned_lower:
            add_language("Common")

        # 2. Bonus languages from positive Intelligence modifier
        int_mod = mods.get("int", 0)
        if int_mod > 0:
            for _ in range(int_mod):
                avail_pool = [l for l in COMMON_LANG_POOL if l.lower() not in assigned_lower]
                if avail_pool:
                    chosen_bonus = random.choice(avail_pool)
                    assigned_langs.append(chosen_bonus)
                    assigned_lower.add(chosen_bonus.lower())

        character_languages = assigned_langs

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
            archetype=clean_arch_input or (archetype_data["name"] if archetype_data and level >= 2 else None),
            archetype_description=clean_pf2e_text(archetype_data.get("level_2_dedication", {}).get("description", "")) if archetype_data else None,
            size=anc.get("size", "med"),
            speed=anc.get("speed", 25) + bonus_speed + bonus_speed,
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
            companion=primary_companion,
            additional_partners=extra_partners,
            feats=chosen_feats,
            languages=character_languages,
            traits=[anc["name"].lower(), cls["name"].lower()],
        )

    def level_up(
        self,
        current_char: Dict[str, Any],
        target_level: int,
        use_dedication: bool = False,
        archetype_name: Optional[str] = None
    ) -> CharacterSheet:
        target_level = max(1, min(7, int(target_level)))
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

        # 2. Extract current attributes (supporting both short and full field names)
        raw_attrs = current_char.get("attributes", {})
        attr_alias = {
            "str": ["str", "strength"],
            "dex": ["dex", "dexterity"],
            "con": ["con", "constitution"],
            "int": ["int", "intelligence"],
            "wis": ["wis", "wisdom"],
            "cha": ["cha", "charisma"]
        }
        mods = {}
        for short_name, aliases in attr_alias.items():
            val = 0
            for a in aliases:
                if a in raw_attrs:
                    val = raw_attrs[a]
                    break
            mods[short_name] = val

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
        if target_level >= 7:
            if cls["name"].lower() in ["ranger", "rogue"] and perception_rank < 3:
                perception_rank = 3
            elif cls["name"].lower() == "barbarian" and will_rank < 2:
                will_rank = 2
            elif cls["name"].lower() == "champion" and fort_rank < 3:
                fort_rank = 3

        fort_prof = self._calc_prof(fort_rank, target_level, mods["con"])
        ref_prof = self._calc_prof(ref_rank, target_level, mods["dex"])
        will_prof = self._calc_prof(will_rank, target_level, mods["wis"])
        perception_prof = self._calc_prof(perception_rank, target_level, mods["wis"])

        # 4. Equipment & Recalculated HP
        equipment_loadout, calculated_ac, shield_bonus = resolve_equipment(
            cls["name"],
            str_mod=mods["str"],
            dex_mod=mods["dex"],
            level=target_level,
            ancestry_name=anc["name"]
        )

        if target_level >= 5:
            for strike in equipment_loadout.strikes:
                extra_prof = 2
                strike.attack_bonus += extra_prof
                strike.map_second += extra_prof
                strike.map_third += extra_prof
        if target_level >= 7:
            for strike in equipment_loadout.strikes:
                # Weapon Specialization (+2 damage)
                if "+2" not in strike.damage_dice and "Weapon Spec" not in strike.damage_dice:
                    strike.damage_dice = f"{strike.damage_dice} + 2" 

        con_mod = mods["con"]
        class_hp_per_lvl = cls.get("hp_per_level", 8)
        base_hp = anc.get("hp", 8) + ((class_hp_per_lvl + con_mod) * target_level)
        bonus_speed = 0
        total_hp = max(1, base_hp)

        # 5. Resolve Archetype (respect existing choice or select new dedication on level up)
        archetype_data = None
        existing_arch_name = current_char.get("archetype")
        clean_target_arch = archetype_name.strip() if archetype_name and archetype_name.strip().lower() not in ["", "any", "any archetype", "none"] else None

        if existing_arch_name and existing_arch_name.lower() not in ["any", "any archetype", "none"]:
            archetype_data = resolve_dynamic_archetype(existing_arch_name, self.feats)
            resolved_arch_name = existing_arch_name
        elif clean_target_arch:
            archetype_data = resolve_dynamic_archetype(clean_target_arch, self.feats)
            resolved_arch_name = clean_target_arch
        elif use_dedication and target_level >= 2:
            archetype_data = pick_archetype(cls["name"], {}, mods)
            resolved_arch_name = archetype_data["name"] if archetype_data else None
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
                            action_cost=safe_action_cost(f2.get("action_cost")),
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
                    resolved_feat_name2 = resolve_feat_subchoices(sf["name"], existing_feat_names)
                    chosen_feats.append(FeatSummary(
                        id=sf["id"],
                        name=resolved_feat_name2,
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
                            action_cost=safe_action_cost(f4.get("action_cost")),
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
                    resolved_name4 = resolve_feat_subchoices(sf4["name"], existing_feat_names)
                    chosen_feats.append(FeatSummary(
                        id=sf4["id"],
                        name=resolved_name4,
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
                    skill_ranks_tmp = {s.get("name"): s.get("rank", 0) for s in current_char.get("skills", []) if isinstance(s, dict)}
                    cf6 = pick_weighted_feat(lvl6_class_feats, cls_name_lower, existing_feat_names, skill_ranks_tmp, {}, 6) or random.choice(lvl6_class_feats)
                    chosen_feats.append(FeatSummary(
                        id=cf6["id"],
                        name=cf6["name"],
                        category="Class Feat (Level 6)",
                        action_cost=safe_action_cost(cf6.get("action_cost")),
                        traits=cf6.get("traits", []),
                        description=clean_pf2e_text(cf6.get("description", ""))
                    ))
                    existing_feat_names.add(cf6["name"])

            elif lvl == 7:
                gf_pool_7 = [f for f in GENERAL_FEATS_LVL3 if f["name"] not in existing_feat_names]
                if gf_pool_7:
                    gf7 = random.choice(gf_pool_7)
                    chosen_feats.append(FeatSummary(
                        id=f"{gf7['id']}-7",
                        name=gf7["name"],
                        category="General (Level 7)",
                        action_cost=None,
                        traits=["general"],
                        description=clean_pf2e_text(gf7["description"])
                    ))
                    existing_feat_names.add(gf7["name"])

                if "Weapon Specialization" not in existing_feat_names:
                    chosen_feats.append(FeatSummary(
                        id="class-feat-weapon-specialization",
                        name="Weapon Specialization",
                        category="Class Feature (Level 7)",
                        action_cost=None,
                        traits=[cls_name_lower],
                        description="You have learned how to inflict greater injuries with your favored weapons. You deal 2 additional damage with weapons and unarmed attacks in which you are trained."
                    ))
                    existing_feat_names.add("Weapon Specialization")

                skill_ranks = {s.name: s.rank for s in (all_skills if "all_skills" in locals() else [])}
                skill_feats_6 = [
                    f for f in self.feats
                    if f.get("category") == "skill"
                    and f.get("level") in [1, 2, 4, 6]
                ]
                sf6 = pick_weighted_feat(skill_feats_6, cls["name"], existing_feat_names, skill_ranks, mods, 6)
                if sf6:
                    resolved_name6 = resolve_feat_subchoices(sf6["name"], existing_feat_names)
                    chosen_feats.append(FeatSummary(
                        id=sf6["id"],
                        name=resolved_name6,
                        category="Skill (Level 6)",
                        action_cost=sf6.get("action_cost"),
                        traits=sf6.get("traits", []),
                        description=clean_pf2e_text(sf6.get("description", ""))
                    ))
                    existing_feat_names.add(resolved_name6)

        if any(f.name.lower() == "toughness" for f in chosen_feats):
            total_hp += target_level

        # 7. Skills
        all_skills = resolve_character_skills(
            class_name=cls["name"],
            background_data=bg,
            attribute_mods=mods,
            level=target_level,
            feats=chosen_feats
        )

        # Resolve Subclass / Eidolon info before spells & focus
        raw_sub = current_char.get("subclass")
        if raw_sub and raw_sub.get("name"):
            subclass_obj = SubclassSummary(**raw_sub)
        elif current_char.get("companion") and current_char["companion"].get("name"):
            comp = current_char["companion"]
            subclass_obj = SubclassSummary(
                title="Eidolon" if cls_name_lower == "summoner" else "Companion",
                name=comp["name"],
                description=comp.get("creature_type", "")
            )
        else:
            subclass_obj = None

        sub_name = subclass_obj.name if subclass_obj else None

        # 8. Spellcasting
        spellcasting_data = resolve_spellcasting(
            class_name=cls["name"],
            attribute_mods=mods,
            level=target_level,
            subclass_name=sub_name
        )

        focus_data = resolve_focus_spells(
            class_name=cls["name"],
            feats=chosen_feats,
            attribute_mods=mods,
            subclass_name=sub_name,
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
        anc_desc = clean_pf2e_text(anc.get("description", "")) or current_char.get("ancestry_description", "")

        # Resolve Languages (de-duplicated & distinct)
        COMMON_LANG_POOL = [
            "Common", "Dwarven", "Elven", "Gnomish", "Goblin", "Halfling", 
            "Orcish", "Draconic", "Sylvan", "Undercommon", "Jotun", "Necril", 
            "Aklo", "Celestial", "Abyssal", "Infernal", "Shadowtongue", "Iruxi"
        ]

        assigned_langs = []
        assigned_lower = set()

        def add_language(lang_name: str):
            clean_name = (lang_name or "").strip().title()
            if not clean_name:
                return
            if clean_name.lower() in assigned_lower:
                # Collision: pick a distinct fallback not yet assigned
                fallback_choices = [l for l in COMMON_LANG_POOL if l.lower() not in assigned_lower]
                if fallback_choices:
                    chosen = random.choice(fallback_choices)
                    assigned_langs.append(chosen)
                    assigned_lower.add(chosen.lower())
            else:
                assigned_langs.append(clean_name)
                assigned_lower.add(clean_name.lower())

        # 1. Ancestry base languages
        raw_anc_langs = anc.get("languages", ["Common"])
        if isinstance(raw_anc_langs, list):
            for l in raw_anc_langs:
                add_language(l)
        else:
            add_language("Common")

        if "common" not in assigned_lower:
            add_language("Common")

        # 2. Bonus languages from positive Intelligence modifier
        int_mod = mods.get("int", 0)
        if int_mod > 0:
            for _ in range(int_mod):
                avail_pool = [l for l in COMMON_LANG_POOL if l.lower() not in assigned_lower]
                if avail_pool:
                    chosen_bonus = random.choice(avail_pool)
                    assigned_langs.append(chosen_bonus)
                    assigned_lower.add(chosen_bonus.lower())

        character_languages = assigned_langs

        # 7. Preserve and scale Languages on level up
        existing_langs = list(current_char.get("languages") or ["Common"])
        lang_set_lower = {l.lower() for l in existing_langs}
        old_int = raw_attrs.get("int", raw_attrs.get("intelligence", 0))
        new_int = mods.get("int", 0)

        COMMON_LANG_POOL = [
            "Common", "Dwarven", "Elven", "Gnomish", "Goblin", "Halfling", 
            "Orcish", "Draconic", "Sylvan", "Undercommon", "Jotun", "Necril", 
            "Aklo", "Celestial", "Abyssal", "Infernal", "Shadowtongue", "Iruxi"
        ]

        if new_int > old_int:
            gained = new_int - old_int
            for _ in range(gained):
                available = [l for l in COMMON_LANG_POOL if l.lower() not in lang_set_lower]
                if available:
                    chosen = random.choice(available)
                    existing_langs.append(chosen)
                    lang_set_lower.add(chosen.lower())
        char_languages = existing_langs

        # Carry over companion and additional partners across level up
        existing_companion = companion_data

        raw_extra_partners = current_char.get("additional_partners") or []
        existing_extra_partners = [
            PartnerCreatureData(**scale_existing_companion(p, old_level, target_level, total_hp)) if isinstance(p, dict)
            else p
            for p in raw_extra_partners
        ]

        # Check if a newly gained archetype unlocks an additional companion at level 2+
        all_partner_types = [
            (existing_companion.creature_type or "").lower() if existing_companion else ""
        ] + [
            (p.creature_type or "").lower() for p in existing_extra_partners
        ]

        arch_str = (resolved_arch_name or "").lower()
        if old_level < 2 and target_level >= 2:
            if "beastmaster" in arch_str and not any("animal" in t or "companion" in t for t in all_partner_types):
                new_partner = resolve_companion(
                    class_name=cls["name"],
                    feats=chosen_feats,
                    archetype=resolved_arch_name,
                    level=target_level
                )
                if new_partner:
                    if not existing_companion:
                        existing_companion = new_partner
                    else:
                        existing_extra_partners.append(new_partner)
            elif "undead master" in arch_str and not any("undead" in t for t in all_partner_types):
                new_partner = resolve_undead_companion(level=target_level)
                if new_partner:
                    if not existing_companion:
                        existing_companion = new_partner
                    else:
                        existing_extra_partners.append(new_partner)

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
            companion=existing_companion,
            additional_partners=existing_extra_partners,
            feats=chosen_feats,
            languages=char_languages,
            traits=current_char.get("traits", [anc["name"].lower(), cls["name"].lower()]),
        )