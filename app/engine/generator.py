
ANCESTRY_BG_MAP = {
    "dwarf": ["dwarf", "dwarven"],
    "elf": ["elf", "elven"],
    "gnome": ["gnome", "gnomish"],
    "goblin": ["goblin"],
    "halfling": ["halfling"],
    "human": ["human"],
    "orc": ["orc", "orcish"],
    "kobold": ["kobold"],
    "leshy": ["leshy"],
    "kashrishi": ["kashrishi"],
    "catfolk": ["catfolk", "amurrun"],
    "lizardfolk": ["lizardfolk", "iruxi"],
    "ratfolk": ["ratfolk", "ysoki"],
    "tengu": ["tengu"],
    "anadi": ["anadi"],
    "automaton": ["automaton"],
    "conrasu": ["conrasu"],
    "fetchling": ["fetchling"],
    "fleshwarp": ["fleshwarp"],
    "goloma": ["goloma"],
    "grippli": ["grippli"],
    "poppet": ["poppet"],
    "shisk": ["shisk"],
    "shoony": ["shoony"],
    "skeleton": ["skeleton"],
    "strix": ["strix"],
    "vanara": ["vanara"],
    "vishkanya": ["vishkanya"],
    "nagaji": ["nagaji"]
}

def is_background_compatible_with_ancestry(bg_data: dict, ancestry_name: str) -> bool:
    anc_lower = ancestry_name.lower()
    bg_name = bg_data.get("name", "").lower()
    bg_lore = bg_data.get("trained_lore", "").lower()
    name_words = [w.strip("(),.-") for w in bg_name.split()]

    bg_restricted_ancestry = None
    for target_anc, aliases in ANCESTRY_BG_MAP.items():
        for alias in aliases:
            if f"{alias} lore" in bg_lore or alias in name_words:
                bg_restricted_ancestry = target_anc
                break
        if bg_restricted_ancestry:
            break

    # If background is universal, it is always compatible
    if not bg_restricted_ancestry:
        return True

    # If restricted, the character's ancestry must match
    for alias in ANCESTRY_BG_MAP.get(bg_restricted_ancestry, [bg_restricted_ancestry]):
        if alias in anc_lower:
            return True

    return False

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
    Strike,
)
from app.engine.names import generate_ancestry_name
from app.engine.equipment import resolve_equipment
from app.engine.skills import resolve_character_skills
from app.engine.feat_prereqs import check_feat_prerequisites, calculate_feat_weight, extract_gate_elements, is_kineticist_feat_allowed
from app.engine.spells import resolve_spellcasting
from app.engine.focus import resolve_focus_spells
from app.engine.subclasses import resolve_heritage, resolve_subclass, BARBARIAN_ANIMAL_CHOICES
from app.engine.archetypes import pick_archetype, ARCHETYPES_CATALOG, resolve_dynamic_archetype
from app.engine.companions import resolve_companion
from app.engine.eidolons import resolve_eidolon
from app.engine.familiars import resolve_familiar
from app.engine.constructs_undead import resolve_construct_companion, resolve_undead_companion
from app.engine.plants_familiars_summons import resolve_plant_companion, resolve_specific_familiar


def get_sneak_attack_dice(level: int, is_archetype: bool = False) -> str:
    if is_archetype:
        return "2d6" if level >= 6 else "1d6"
    return "3d6" if level >= 11 else ("2d6" if level >= 5 else "1d6")

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

ARCHETYPE_GRANTED_FEATURES = {
    "Rogue Dedication": FeatSummary(
        id="feat-archetype-surprise-attack",
        name="Surprise Attack",
        category="Archetype Feature",
        action_cost=None,
        traits=["archetype", "rogue"],
        description="You act or spring into combat before your foes are ready. On the first round of combat, if you roll Deception or Stealth for initiative, any creatures that haven't acted yet are off-guard to you."
    ),
    "Ranger Dedication": FeatSummary(
        id="feat-archetype-hunt-prey",
        name="Hunt Prey",
        category="Archetype Feature",
        action_cost=1,
        traits=["archetype", "concentrate", "ranger"],
        description="Designate a creature you can see or track as your prey. You gain a +2 circumstance bonus to Perception checks to Seek or Sense Motive against it, and a +2 circumstance bonus to Survival checks to Track it. You also ignore the second range increment penalty on ranged attacks against your prey."
    ),
    "Investigator Dedication": FeatSummary(
        id="feat-archetype-devise-a-stratagem",
        name="Devise a Stratagem",
        category="Archetype Feature",
        action_cost=1,
        traits=["archetype", "concentrate", "fortune", "investigator"],
        description="Roll a d20. You must use that result for the attack roll of your next Strike this round against the designated creature, substituting your Intelligence modifier for your Strength or Dexterity modifier on the attack roll."
    )
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


def strip_foundry_tags(val: str) -> str:
    if not isinstance(val, str):
        return val
    cleaned = re.sub(r'@UUID\[[^\]]+\]\{([^}]+)\}', r'\1', val)
    cleaned = re.sub(r'@UUID\[[^\]]+\]', '', cleaned)
    cleaned = re.sub(r'@Compendium\[[^\]]+\]\{([^}]+)\}', r'\1', cleaned)
    cleaned = re.sub(r'@Compendium\[[^\]]+\]', '', cleaned)
    return cleaned.strip()


def safe_action_cost(val):
    if val is None:
        return None
    if isinstance(val, int):
        return val
    if isinstance(val, str):
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
    comp = dict(companion_data)
    level_delta = target_level - old_level
    if level_delta <= 0:
        return comp

    creature_type = (comp.get("creature_type") or "").lower()

    if "eidolon" in creature_type:
        comp["hp"] = master_hp
    else:
        comp["hp"] = comp.get("hp", 20) + (level_delta * 8)

    stage_bump = 2 if (old_level < 4 and target_level >= 4 and "eidolon" not in creature_type) else 0
    total_stat_boost = level_delta + stage_bump
    comp["ac"] = comp.get("ac", 16) + total_stat_boost
    comp["fortitude"] = comp.get("fortitude", 5) + total_stat_boost
    comp["reflex"] = comp.get("reflex", 5) + total_stat_boost
    comp["will"] = comp.get("will", 5) + total_stat_boost
    comp["perception"] = comp.get("perception", 4) + total_stat_boost

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

    if "additional lore" in fn_lower and "(" not in feat_name:
        lore_pool = [
            "Academia Lore", "Architecture Lore", "Art Lore", "Barrow Lore",
            "Circus Lore", "Engineering Lore", "Forest Lore", "Fortune-Telling Lore",
            "Guild Lore", "Heraldry Lore", "Hunting Lore", "Labor Lore",
            "Legal Lore", "Midwifery Lore", "Mining Lore", "Ocean Lore",
            "Politics Lore", "Sailing Lore", "Scouting Lore", "Settlement Lore",
            "Theatre Lore", "Underworld Lore", "Warfare Lore"
        ]
        chosen = random.choice(lore_pool)
        return f"{feat_name} ({chosen})"

    return feat_name


def enrich_feat_description(feat_name: str, raw_desc: str) -> str:
    cleaned = clean_pf2e_text(raw_desc or "")
    if "(" in feat_name and ")" in feat_name:
        subchoice = feat_name.split("(", 1)[1].rstrip(")")
        if "additional lore" in feat_name.lower():
            prefix = f"Chosen Lore: {subchoice}. (Scales automatically: Trained at 1st, Expert at 3rd, Master at 7th, Legendary at 15th).\n\n"
            return prefix + cleaned
        elif "spotter" in feat_name.lower() or "stalker" in feat_name.lower():
            prefix = f"Selected Environment: {subchoice}.\n\n"
            return prefix + cleaned
    return cleaned


def pick_weighted_feat(candidates, class_name, owned_names, skill_ranks, mods, char_level):
    valid = [
        f for f in candidates
        if f["name"] not in owned_names
        and check_feat_prerequisites(f, skill_ranks, owned_names, mods, char_level)
    ]
    if not valid:
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


def extract_bg_feat(bg_desc: str, feats_list: list) -> str:
    if not bg_desc:
        return ""
    feat_lookup = {f["name"].lower(): f["name"] for f in feats_list}
    m_uuid = re.search(r"@UUID\[[^\]]*feats-srd\.Item\.([^|\]]+)", bg_desc) or re.search(r"@UUID\[[^\]]*Item\.([^|\]]+)", bg_desc)
    if m_uuid:
        c_name = m_uuid.group(1).strip()
        if c_name.lower() in feat_lookup:
            return feat_lookup[c_name.lower()]
        return c_name
    m_choice = re.search(r"either\s+([A-Za-z\s'’\-]+?)\s+or\s+([A-Za-z\s'’\-]+?)\s+(?:skill|general)?\s*feat", bg_desc, re.IGNORECASE)
    if m_choice:
        opt1, opt2 = m_choice.group(1).strip(), m_choice.group(2).strip()
        valid = [feat_lookup[opt.lower()] for opt in [opt1, opt2] if opt.lower() in feat_lookup]
        if valid:
            return random.choice(valid)
    m_gain = re.search(r"gain the\s+([A-Za-z\s'’\-]+?)\s+(?:skill|general)?\s*feat", bg_desc, re.IGNORECASE)
    if m_gain:
        cand = m_gain.group(1).strip()
        if cand.lower() in feat_lookup:
            return feat_lookup[cand.lower()]
        return cand
    desc_l = bg_desc.lower()
    for f_low, f_real in feat_lookup.items():
        if len(f_low) > 4 and f" {f_low} " in f" {desc_l} ":
            idx = desc_l.find(f_low)
            if "feat" in desc_l[idx:idx + 50]:
                return f_real
    return ""


class PF2eGenerator:
    def __init__(self):
        self.ancestries = {a["name"].lower(): a for a in load_data("ancestries.json")}
        self.classes = {c["name"].lower(): c for c in load_data("classes.json")}
        self.backgrounds = {b["name"].lower(): b for b in load_data("backgrounds.json")}
        raw_feats = load_data("feats.json")
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
        use_dedication: bool = False,
        heritage_name: Optional[str] = None,
        subclass_name: Optional[str] = None
    ) -> CharacterSheet:
        level = max(1, min(8, int(level)))

        if ancestry_name and ancestry_name.lower() in self.ancestries:
            anc = self.ancestries[ancestry_name.lower()]
        else:
            anc = random.choice(list(self.ancestries.values()))

        if class_name and class_name.lower() in self.classes:
            cls = self.classes[class_name.lower()]
            cls_name_lower = (cls["name"] if isinstance(cls, dict) else str(cls)).lower()
        else:
            cls = random.choice(list(self.classes.values()))
            cls_name_lower = (cls["name"] if isinstance(cls, dict) else str(cls)).lower()

        if background_name and background_name.strip():
            matched_bg = next((b for b in self.backgrounds.values() if b["name"].lower() == background_name.strip().lower()), None)
            bg = matched_bg if matched_bg else random.choice(list(self.backgrounds.values()))
        else:
            char_anc_name = anc.get("name", "") if isinstance(anc, dict) else getattr(anc, "name", "")
            eligible_bgs = [
                b for b in self.backgrounds.values()
                if is_background_compatible_with_ancestry(b, char_anc_name)
            ]
            bg = random.choice(eligible_bgs) if eligible_bgs else random.choice(list(self.backgrounds.values()))

        if heritage_name and str(heritage_name).strip() and str(heritage_name).strip().lower() not in ["none", ""]:
            heritage_data = {"name": str(heritage_name).strip(), "description": ""}
        else:
            heritage_data = resolve_heritage(anc["name"])

        cls_name_lower = cls["name"].lower()
        if subclass_name and str(subclass_name).strip() and str(subclass_name).strip().lower() not in ["none", ""]:
            subclass_data = {"name": str(subclass_name).strip(), "title": "Subclass", "description": ""}
        else:
            subclass_data = resolve_subclass(cls["name"])

        sub_n_val = subclass_data.get("name", "") if isinstance(subclass_data, dict) else getattr(subclass_data, "name", "")
        gate_elements = extract_gate_elements(sub_n_val) if cls_name_lower == "kineticist" else set()
        

        resolved_name = char_name.strip() if char_name and char_name.strip() else generate_ancestry_name(anc["name"])
        raw_arch = archetype_name.strip() if archetype_name and archetype_name.strip() else ""
        if raw_arch.lower() in ["", "any", "any archetype", "none", "random"]:
            clean_arch_input = None
        else:
            clean_arch_input = raw_arch

        archetype_data = None
        if clean_arch_input:
            archetype_data = resolve_dynamic_archetype(clean_arch_input, self.feats)

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

        if not archetype_data and use_dedication and level >= 2:
            archetype_data = pick_archetype(cls["name"], {}, mods, getattr(self, "feats", None))

        if level >= 5:
            lvl5_boosts_applied: Set[str] = set()
            lvl5_priority = [key_attr, "con", "dex", "wis", "str", "int", "cha"]
            for attr in lvl5_priority:
                if len(lvl5_boosts_applied) < 4 and attr not in lvl5_boosts_applied:
                    mods[attr] += 1
                    lvl5_boosts_applied.add(attr)

        fort_rank = cls.get("saving_throws", {}).get("fortitude", 1)
        ref_rank = cls.get("saving_throws", {}).get("reflex", 1)
        will_rank = cls.get("saving_throws", {}).get("will", 1)
        perception_rank = cls.get("perception", 1)

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

        sub_n = subclass_data["name"] if subclass_data else ""
        arch_n = clean_arch_input or (archetype_data["name"] if archetype_data else "")

        equipment_loadout, calculated_ac, shield_bonus = resolve_equipment(
            cls["name"],
            str_mod=mods["str"],
            dex_mod=mods["dex"],
            level=level,
            ancestry_name=anc["name"],
            subclass_name=sub_n,
            archetype_name=arch_n,
        )

        # Inject Barbarian Animal Instinct Bestial Strike
        if cls["name"].lower() == "barbarian" and subclass_data:
            sub_name = subclass_data.get("name", "")
            if "Animal Instinct" in sub_name:
                matched_animal = None
                for a in BARBARIAN_ANIMAL_CHOICES:
                    if f"({a['name']})" in sub_name or a['name'].lower() in sub_name.lower():
                        matched_animal = a
                        break

                if matched_animal:
                    unarmed_prof = 2
                    s_mod = mods.get("str", 4) if "mods" in locals() and isinstance(mods, dict) else 4
                    unarmed_attack_bonus = level + unarmed_prof + s_mod

                    dice_count = 2 if level >= 4 else 1
                    die_size = matched_animal["die"].replace("1", "", 1)
                    damage_dice_str = f"{dice_count}{die_size}"

                    rage_dmg = 2 if level < 7 else 6
                    damage_str = f"{damage_dice_str} + {s_mod} (+{rage_dmg} Rage)"

                    strike_name = f"{matched_animal['strike']} ({matched_animal['name']} Rage Strike)"
                    traits_list = list(matched_animal["traits"]) + ["rage"]

                    # Agile MAP is -4/-8; standard is -5/-10
                    is_agile = "agile" in traits_list
                    map2_val = unarmed_attack_bonus - (4 if is_agile else 5)
                    map3_val = unarmed_attack_bonus - (8 if is_agile else 10)

                    map_second = f"+{map2_val}" if map2_val >= 0 else str(map2_val)
                    map_third = f"+{map3_val}" if map3_val >= 0 else str(map3_val)

                    animal_strike = Strike(
                        name=strike_name,
                        attack_bonus=f"+{unarmed_attack_bonus}",
                        map_second=map_second,
                        map_third=map_third,
                        damage_dice=damage_dice_str,
                        damage=damage_str,
                        damage_type=matched_animal["type"],
                        traits=traits_list
                    )
                    equipment_loadout.strikes.insert(0, animal_strike)

        if level >= 5:
            for strike in equipment_loadout.strikes:
                extra_prof = 2
                strike.attack_bonus += extra_prof
                strike.map_second += extra_prof
                strike.map_third += extra_prof
        if level >= 7:
            for strike in equipment_loadout.strikes:
                if "+2" not in strike.damage_dice and "Weapon Spec" not in strike.damage_dice:
                    strike.damage_dice = f"{strike.damage_dice} + 2" 

        con_mod = mods["con"]
        class_hp_per_lvl = cls.get("hp_per_level", 8)
        base_hp = anc.get("hp", 8) + ((class_hp_per_lvl + con_mod) * level)
        bonus_speed = 0

        if cls["name"].lower() == "kineticist":
            blast_lvl = level
            prof = 2 + blast_lvl
            if blast_lvl >= 5:
                prof += 2
            melee_bonus = prof + mods.get("con", 0)
            ranged_bonus = prof + mods.get("dex", 0)
            dice_count = 2 if blast_lvl >= 5 else 1
            melee_str_bonus = mods.get("str", 0) if mods.get("str", 0) > 0 else 0
            spec_bonus = 2 if blast_lvl >= 7 else 0
            melee_dmg_bonus = mods.get("con", 0) + melee_str_bonus + spec_bonus
            ranged_dmg_bonus = mods.get("con", 0) + spec_bonus
            melee_dmg_str = f"{dice_count}d8+{melee_dmg_bonus}" if melee_dmg_bonus > 0 else f"{dice_count}d8"
            ranged_dmg_str = f"{dice_count}d6+{ranged_dmg_bonus}" if ranged_dmg_bonus > 0 else f"{dice_count}d6"
            melee_blast = Strike(
                name="Elemental Blast (Melee)",
                attack_bonus=melee_bonus,
                map_second=melee_bonus - 5,
                map_third=melee_bonus - 10,
                damage_dice=melee_dmg_str,
                damage_type="Bludgeoning / Piercing / Slashing",
                traits=["Impulse", "Kinetic", "Magical", "Primal"]
            )
            ranged_blast = Strike(
                name="Elemental Blast (Ranged)",
                attack_bonus=ranged_bonus,
                map_second=ranged_bonus - 5,
                map_third=ranged_bonus - 10,
                damage_dice=ranged_dmg_str,
                damage_type="Bludgeoning / Piercing / Slashing (60 ft)",
                traits=["Impulse", "Infusion", "Kinetic", "Magical", "Primal"]
            )
            equipment_loadout.strikes = [s for s in equipment_loadout.strikes if not s.name.startswith("Elemental Blast")]
            equipment_loadout.strikes.insert(0, ranged_blast)
            equipment_loadout.strikes.insert(0, melee_blast)

        total_hp = max(1, base_hp)

        cls_name_lower = cls["name"].lower()
        gate_elements = set()
        chosen_feats: List[FeatSummary] = []
        bg_desc = bg.get("description", "")
        bg_feat_name = extract_bg_feat(bg_desc, self.feats)

        if bg_feat_name:
            chosen_feats.append(FeatSummary(
                id=f"feat-bg-{bg_feat_name.lower().replace(' ', '-')}",
                name=bg_feat_name,
                category="Background Feat",
                action_cost=None,
                traits=["General", "Skill"],
                description=f"Granted by the {bg['name']} background."
            ))

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

        if subclass_data:
            chosen_feats.append(FeatSummary(
                id=f"subclass-{cls['name'].lower()}",
                name=f"{subclass_data['title']}: {subclass_data['name']}",
                category="Class Feature",
                action_cost=None,
                traits=[cls['name'].lower()],
                description=clean_pf2e_text(subclass_data["description"])
            ))

        if cls_name_lower in CLASS_FEATURES_LVL1:
            base_cf1 = CLASS_FEATURES_LVL1[cls_name_lower]
            s_dice = get_sneak_attack_dice(level, is_archetype=False)
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

        lvl1_feats = [
            f for f in self.feats
            if f.get("category") == "class"
            and f.get("level") == 1
            and cls_name_lower in [t.lower() for t in f.get("traits", [])]
            and (cls_name_lower != "kineticist" or is_kineticist_feat_allowed(f, gate_elements))
        ]
        if lvl1_feats:
            f1 = pick_weighted_feat(lvl1_feats, cls["name"], {f.name for f in chosen_feats}, {}, mods, 1) or random.choice(lvl1_feats)
            chosen_feats.append(FeatSummary(
                id=f1["id"],
                name=f1["name"],
                category="Class (Level 1)",
                action_cost=safe_action_cost(f1.get("action_cost")),
                traits=f1.get("traits", []),
                description=clean_pf2e_text(f1.get("description", ""))
            ))

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
                if ded["name"] in ARCHETYPE_GRANTED_FEATURES:
                    chosen_feats.append(ARCHETYPE_GRANTED_FEATURES[ded["name"]])
            else:
                lvl2_feats = [
                    f for f in self.feats
                    if f.get("category") == "class"
                    and f.get("level") == 2
                    and cls_name_lower in [t.lower() for t in f.get("traits", [])]
                    and (cls_name_lower != "kineticist" or is_kineticist_feat_allowed(f, gate_elements))
                ]
                if lvl2_feats:
                    f2 = pick_weighted_feat(lvl2_feats, cls["name"], {f.name for f in chosen_feats}, {}, mods, 2) or random.choice(lvl2_feats)
                    chosen_feats.append(FeatSummary(
                        id=f2["id"],
                        name=f2["name"],
                        category="Class (Level 2)",
                        action_cost=safe_action_cost(f2.get("action_cost")),
                        traits=f2.get("traits", []),
                        description=clean_pf2e_text(f2.get("description", ""))
                    ))

            owned_names = {f.name for f in chosen_feats}
            skill_feats_2 = [f for f in self.feats if f.get("category") == "skill" and f.get("level") in [1, 2]]
            sf = pick_weighted_feat(skill_feats_2, cls["name"], owned_names, {}, mods, 2)
            if sf:
                resolved_feat_name2 = resolve_feat_subchoices(sf["name"], owned_names)
                chosen_feats.append(FeatSummary(
                    id=sf["id"],
                    name=resolved_feat_name2,
                    category="Skill (Level 2)",
                    action_cost=sf.get("action_cost"),
                    traits=sf.get("traits", []),
                    description=enrich_feat_description(resolved_feat_name2, sf.get("description", ""))
                ))
                owned_names.add(resolved_feat_name2)

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
                if avail_anc_feats:
                    sub_f = random.choice(avail_anc_feats)
                    gf_name = f"Ancestral Paragon: {sub_f['name']}"
                    gf_desc = f"Selected 1st-level Ancestry Feat: {sub_f['name']}. You gain a 1st-level ancestry feat.\n\n[{sub_f['name']}]: {clean_pf2e_text(sub_f.get('description', ''))}"

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
                    and (cls_name_lower != "kineticist" or is_kineticist_feat_allowed(f, gate_elements))
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
                    description=enrich_feat_description(resolved_name4, sf4.get("description", ""))
                ))

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

        if level >= 6:
            lvl6_class_feats = [
                f for f in self.feats
                if f.get("category") == "class"
                and f.get("level") in (4, 6)
                and cls_name_lower in [t.lower() for t in f.get("traits", [])]
                and (cls_name_lower != "kineticist" or is_kineticist_feat_allowed(f, gate_elements))
            ]
            if lvl6_class_feats:
                cf6 = pick_weighted_feat(lvl6_class_feats, cls["name"], {f.name for f in chosen_feats}, {}, mods, 6) or random.choice(lvl6_class_feats)
                chosen_feats.append(FeatSummary(
                    id=cf6["id"],
                    name=cf6["name"],
                    category="Class Feat (Level 6)",
                    action_cost=safe_action_cost(cf6.get("action_cost")),
                    traits=cf6.get("traits", []),
                    description=clean_pf2e_text(cf6.get("description", ""))
                ))

            owned_names = {f.name for f in chosen_feats}
            skill_feats_6 = [
                f for f in self.feats
                if f.get("category") == "skill"
                and f.get("level") in [1, 2, 4, 6]
            ]
            sf6 = pick_weighted_feat(skill_feats_6, cls["name"], owned_names, {}, mods, 6)
            if sf6:
                resolved_name6 = resolve_feat_subchoices(sf6["name"], owned_names)
                chosen_feats.append(FeatSummary(
                    id=sf6["id"],
                    name=resolved_name6,
                    category="Skill (Level 6)",
                    action_cost=sf6.get("action_cost"),
                    traits=sf6.get("traits", []),
                    description=enrich_feat_description(resolved_name6, sf6.get("description", ""))
                ))
                owned_names.add(resolved_name6)

        if level >= 7:
            owned_names = {f.name for f in chosen_feats}
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

        
        if level >= 8:
            owned_names = {f.name for f in chosen_feats}
            arch_feats_8 = []
            if archetype_data:
                arch_feats_8 = [f for f in archetype_data.get("level_8_feats", []) if f["name"] not in owned_names]

            if arch_feats_8 and random.random() < 0.6:
                af8 = random.choice(arch_feats_8)
                chosen_feats.append(FeatSummary(
                    id=af8["id"],
                    name=af8["name"],
                    category=f"Archetype Feat (Level 8 - {archetype_data['name']})",
                    action_cost=None,
                    traits=["archetype"],
                    description=clean_pf2e_text(af8["description"])
                ))
            else:
                lvl8_class_feats = [
                    f for f in self.feats
                    if f.get("category") == "class"
                    and f.get("level") in (6, 8)
                    and cls_name_lower in [t.lower() for t in f.get("traits", [])]
                    and f["name"] not in owned_names
                ]
                if lvl8_class_feats:
                    cf8 = random.choice(lvl8_class_feats)
                    chosen_feats.append(FeatSummary(
                        id=cf8["id"],
                        name=cf8["name"],
                        category="Class Feat (Level 8)",
                        action_cost=None,
                        traits=[cls_name_lower],
                        description=clean_pf2e_text(cf8["description"])
                    ))

        planned_arch = archetype_name.strip() if archetype_name and archetype_name.strip() else None
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

        collected_partners = []
        arch_name = archetype_data["name"].lower() if archetype_data else ""
        all_feat_str = " ".join([f.name.lower() for f in chosen_feats])

        if cls_name_lower == "summoner":
            sub_type = subclass_data.get("name", "") if isinstance(subclass_data, dict) else getattr(subclass_data, "name", "")
            eidolon_partner = resolve_eidolon(master_hp=total_hp, level=level, eidolon_type=sub_type)
            collected_partners.append(eidolon_partner)
            # Ensure character subclass matches the resolved eidolon partner exactly
            if eidolon_partner:
                # Extract specific subtype from partner (e.g., "Dragon Eidolon", "Anger Phantom Eidolon")
                e_type = getattr(eidolon_partner, "creature_type", "")
                if not e_type or e_type == "Eidolon":
                    e_type = getattr(eidolon_partner, "stage", "Eidolon")
                subclass_data = {"name": e_type, "title": "Eidolon", "description": f"{e_type} tactical partner"}
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

        sub_name = subclass_data["name"] if subclass_data else None
        spellcasting_data = resolve_spellcasting(
            class_name=cls["name"],
            attribute_mods=mods,
            level=level,
            subclass_name=sub_name
        )

        focus_data = resolve_focus_spells(
            class_name=cls["name"],
            feats=chosen_feats,
            attribute_mods=mods,
            subclass_name=sub_name,
            level=level
        )

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
                fallback_choices = [l for l in COMMON_LANG_POOL if l.lower() not in assigned_lower]
                if fallback_choices:
                    chosen = random.choice(fallback_choices)
                    assigned_langs.append(chosen)
                    assigned_lower.add(chosen.lower())
            else:
                assigned_langs.append(clean_name)
                assigned_lower.add(clean_name.lower())

        raw_anc_langs = anc.get("languages", ["Common"])
        if isinstance(raw_anc_langs, list):
            for l in raw_anc_langs:
                add_language(l)
        else:
            add_language("Common")

        if "common" not in assigned_lower:
            add_language("Common")

        int_mod = mods.get("int", 0)
        if int_mod > 0:
            for _ in range(int_mod):
                avail_pool = [l for l in COMMON_LANG_POOL if l.lower() not in assigned_lower]
                if avail_pool:
                    chosen_bonus = random.choice(avail_pool)
                    assigned_langs.append(chosen_bonus)
                    assigned_lower.add(chosen_bonus.lower())

        character_languages = assigned_langs


        # Annotate strikes with Sneak Attack precision damage if feature is present
        has_sneak = any("sneak attack" in f.name.lower() or "sneak attacker" in f.name.lower() for f in chosen_feats)
        if has_sneak:
            is_arch_sneak = any("sneak attacker" in f.name.lower() for f in chosen_feats) and cls_name_lower != "rogue"
            s_dice_val = get_sneak_attack_dice(level if "level" in locals() else target_level, is_archetype=is_arch_sneak)
            for st in equipment_loadout.strikes:
                if "precision" not in st.damage_dice.lower() and "sneak" not in st.damage_dice.lower():
                    st.damage_dice = f"{st.damage_dice} (+{s_dice_val} precision vs off-guard)"

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
            speed=anc.get("speed", 25) + bonus_speed,
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
        target_level = max(1, min(8, int(target_level)))
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
        cls_name_lower = (cls["name"] if isinstance(cls, dict) else str(cls)).lower()
        bg = self.backgrounds.get(bg_name) or next(
            (b for b in self.backgrounds.values() if b["name"].lower() == bg_name),
            list(self.backgrounds.values())[0]
        )
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
        elif old_level >= 5 and target_level < 5:
            # De-escalate level 5 boosts
            lvl5_boosts_applied: Set[str] = set()
            lvl5_priority = [key_attr, "con", "dex", "wis", "str", "int", "cha"]
            for attr in lvl5_priority:
                if len(lvl5_boosts_applied) < 4 and attr not in lvl5_boosts_applied:
                    mods[attr] = max(0, mods[attr] - 1)
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

        # 4. Equipment & Weapons Locking
        current_sub = (current_char.get("subclass") or {}).get("name", "") if isinstance(current_char.get("subclass"), dict) else ""
        gate_elements = extract_gate_elements(current_sub) if cls_name_lower == "kineticist" else set()
        current_arch = current_char.get("archetype") or ""
        equipment_loadout, calculated_ac, shield_bonus = resolve_equipment(
            cls["name"],
            str_mod=mods["str"],
            dex_mod=mods["dex"],
            level=target_level,
            ancestry_name=anc["name"],
            subclass_name=current_sub,
            archetype_name=current_arch
        )

        # Preserve and scale equipped strikes instead of re-rolling random weapons
        raw_eq = current_char.get("equipment")
        if isinstance(raw_eq, dict):
            raw_strikes = raw_eq.get("strikes")
        elif hasattr(raw_eq, "strikes"):
            raw_strikes = raw_eq.strikes
        else:
            raw_strikes = current_char.get("strikes") or current_char.get("weapons")

        if raw_strikes:
            preserved_strikes = []
            for s in raw_strikes:
                s_dict = s if isinstance(s, dict) else (s.__dict__ if hasattr(s, "__dict__") else {})
                name = s_dict.get("name", "")
                if not name or name.startswith("Elemental Blast"):
                    continue

                is_ranged = "ranged" in name.lower() or "bow" in name.lower() or "crossbow" in name.lower()
                ab_mod = mods.get("dex" if is_ranged else "str", 0)

                base_prof_rank = 4 if cls["name"].lower() == "fighter" else 2
                if target_level >= 5 and cls["name"].lower() in ["fighter", "gunslinger"]:
                    base_prof_rank = 6

                item_bonus = 1 if target_level >= 2 else 0
                new_atk = base_prof_rank + target_level + ab_mod + item_bonus

                # Strip existing rune prefixes to recover clean base weapon name
                clean_name = re.sub(r"^(\+?\d+\s+)?(striking\s+)?", "", name, flags=re.I).strip()
                if target_level >= 4:
                    display_name = f"+1 Striking {clean_name}"
                elif target_level >= 2:
                    display_name = f"+1 {clean_name}"
                else:
                    display_name = clean_name

                # Extract base die type (e.g. d6, d8, d10) and any modifier suffix
                raw_dice = s_dict.get("damage_dice", "1d8")
                # Remove previous weapon spec or extra spaces
                raw_dice = re.sub(r"\s*\+\s*2", "", raw_dice).strip()
                m_die = re.search(r"(\d*)d(\d+)(.*)", raw_dice)
                if m_die:
                    die_faces = m_die.group(2)
                    tail = m_die.group(3).strip()
                    dice_count = 2 if target_level >= 4 else 1
                    base_str = f"{dice_count}d{die_faces}{(" " + tail) if tail else ""}"
                else:
                    base_str = raw_dice

                if target_level >= 7:
                    dmg_dice = f"{base_str} + 2"
                else:
                    dmg_dice = base_str

                preserved_strikes.append(Strike(
                    name=display_name,
                    attack_bonus=new_atk,
                    map_second=new_atk - (4 if "Agile" in s_dict.get("traits", []) else 5),
                    map_third=new_atk - (8 if "Agile" in s_dict.get("traits", []) else 10),
                    damage_dice=dmg_dice,
                    damage_type=s_dict.get("damage_type", "Physical"),
                    traits=s_dict.get("traits", [])
                ))

            if preserved_strikes:
                equipment_loadout.strikes = preserved_strikes

        con_mod = mods["con"]
        class_hp_per_lvl = cls.get("hp_per_level", 8)
        base_hp = anc.get("hp", 8) + ((class_hp_per_lvl + con_mod) * target_level)

        # Kineticist Elemental Blasts
        if cls["name"].lower() == "kineticist":
            blast_lvl = target_level
            prof = 2 + blast_lvl
            if blast_lvl >= 5:
                prof += 2

            melee_bonus = prof + mods.get("con", 0)
            ranged_bonus = prof + mods.get("dex", 0)

            dice_count = 2 if blast_lvl >= 5 else 1
            melee_str_bonus = mods.get("str", 0) if mods.get("str", 0) > 0 else 0
            spec_bonus = 2 if blast_lvl >= 7 else 0

            melee_dmg_bonus = mods.get("con", 0) + melee_str_bonus + spec_bonus
            ranged_dmg_bonus = mods.get("con", 0) + spec_bonus

            melee_dmg_str = f"{dice_count}d8+{melee_dmg_bonus}" if melee_dmg_bonus > 0 else f"{dice_count}d8"
            ranged_dmg_str = f"{dice_count}d6+{ranged_dmg_bonus}" if ranged_dmg_bonus > 0 else f"{dice_count}d6"

            melee_blast = Strike(
                name="Elemental Blast (Melee)",
                attack_bonus=melee_bonus,
                map_second=melee_bonus - 5,
                map_third=melee_bonus - 10,
                damage_dice=melee_dmg_str,
                damage_type="Bludgeoning / Piercing / Slashing",
                traits=["Impulse", "Kinetic", "Magical", "Primal"]
            )
            ranged_blast = Strike(
                name="Elemental Blast (Ranged)",
                attack_bonus=ranged_bonus,
                map_second=ranged_bonus - 5,
                map_third=ranged_bonus - 10,
                damage_dice=ranged_dmg_str,
                damage_type="Bludgeoning / Piercing / Slashing (60 ft)",
                traits=["Impulse", "Infusion", "Kinetic", "Magical", "Primal"]
            )
            equipment_loadout.strikes = [s for s in equipment_loadout.strikes if not s.name.startswith("Elemental Blast")]
            equipment_loadout.strikes.insert(0, ranged_blast)
            equipment_loadout.strikes.insert(0, melee_blast)

        total_hp = max(1, base_hp)

        # 5. Resolve Archetype
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
            archetype_data = pick_archetype(cls["name"], {}, mods, getattr(self, "feats", None))
            resolved_arch_name = archetype_data["name"] if archetype_data else None
        else:
            resolved_arch_name = None

        # 6. Preserve and advance/trim feats
        existing_feats_raw = current_char.get("feats", [])
        chosen_feats: List[FeatSummary] = [FeatSummary(**f) if isinstance(f, dict) else f for f in existing_feats_raw]

        if target_level < old_level:
            # Leveling down: filter out feats from levels above target_level
            filtered_feats = []
            for f in chosen_feats:
                cat = (f.category or "").lower()
                m = re.search(r"level\s*(\d+)", cat)
                if m:
                    f_lvl = int(m.group(1))
                    if f_lvl > target_level:
                        continue
                if target_level < 7 and f.name == "Weapon Specialization":
                    continue
                filtered_feats.append(f)
            chosen_feats = filtered_feats

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
                    if ded["name"] in ARCHETYPE_GRANTED_FEATURES:
                        extra_feat = ARCHETYPE_GRANTED_FEATURES[ded["name"]]
                        if extra_feat.name not in existing_feat_names:
                            chosen_feats.append(extra_feat)
                            existing_feat_names.add(extra_feat.name)
                else:
                    lvl2_feats = [
                        f for f in self.feats
                        if f.get("category") == "class"
                        and f.get("level") == 2
                        and cls_name_lower in [t.lower() for t in f.get("traits", [])]
                    and (cls_name_lower != "kineticist" or is_kineticist_feat_allowed(f, gate_elements))
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
                        description=enrich_feat_description(resolved_feat_name2, sf.get("description", ""))
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
                    and (cls_name_lower != "kineticist" or is_kineticist_feat_allowed(f, gate_elements))
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
                        description=enrich_feat_description(resolved_name4, sf4.get("description", ""))
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

            
            elif lvl == 7:
                # Level 7: General Feat & Weapon Specialization
                if "Weapon Specialization" not in existing_feat_names:
                    chosen_feats.append(FeatSummary(
                        id="class-feat-weapon-specialization",
                        name="Weapon Specialization",
                        category="Class Feature (Level 7)",
                        action_cost=None,
                        traits=[cls_name_lower],
                        description="You deal 2 additional damage with weapons and unarmed attacks in which you are trained."
                    ))
                    existing_feat_names.add("Weapon Specialization")
                
                gen_feats_7 = [f for f in self.feats if f.get("category") == "general" and f.get("level", 1) <= 7 and f["name"] not in existing_feat_names]
                if gen_feats_7:
                    gf7 = random.choice(gen_feats_7)
                    chosen_feats.append(FeatSummary(
                        id=gf7["id"],
                        name=gf7["name"],
                        category="General Feat (Level 7)",
                        action_cost=None,
                        traits=["general"],
                        description=clean_pf2e_text(gf7["description"])
                    ))
                    existing_feat_names.add(gf7["name"])

            elif lvl == 8:
                # Level 8: Class Feat (or Archetype Feat) & Skill Feat
                arch_feats_8 = []
                if archetype_data:
                    arch_feats_8 = [f for f in archetype_data.get("level_8_feats", []) if f["name"] not in existing_feat_names]
                
                if arch_feats_8 and random.random() < 0.6:
                    af8 = random.choice(arch_feats_8)
                    chosen_feats.append(FeatSummary(
                        id=af8["id"],
                        name=af8["name"],
                        category=f"Archetype Feat (Level 8 - {archetype_data['name']})",
                        action_cost=None,
                        traits=["archetype"],
                        description=clean_pf2e_text(af8["description"])
                    ))
                    existing_feat_names.add(af8["name"])
                else:
                    lvl8_class_feats = [
                        f for f in self.feats
                        if f.get("category") == "class"
                        and f.get("level") in (6, 8)
                        and cls_name_lower in [t.lower() for t in f.get("traits", [])]
                        and f["name"] not in existing_feat_names
                    ]
                    if lvl8_class_feats:
                        cf8 = random.choice(lvl8_class_feats)
                        chosen_feats.append(FeatSummary(
                            id=cf8["id"],
                            name=cf8["name"],
                            category="Class Feat (Level 8)",
                            action_cost=None,
                            traits=[cls_name_lower],
                            description=clean_pf2e_text(cf8["description"])
                        ))
                        existing_feat_names.add(cf8["name"])

            elif lvl == 6:
                lvl6_class_feats = [
                    f for f in self.feats
                    if f.get("category") == "class"
                    and f.get("level") in (4, 6)
                    and cls_name_lower in [t.lower() for t in f.get("traits", [])]
                and (cls_name_lower != "kineticist" or is_kineticist_feat_allowed(f, gate_elements))
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

                skill_feats_6 = [
                    f for f in self.feats
                    if f.get("category") == "skill"
                    and f.get("level") in [1, 2, 4, 6]
                ]
                sf6 = pick_weighted_feat(skill_feats_6, cls["name"], existing_feat_names, {}, mods, 6)
                if sf6:
                    resolved_name6 = resolve_feat_subchoices(sf6["name"], existing_feat_names)
                    chosen_feats.append(FeatSummary(
                        id=sf6["id"],
                        name=resolved_name6,
                        category="Skill (Level 6)",
                        action_cost=sf6.get("action_cost"),
                        traits=sf6.get("traits", []),
                        description=enrich_feat_description(resolved_name6, sf6.get("description", ""))
                    ))
                    existing_feat_names.add(resolved_name6)

        if any(f.name.lower() == "toughness" for f in chosen_feats):
            total_hp += target_level

        # 7. Preserve and resolve skills & lore
        existing_skills_data = current_char.get("skills") or current_char.get("all_skills")
        existing_lore_name = current_char.get("lore")
        if not existing_lore_name and existing_skills_data:
            for sk in existing_skills_data:
                sk_dict = sk if isinstance(sk, dict) else (sk.__dict__ if hasattr(sk, "__dict__") else {})
                if sk_dict.get("is_lore") or "Lore" in sk_dict.get("name", ""):
                    existing_lore_name = sk_dict.get("name")
                    break

        all_skills = resolve_character_skills(
            class_name=cls["name"],
            background_data=bg,
            attribute_mods=mods,
            level=target_level,
            feats=chosen_feats,
            existing_skills=existing_skills_data,
            existing_lore=existing_lore_name
        )

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

        anc_desc = clean_pf2e_text(anc.get("description", "")) or current_char.get("ancestry_description", "")

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

        existing_companion = companion_data

        raw_extra_partners = current_char.get("additional_partners") or []
        existing_extra_partners = [
            PartnerCreatureData(**scale_existing_companion(p, old_level, target_level, total_hp)) if isinstance(p, dict)
            else p
            for p in raw_extra_partners
        ]

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


        # Refresh Sneak Attack feat descriptions on level up / down
        for f in chosen_feats:
            if f.name.lower() == "sneak attack":
                cur_dice = get_sneak_attack_dice(target_level, is_archetype=False)
                f.description = f"When your Strike hits an off-guard target and deals damage, you deal an extra {cur_dice} precision damage."
            elif f.name.lower() == "sneak attacker":
                cur_dice = get_sneak_attack_dice(target_level, is_archetype=True)
                f.description = f"You gain the Sneak Attack class feature, dealing an extra {cur_dice} precision damage to off-guard targets."

        has_sneak_lvl = any("sneak attack" in f.name.lower() or "sneak attacker" in f.name.lower() for f in chosen_feats)
        if has_sneak_lvl:
            is_arch_sneak_lvl = any("sneak attacker" in f.name.lower() for f in chosen_feats) and cls_name_lower != "rogue"
            s_dice_lvl = get_sneak_attack_dice(target_level, is_archetype=is_arch_sneak_lvl)
            for st in equipment_loadout.strikes:
                if "precision" not in st.damage_dice.lower() and "sneak" not in st.damage_dice.lower():
                    st.damage_dice = f"{st.damage_dice} (+{s_dice_lvl} precision vs off-guard)"

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
