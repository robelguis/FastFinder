import copy
import json
import os
import random
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from google import genai
from google.genai import types

from app.engine.archetypes import (
    ARCHETYPES_CATALOG,
    OSTILLI_GRAFT_ITEM,
    pick_archetype,
    resolve_dynamic_archetype,
)
from app.engine.companions import resolve_companion
from app.engine.constructs_undead import resolve_construct_companion, resolve_undead_companion
from app.engine.eidolons import resolve_eidolon
from app.engine.equipment import get_fundamental_rune_tiers, resolve_equipment
from app.engine.familiars import resolve_familiar
from app.engine.feat_prereqs import (
    calculate_feat_weight,
    check_feat_prerequisites,
    extract_gate_elements,
    is_kineticist_feat_allowed,
)
from app.engine.focus import resolve_focus_spells
from app.engine.deities import get_deity, get_deity_domains, get_domain_info, select_deity
from app.engine.heritages import ANCESTRY_HERITAGES, resolve_heritage
from app.engine.models import (
    AttributeModifiers,
    CharacterSheet,
    Defenses,
    FeatSummary,
    PartnerCreatureData,
    Proficiency,
    SkillEntry,
    Strike,
    SubclassSummary,
    DeitySummary,
    FocusSpellData,
    SpellSummary,
)
from app.engine.names import generate_golarion_name
from app.engine.plants_familiars_summons import resolve_plant_companion, resolve_specific_familiar
from app.engine.progression import (
    apply_remaster_level_boosts,
    get_class_saving_throws,
    get_weapon_prof_bonus_delta,
    get_weapon_spec_bonus,
)
from app.engine.skills import resolve_character_skills
from app.engine.spells import resolve_spellcasting
from app.engine.subclasses import BARBARIAN_ANIMAL_CHOICES, resolve_subclass
from app.engine.validator import sanitize_and_validate_sheet

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"

ATTRIBUTES = ["str", "dex", "con", "int", "wis", "cha"]
ATTR_NAME_TO_SHORT = {
    "str": "str", "strength": "str",
    "dex": "dex", "dexterity": "dex",
    "con": "con", "constitution": "con",
    "int": "int", "intelligence": "int",
    "wis": "wis", "wisdom": "wis",
    "cha": "cha", "charisma": "cha",
}
ATTR_FULL_TO_SHORT = (
    ("strength", "str"),
    ("dexterity", "dex"),
    ("constitution", "con"),
    ("intelligence", "int"),
    ("wisdom", "wis"),
    ("charisma", "cha"),
)

RANK_MAP = {
    1: (2, "T"),
    2: (4, "E"),
    3: (6, "M"),
    4: (8, "L"),
}

RANK_WORD_SPECS = {
    "trained": (2, "T"),
    "expert": (4, "E"),
    "master": (6, "M"),
    "legendary": (8, "L"),
}

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
    "nagaji": ["nagaji"],
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
        "description": "When your Strike hits an off-guard target and deals damage, you deal an extra {sneak_dice} precision damage.",
    },
    "swashbuckler": {
        "name": "Panache & Finisher",
        "description": "When you have panache, your Strikes deal +{panache_flat} precision damage. Using a Finisher ends panache and deals +{finisher_dice} precision damage.",
    },
    "investigator": {
        "name": "Devise a Stratagem",
        "description": "You assess a foe's defenses. Once per round (1 action or free action against your lead), roll a d20 and use it for your next Strike against that creature with your Intelligence modifier to attack.",
    },
    "thaumaturge": {
        "name": "Exploit Vulnerability",
        "description": "You identify a mortal weakness in your target, dealing mortal weakness or personal antithesis bonus damage.",
    },
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
    "bard": {"name": "Lightning Reflexes", "description": "Your proficiency rank for Reflex saves increases to Expert (+4)."},
    "thaumaturge": {"name": "Second Implement", "description": "You gain a second implement and its initiate benefit. While holding either implement, you can use its benefits."},
}

ARCHETYPE_GRANTED_FEATURES = {
    "Rogue Dedication": FeatSummary(
        id="feat-archetype-surprise-attack",
        name="Surprise Attack",
        category="Archetype Feature",
        action_cost=None,
        traits=["archetype", "rogue"],
        description="You act or spring into combat before your foes are ready. On the first round of combat, if you roll Deception or Stealth for initiative, any creatures that haven't acted yet are off-guard to you.",
    ),
    "Ranger Dedication": FeatSummary(
        id="feat-archetype-hunt-prey",
        name="Hunt Prey",
        category="Archetype Feature",
        action_cost=1,
        traits=["archetype", "concentrate", "ranger"],
        description="Designate a creature you can see or track as your prey. You gain a +2 circumstance bonus to Perception checks to Seek or Sense Motive against it, and a +2 circumstance bonus to Survival checks to Track it. You also ignore the second range increment penalty on ranged attacks against your prey.",
    ),
    "Investigator Dedication": FeatSummary(
        id="feat-archetype-devise-a-stratagem",
        name="Devise a Stratagem",
        category="Archetype Feature",
        action_cost=1,
        traits=["archetype", "concentrate", "fortune", "investigator"],
        description="Roll a d20. You must use that result for the attack roll of your next Strike this round against the designated creature, substituting your Intelligence modifier for your Strength or Dexterity modifier on the attack roll.",
    ),
}

ARCHER_DEDICATION = {
    "feat": "Archer Dedication",
    "level": 2,
    "prerequisites": ["Trained in Martial Weapons"],
    "weapons": ["Shortbow", "Longbow", "Composite Shortbow", "Composite Longbow"],
    "benefit": (
        "You become trained in all simple and martial ranged weapons. "
        "Whenever you gain a class feature that grants you expert or greater "
        "proficiency in a given weapon, you also gain that proficiency in "
        "bows and your choice of a 3rd designated ranged weapon."
    ),
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
    "kobold": {"name": "Kobold Breath", "description": "You channel dragon blood to exhale an elemental blast in a 15-foot cone for 3d4 damage."},
}

ALL_SKILL_NAMES = [
    "Acrobatics", "Athletics", "Deception", "Diplomacy", "Intimidation",
    "Medicine", "Nature", "Occultism", "Performance", "Religion",
    "Society", "Stealth", "Survival", "Thievery",
]

TERRAIN_TYPES = [
    "Aquatic", "Arctic", "Desert", "Forest",
    "Mountain", "Plains", "Sky", "Swamp", "Underground",
]

COMMON_LANG_POOL = [
    "Common", "Dwarven", "Elven", "Gnomish", "Goblin", "Halfling",
    "Orcish", "Draconic", "Sylvan", "Undercommon", "Jotun", "Necril",
    "Aklo", "Celestial", "Abyssal", "Infernal", "Shadowtongue", "Iruxi",
]

BACKGROUND_CUSTOM_ACTIONS = {
    "hunt the razer's pawn": {
        "name": "Hunt the Razer's Pawn",
        "action_cost": 1,
        "traits": ["Concentrate", "Exploration", "Secret"],
        "description": "You study the demeanor, iconography, or residual essence of a creature to determine if it is an agent or pawn of Treerazer. Attempt a Religion check against the creature's Deception DC. On a success, you learn whether the creature is allied with, dominated by, or in the service of Treerazer or his cult.",
    },
    "stellar misfortune": {
        "name": "Stellar Misfortune",
        "action_cost": 1,
        "traits": ["Concentrate", "Occult", "Prediction"],
        "description": "You call upon the indifferent cold of the stars to curse an enemy's next step, imposing misdirection or misfortune on their rolls. Attempt an Occultism check or spell attack against the target.",
    },
}

WING_NATURAL_ANCESTRIES = {"strix", "sprite", "awakened animal"}
WING_NATURAL_HERITAGES = {"dragonblood", "beastkin", "tiefling", "aasimar", "nephilim", "sylph"}

_LORE_BLOCKLIST_WORDS = {
    "a", "an", "the", "and", "or", "for", "of", "in", "to", "with", "from",
    "your", "my", "our", "their", "this", "that", "any", "each", "either", "both",
    "gain", "gained", "gains", "grant", "grants", "granted", "also", "feat",
    "general", "skill", "subcategory", "trained", "additional", "lore",
}

_RE_HTML_TAG = re.compile(r"<[^>]+>")
_RE_TEMPLATE = re.compile(r"@Template\[(?:type:)?([a-zA-Z]+)\|distance:(\d+)[^\]]*\](?:\{([^}]+)\})?")
_RE_UUID_LABELED = re.compile(r"@UUID\[[^\]]+\]\{([^}]+)\}")
_RE_UUID_BARE = re.compile(r"@UUID\[(?:.*?\.)?([^\]\.]+?)\]")
_RE_COMPENDIUM_LABELED = re.compile(r"@Compendium\[[^\]]+\]\{([^}]+)\}")
_RE_COMPENDIUM_BARE = re.compile(r"@Compendium\[[^\]]+\]")
_RE_CHECK_LABELED = re.compile(r"@Check\[[^\]]+\]\{([^}]+)\}")
_RE_CHECK_TYPE = re.compile(r"@Check\[[^\]]*type:([a-zA-Z]+)[^\]]*\]")
_RE_DAMAGE_LABELED = re.compile(r"@Damage\[[^\]]+\]\{([^}]+)\}")
_RE_DAMAGE_BARE = re.compile(r"@Damage\[([^\]]+)\]")
_RE_AT_LABELED = re.compile(r"@[A-Za-z]+\[[^\]]+\]\{([^}]+)\}")
_RE_AT_BARE = re.compile(r"@[A-Za-z]+\[[^\]]+\]")
_RE_EMPTY_BRACKETS = re.compile(r"\[\s*\]")
_RE_ROLL_INLINE_LABELED = re.compile(r"\[\[/r\s+[^\]{]+\{([^}]+)\}\]\]")
_RE_ROLL_LABELED = re.compile(r"/r\s+[^\s{]+(?:\s+#[^{]+)?\{([^}]+)\}")
_RE_ROLL_DICE = re.compile(r"/r\s+([0-9d+\-]+)")
_RE_CEIL_LEVEL = re.compile(r"\(ceil\(@actor\.level/2\)\)d(\d+)(?:\[[^\]]*\])?")
_RE_OPTIONS_TAG = re.compile(r"\[[^\]]*options:[^\]]*\]")
_RE_ACT_TAG = re.compile(r"/act\s+([a-zA-Z\-]+)(?:\s+skill=([a-zA-Z]+))?")
_RE_DICE_TYPE = re.compile(r"(\d+d\d+(?:\+\d+)?)\[([a-zA-Z]+)\]")
_RE_PAREN_BRACE = re.compile(r"\(([A-Za-z]+)\)\s*\{[^}\n]+\}?")
_RE_TRAILING_BRACE = re.compile(r"\s*\{[A-Za-z][^}\n]*$", flags=re.MULTILINE)
_RE_RUNE_PREFIX = re.compile(r"^\+\d+\s+(?:(?:Greater|Major)\s+)?(?:Striking\s+)?", flags=re.I)


def is_background_compatible_with_ancestry(bg_data: dict, ancestry_name: str) -> bool:
    anc_lower = ancestry_name.lower()
    bg_name = bg_data.get("name", "").lower()
    bg_lore = bg_data.get("trained_lore", "").lower()
    name_words = {w.strip("(),.-") for w in bg_name.split()}

    bg_restricted_ancestry = None
    for target_anc, aliases in ANCESTRY_BG_MAP.items():
        if any(f"{alias} lore" in bg_lore or alias in name_words for alias in aliases):
            bg_restricted_ancestry = target_anc
            break

    if not bg_restricted_ancestry:
        return True

    return any(
        alias in anc_lower
        for alias in ANCESTRY_BG_MAP.get(bg_restricted_ancestry, [bg_restricted_ancestry])
    )


def get_sneak_attack_dice(level: int, is_archetype: bool = False) -> str:
    if is_archetype:
        return "2d6" if level >= 6 else "1d6"
    return "3d6" if level >= 11 else ("2d6" if level >= 5 else "1d6")


def is_animal_partner(p: Any) -> bool:
    ct = (getattr(p, "creature_type", "") or "").lower()
    st = (getattr(p, "sub_type", "") or "").lower()
    nm = (getattr(p, "name", "") or "").lower()
    return (
        "animal" in ct
        or "mount" in ct
        or "animal companion" in st
        or nm.startswith("companion (")
        or nm == "faithful steed"
    )


def strip_foundry_tags(val: str) -> str:
    if not isinstance(val, str):
        return val
    cleaned = _RE_UUID_LABELED.sub(r"\1", val)
    cleaned = _RE_UUID_BARE.sub("", cleaned)
    cleaned = _RE_COMPENDIUM_LABELED.sub(r"\1", cleaned)
    cleaned = _RE_COMPENDIUM_BARE.sub("", cleaned)
    return cleaned.strip()


def safe_action_cost(val: Any) -> Optional[int]:
    if val is None:
        return None
    if isinstance(val, int):
        return val
    if isinstance(val, str):
        m = re.search(r"\d+", val)
        if m:
            return int(m.group())
        if any(w in val.lower() for w in ("reaction", "free")):
            return 0
    return None


def clean_pf2e_text(text: str) -> str:
    if not text:
        return ""
    text = _RE_HTML_TAG.sub("", text)
    text = _RE_TEMPLATE.sub(lambda m: m.group(3) if m.group(3) else f"{m.group(2)}-foot {m.group(1)}", text)
    text = _RE_UUID_LABELED.sub(r"\1", text)
    text = _RE_UUID_BARE.sub(r"\1", text)
    text = _RE_CHECK_LABELED.sub(r"\1", text)
    text = _RE_CHECK_TYPE.sub(r"\1 check", text)
    text = _RE_DAMAGE_LABELED.sub(r"\1", text)
    text = _RE_DAMAGE_BARE.sub(r"\1", text)
    text = _RE_AT_LABELED.sub(r"\1", text)
    text = _RE_AT_BARE.sub("", text)
    text = _RE_EMPTY_BRACKETS.sub("", text)
    text = _RE_ROLL_INLINE_LABELED.sub(r"\1", text)
    text = _RE_ROLL_LABELED.sub(r"\1", text)
    text = _RE_ROLL_DICE.sub(r"\1", text)
    text = _RE_CEIL_LEVEL.sub(r"1d\1 per 2 levels", text)
    text = text.replace("@actor.level", "your level")
    text = _RE_OPTIONS_TAG.sub("", text)
    text = _RE_ACT_TAG.sub(
        lambda m: f"{m.group(1).replace('-', ' ').title()}" + (f" ({m.group(2).title()})" if m.group(2) else ""),
        text,
    )
    text = _RE_DICE_TYPE.sub(r"\1 \2", text)
    text = _RE_PAREN_BRACE.sub(r"(\1)", text)
    text = _RE_TRAILING_BRACE.sub("", text)
    text = text.replace("[[", "").replace("]]", "")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    # 1. Clean nested-paren formulas followed by [type]{label} or {label}
    text = re.sub(r"\((?:[^()\n]|\([^()\n]*\))*\)(?:\s*\[[^\]\n]+\])?\s*\{([^}\n]+)\}", r"\1", text)
    # 2. Clean formula tokens (your level, @actor.*) with optional [type] and {label}
    text = re.sub(r"\b(?:your level|@actor(?:\.[A-Za-z0-9_]+)+)(?:\s*\[[^\]\n]+\])?\s*\{([^}\n]+)\}", r"\1", text)
    # 3. Clean (Skill/Action) followed by key=val tokens and {label}
    text = re.sub(r"(\([A-Za-z][A-Za-z0-9_\s\-]*\))(?:\s+[a-zA-Z0-9_\-]+=[a-zA-Z0-9_\-]+)*\s*\{([^}\n]+)\}", r"\1", text)
    # 4. Clean remaining @actor.* attribute paths and stray braces
    text = re.sub(r"@actor(?:\.system)?\.abilities\.([a-z]{3})\.mod", lambda m: f"your {m.group(1).upper()} modifier", text)
    text = re.sub(r"@actor\.[A-Za-z0-9_.]+", "your level", text)
    text = re.sub(r"\{([^}\n]+)\}", r"\1", text)
    return text.strip()


def load_data(filename: str) -> Any:
    path = DATA_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Missing {filename}.")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _parse_int_bonus(val: Any, default: int = 0) -> int:
    try:
        return int(str(val).replace("+", "").strip())
    except (ValueError, TypeError):
        return default


def _bump_strike_bonus(val: Any, delta: int) -> Any:
    try:
        clean_val = str(val).replace("+", "").strip()
        return str(int(clean_val) + int(delta))
    except (ValueError, TypeError):
        return val


def _apply_extra_weapon_stats(equipment_loadout: Any, class_name: str, level: int) -> None:
    if not equipment_loadout or not getattr(equipment_loadout, "strikes", None):
        return
    extra_prof = get_weapon_prof_bonus_delta(class_name, level)
    if extra_prof:
        for strike in equipment_loadout.strikes:
            strike.attack_bonus = _bump_strike_bonus(strike.attack_bonus, extra_prof)
            strike.map_second = _bump_strike_bonus(strike.map_second, extra_prof)
            strike.map_third = _bump_strike_bonus(strike.map_third, extra_prof)
    spec_dmg = get_weapon_spec_bonus(class_name, level)
    if spec_dmg:
        for strike in equipment_loadout.strikes:
            if f"+{spec_dmg}" not in strike.damage_dice and "Weapon Spec" not in strike.damage_dice:
                strike.damage_dice = f"{strike.damage_dice} + {str(spec_dmg)}"


def _build_archer_bow_strike(level: int, dex_mod: int) -> Strike:
    chosen_bow = random.choice(["Shortbow", "Longbow", "Composite Shortbow", "Composite Longbow"])
    is_long = "longbow" in chosen_bow.lower()
    range_ft = 100 if is_long else 60
    potency = 3 if level >= 16 else (2 if level >= 10 else (1 if level >= 2 else 0))
    dice_mult = 4 if level >= 19 else (3 if level >= 12 else (2 if level >= 4 else 1))
    striking_label = (
        "Major Striking " if dice_mult == 4 else
        ("Greater Striking " if dice_mult == 3 else ("Striking " if dice_mult == 2 else ""))
    )
    prefix = f"+{potency} {striking_label}" if potency > 0 else striking_label
    atk = level + 2 + dex_mod + potency
    return Strike(
        name=f"{prefix}{chosen_bow}",
        attack_bonus=str(atk),
        map_second=str(atk - 5),
        map_third=str(atk - 10),
        damage_dice=f"{dice_mult}d8" if is_long else f"{dice_mult}d6",
        damage_type="Piercing",
        traits=["Deadly d10", f"Range {range_ft} ft"],
    )


def _inject_kineticist_blasts(equipment_loadout: Any, level: int, mods: dict) -> None:
    prof = 2 + level + (2 if level >= 5 else 0)
    melee_bonus = prof + mods.get("con", 0)
    ranged_bonus = prof + mods.get("dex", 0)
    dice_count = 2 if level >= 5 else 1
    melee_str_bonus = mods.get("str", 0) if mods.get("str", 0) > 0 else 0
    spec_bonus = 2 if level >= 7 else 0
    melee_dmg_bonus = mods.get("con", 0) + melee_str_bonus + spec_bonus
    ranged_dmg_bonus = mods.get("con", 0) + spec_bonus

    melee_blast = Strike(
        name="Elemental Blast (Melee)",
        attack_bonus=melee_bonus,
        map_second=melee_bonus - 5,
        map_third=melee_bonus - 10,
        damage_dice=f"{dice_count}d8+{melee_dmg_bonus}" if melee_dmg_bonus > 0 else f"{dice_count}d8",
        damage_type="Bludgeoning / Piercing / Slashing",
        traits=["Impulse", "Kinetic", "Magical", "Primal"],
    )
    ranged_blast = Strike(
        name="Elemental Blast (Ranged)",
        attack_bonus=ranged_bonus,
        map_second=ranged_bonus - 5,
        map_third=ranged_bonus - 10,
        damage_dice=f"{dice_count}d6+{ranged_dmg_bonus}" if ranged_dmg_bonus > 0 else f"{dice_count}d6",
        damage_type="Bludgeoning / Piercing / Slashing (60 ft)",
        traits=["Impulse", "Infusion", "Kinetic", "Magical", "Primal"],
    )
    equipment_loadout.strikes = [s for s in equipment_loadout.strikes if not s.name.startswith("Elemental Blast")]
    equipment_loadout.strikes.insert(0, ranged_blast)
    equipment_loadout.strikes.insert(0, melee_blast)


def sync_feat_partners(
    existing_partners: list,
    chosen_feats: list,
    archetype_name: Optional[str],
    class_name: str,
    level: int,
    master_ac: int,
    master_fort: int,
    master_ref: int,
    master_will: int,
    master_perception: int,
    master_hp: int = 20,
    concept_text: Optional[str] = None,
    ancestry_name: str = "",
    heritage_name: str = "",
    background_name: str = "",
    subclass_name: str = "",
) -> list:
    partners = list(existing_partners)
    feat_names = [f.name.lower() for f in chosen_feats]
    all_feat_str = " ".join(feat_names)
    arch_str = (archetype_name or "").lower()
    cls_lower = class_name.lower()
    existing_names = {(p.name or "").lower() for p in partners}

    def _append_unique(partner: Optional[PartnerCreatureData]) -> None:
        if partner and (partner.name or "").lower() not in existing_names:
            partners.append(partner)
            existing_names.add((partner.name or "").lower())

    # 0. Summoner Dedication Eidolon
    if level >= 2 and "summoner" in arch_str and cls_lower != "summoner":
        if not any("eidolon" in (p.creature_type or "").lower() for p in partners):
            _append_unique(resolve_eidolon(master_hp=master_hp, level=level, eidolon_type=""))

    # 1. Undead Companion / Undead Master / Necromancer
    if any(k in arch_str for k in ("undead master", "necromancer")) or "undead companion" in all_feat_str:
        if not any("undead" in (p.creature_type or "").lower() for p in partners):
            _append_unique(resolve_undead_companion(level=level))

    # 2. Construct Companion / Clockwork Reanimator / Inventor Dedication
    if (
        any(k in arch_str for k in ("clockwork reanimator", "inventor"))
        or any(k in all_feat_str for k in ("construct companion", "prototype companion"))
    ):
        if not any("construct" in (p.creature_type or "").lower() for p in partners):
            _append_unique(resolve_construct_companion(master_int_mod=2, level=level))

    # 3. Plant Companion
    if "plant companion" in all_feat_str:
        if not any("plant" in (p.creature_type or "").lower() for p in partners):
            _append_unique(resolve_plant_companion(level=level))

    # 4. Animal Companion / Mounts / Faithful Steed / Beastmaster / Cavalier
    animal_triggers = ("animal companion", "mature animal companion", "mount", "bonded animal")
    steed_triggers = ("faithful steed", "knight's steed")
    animal_arch_triggers = ("beastmaster", "cavalier", "mammoth lord")
    is_kineticist = cls_lower == "kineticist"
    has_steed_feat = any(st in all_feat_str for st in steed_triggers) or cls_lower == "champion"
    is_druid_animal_order = (
        (cls_lower == "druid" or (level >= 2 and "druid" in arch_str))
        and "selected druidic order: animal" in all_feat_str
    )
    has_animal_arch = level >= 2 and any(ar in arch_str for ar in animal_arch_triggers)

    if (not is_kineticist or is_druid_animal_order or has_animal_arch) and (
        any(tr in all_feat_str for tr in animal_triggers)
        or any(st in all_feat_str for st in steed_triggers)
        or cls_lower == "ranger"
        or is_druid_animal_order
        or has_animal_arch
    ):
        if not any(is_animal_partner(p) for p in partners):
            comp = resolve_companion(
                class_name="Champion" if has_steed_feat else class_name,
                feats=chosen_feats,
                archetype=archetype_name if (archetype_name and level >= 2) else None,
                level=level,
                force_qualify=is_druid_animal_order,
                concept_text=concept_text,
                ancestry_name=ancestry_name,
                heritage_name=heritage_name,
                background_name=background_name,
                subclass_name=subclass_name,
            )
            if comp:
                if has_steed_feat:
                    comp.name = "Faithful Steed"
                    comp.creature_type = "Animal Companion"
                _append_unique(comp)

    # 5. Familiars & Pets
    has_marine_ally = "marine ally" in feat_names
    is_druid_leaf = (
        (cls_lower == "druid" or (level >= 2 and "druid" in arch_str))
        and ("selected druidic order: leaf" in all_feat_str or "leaf order" in feat_names)
    )
    is_leaf_leshy = ("leshy familiar" in all_feat_str) or is_druid_leaf
    has_witch_dedication = level >= 2 and "witch" in arch_str
    has_familiar_arch = (level >= 2 and any(k in arch_str for k in ("familiar master", "witch"))) or is_druid_leaf
    has_elemental_familiar = "elemental familiar" in all_feat_str
    familiar_triggers = (
        "familiar", "marine ally", "leshy familiar", "elemental familiar",
        "shadow familiar", "spirit guide", "glyph familiar", "call wizardly tools",
    )
    has_pet_feat = "pet" in feat_names
    is_animal_partner_class = cls_lower == "ranger" or (cls_lower == "druid" and any("animal" in f for f in feat_names))

    if (
        cls_lower != "witch"
        and (not is_animal_partner_class or has_familiar_arch or has_marine_ally or is_leaf_leshy)
        and not any("familiar" in (p.creature_type or "").lower() for p in partners)
    ):
        if is_kineticist and not (
            has_marine_ally or is_leaf_leshy or has_familiar_arch
            or (level >= 2 and any(k in arch_str for k in ("beastmaster", "clockwork reanimator")))
        ):
            if has_elemental_familiar:
                _append_unique(resolve_familiar(
                    master_ac=master_ac, master_fort=master_fort, master_ref=master_ref,
                    master_will=master_will, master_perception=master_perception,
                    class_name=class_name, level=level, aquatic_only=False,
                    is_pet=False, forced_species="elemental", description_text=concept_text,
                ))
        elif (
            has_marine_ally or is_leaf_leshy or has_witch_dedication
            or any(tr in all_feat_str for tr in familiar_triggers) or has_familiar_arch
        ):
            forced_sp = "leshy" if is_leaf_leshy else ("elemental" if has_elemental_familiar else None)
            _append_unique(resolve_familiar(
                master_ac=master_ac, master_fort=master_fort, master_ref=master_ref,
                master_will=master_will, master_perception=master_perception,
                class_name=class_name, level=level, aquatic_only=has_marine_ally,
                is_pet=False, forced_species=forced_sp, description_text=concept_text,
            ))
        elif has_pet_feat:
            _append_unique(resolve_familiar(
                master_ac=master_ac, master_fort=master_fort, master_ref=master_ref,
                master_will=master_will, master_perception=3 + level,
                class_name=class_name, level=level, aquatic_only=False, is_pet=True,
                description_text=concept_text,
            ))

    return partners


def scale_existing_companion(companion_data: dict, old_level: int, target_level: int, master_hp: int) -> dict:
    comp = dict(companion_data)
    level_delta = target_level - old_level
    if level_delta <= 0:
        return comp

    creature_type = (comp.get("creature_type") or "").lower()
    c_stage = (comp.get("stage") or "").lower()
    if "eidolon" in creature_type:
        comp["hp"] = master_hp
    elif any(k in creature_type or k in c_stage for k in ("familiar", "pet")):
        comp["hp"] = 5 * target_level
    else:
        comp["hp"] = comp.get("hp", 20) + (level_delta * 8)

    stage_bump = 2 if (old_level < 4 and target_level >= 4 and "eidolon" not in creature_type) else 0
    total_stat_boost = level_delta + stage_bump
    comp["ac"] = _parse_int_bonus(comp.get("ac", 16), 16) + total_stat_boost
    comp["fortitude"] = _parse_int_bonus(comp.get("fortitude", 5), 5) + total_stat_boost
    comp["reflex"] = _parse_int_bonus(comp.get("reflex", 5), 5) + total_stat_boost
    comp["will"] = _parse_int_bonus(comp.get("will", 5), 5) + total_stat_boost
    comp["perception"] = _parse_int_bonus(comp.get("perception", 4), 4) + total_stat_boost

    updated_strikes = []
    for strike in comp.get("strikes", []):
        s = dict(strike)
        raw_atk = s.get("attack_bonus", 5)
        new_atk = _parse_int_bonus(raw_atk, 5) + total_stat_boost
        s["attack_bonus"] = f"{new_atk:+d}" if isinstance(raw_atk, str) else new_atk
        for m_key, m_def in (("map_second", 0), ("map_third", -5)):
            if m_key in s:
                raw_m = s.get(m_key, m_def)
                new_m = _parse_int_bonus(raw_m, m_def) + total_stat_boost
                s[m_key] = f"{new_m:+d}" if isinstance(raw_m, str) else new_m
        updated_strikes.append(s)
    comp["strikes"] = updated_strikes

    if target_level >= 4 and "Young" in comp.get("stage", ""):
        comp["stage"] = comp["stage"].replace("Young", "Mature")

    return comp


def _attach_named_artillery_strike(chosen_feats: List[FeatSummary], equipment_loadout: Any, level: int, mods: dict) -> None:
    if not equipment_loadout or not hasattr(equipment_loadout, "strikes") or not chosen_feats:
        return
    art_feat = next((f for f in chosen_feats if "named artillery" in (f.name or "").lower()), None)
    if not art_feat:
        return
    if any(
        "siege" in " ".join(st.traits or []).lower() or "artillery" in (st.name or "").lower()
        for st in equipment_loadout.strikes
    ):
        return

    weapon_label = "Named Artillery"
    if "(" in art_feat.name and ")" in art_feat.name:
        weapon_label = art_feat.name.split("(", 1)[1].rstrip(")").strip()

    prof = 4 if level >= 5 else 2
    stat_mod = max(mods.get("dex", 0), mods.get("int", 0))
    atk = level + prof + stat_mod + 1
    dice_count = 4 if level >= 15 else (3 if level >= 9 else (2 if level >= 4 else 1))
    dmg_die = "d10" if any(k in weapon_label.lower() for k in ("bombard", "cannon", "trebuchet")) else "d8"
    dmg_type = (
        "Fire / Bludgeoning"
        if any(k in weapon_label.lower() for k in ("bombard", "cannon", "dragon"))
        else "Piercing / Bludgeoning"
    )
    equipment_loadout.strikes.append(Strike(
        name=f"{weapon_label} (Artillery)",
        attack_bonus=str(atk),
        map_second=str(atk - 5),
        map_third=str(atk - 10),
        damage_dice=f"{dice_count}{dmg_die}+{max(0, mods.get('int', 0))}",
        damage_type=dmg_type,
        traits=["Siege", "Artillery", "Range 120 ft", "+1 Named Bonus"],
    ))


def _clean_lore_candidate(raw: str) -> str:
    """Extracts a clean '<Topic> Lore' name from a candidate phrase without glue words."""
    if not raw or not isinstance(raw, str):
        return ""
    words = re.findall(r"[A-Za-z][A-Za-z'\-]*", raw)
    if not words:
        return ""
    lore_indices = [i for i, w in enumerate(words) if w.lower() == "lore"]
    if not lore_indices:
        return ""
    last_lore = lore_indices[-1]
    topic_tokens = []
    for w in reversed(words[:last_lore]):
        if w.lower() in _LORE_BLOCKLIST_WORDS:
            break
        topic_tokens.append(w.capitalize())
        if len(topic_tokens) == 3:
            break
    if not topic_tokens:
        return ""
    topic_tokens.reverse()
    return " ".join(topic_tokens) + " Lore"


def extract_lores_from_feat(feat_name: str, feat_desc: str = "") -> List[str]:
    """Generically extracts Lore skill names (e.g., 'Yaoguai Lore') granted by any feat."""
    found: List[str] = []
    seen: Set[str] = set()

    def _add(raw: str) -> None:
        cand = _clean_lore_candidate(raw)
        if not cand:
            return
        key = cand.lower()
        if key not in seen and key != "lore":
            seen.add(key)
            found.append(cand)

    for pm in re.findall(r"\(([^)]+)\)", feat_name or ""):
        if "lore" in pm.lower():
            _add(pm)

    blob = f"{feat_name or ''}\n{feat_desc or ''}"
    for m in re.finditer(r"\b(?:[A-Za-z][A-Za-z'\-]*\s+){1,4}Lore\b", blob):
        _add(m.group(0))

    return found


def apply_feat_granted_lores(all_skills: list, chosen_feats: list, level: int, int_mod: int) -> None:
    """Ensures any Lore skill referenced as granted by a feat is present and at least Trained."""
    if not isinstance(all_skills, list) or not chosen_feats:
        return

    t_bonus = level + 2 + int_mod
    existing_by_low = {}
    for sk in all_skills:
        sk_name = ((getattr(sk, "name", None) if not isinstance(sk, dict) else sk.get("name", "")) or "").strip()
        if sk_name:
            existing_by_low[sk_name.lower()] = sk

    for feat in chosen_feats:
        f_name = (getattr(feat, "name", None) if not isinstance(feat, dict) else feat.get("name", "")) or ""
        f_desc = (getattr(feat, "description", None) if not isinstance(feat, dict) else feat.get("description", "")) or ""
        if not re.search(
            r"\b(gain|grants?|additional)\b.*\blore\b|\blore\b.*\b(trained|lore feat)\b",
            f"{f_name} {f_desc}",
            re.IGNORECASE | re.DOTALL,
        ):
            continue

        for lore_name in extract_lores_from_feat(f_name, f_desc):
            l_low = lore_name.lower()
            sk = existing_by_low.get(l_low)
            if sk is not None:
                cur_rank = ((getattr(sk, "rank_letter", None) if not isinstance(sk, dict) else sk.get("rank_letter", "U")) or "U").upper()
                if cur_rank == "U":
                    if isinstance(sk, dict):
                        sk["rank_letter"] = "T"
                        sk["rank"] = 2
                        sk["modifier"] = max(int(sk.get("modifier", 0)), t_bonus)
                    else:
                        sk.rank_letter = "T"
                        if hasattr(sk, "rank"):
                            sk.rank = 2
                        sk.modifier = max(int(getattr(sk, "modifier", 0)), t_bonus)
            else:
                sample = all_skills[0] if all_skills else None
                if isinstance(sample, dict):
                    new_sk = {
                        "name": lore_name,
                        "attribute": "INT",
                        "rank_letter": "T",
                        "rank": 2,
                        "modifier": t_bonus,
                        "is_lore": True,
                    }
                    all_skills.append(new_sk)
                    existing_by_low[l_low] = new_sk
                elif sample is not None:
                    try:
                        new_sk = type(sample)(
                            name=lore_name,
                            attribute="INT",
                            rank_letter="T",
                            rank=2,
                            modifier=t_bonus,
                        )
                        all_skills.append(new_sk)
                        existing_by_low[l_low] = new_sk
                    except Exception:
                        pass


def resolve_feat_subchoices(feat_name: str, existing_feat_names: set, active_deity_name: Optional[str] = None) -> str:
    fn_lower = feat_name.lower()
    if "(" in feat_name:
        return feat_name

    if "wilderness spotter" in fn_lower:
        taken = {
            fn.split("(")[-1].replace(")", "").strip().title()
            for fn in existing_feat_names
            if "wilderness spotter" in fn.lower() and "(" in fn
        }
        available = [t for t in TERRAIN_TYPES if t not in taken]
        chosen = random.choice(available or TERRAIN_TYPES)
        return f"{feat_name} ({chosen})"

    if "splinter faith" in fn_lower:
        deity_pool = get_deity_domains(active_deity_name, include_alternate=True) if active_deity_name else []
        fallback_pool = ["Protection", "Zeal", "Sun", "Might", "Moon", "Nature", "Healing", "Truth", "Family", "Travel"]
        domain_pool = deity_pool if len(deity_pool) >= 4 else (deity_pool + [d for d in fallback_pool if d not in deity_pool])
        return f"{feat_name} ({', '.join(random.sample(domain_pool, min(4, len(domain_pool))))})"

    norm_fn = fn_lower.replace("’", "'")
    if any(k in norm_fn for k in ("deity's domain", "deitys domain", "domain initiate")):
        deity_pool = get_deity_domains(active_deity_name, include_alternate=True) if active_deity_name else []
        fallback_pool = ["Zeal", "Protection", "Sun", "Might", "Moon", "Nature", "Healing", "Truth", "Family", "Travel"]
        domain_pool = deity_pool or fallback_pool
        taken_domains = {
            fn.split("(")[-1].replace(")", "").strip().title()
            for fn in existing_feat_names
            if "domain" in fn.lower() and "(" in fn
        }
        avail_domains = [d for d in domain_pool if d not in taken_domains]
        return f"{feat_name} ({random.choice(avail_domains or domain_pool)})"

    if "terrain stalker" in fn_lower:
        return f"{feat_name} ({random.choice(['Rubble', 'Snow', 'Underbrush'])})"

    if "additional lore" in fn_lower:
        lore_pool = [
            "Academia Lore", "Architecture Lore", "Art Lore", "Barrow Lore",
            "Circus Lore", "Engineering Lore", "Forest Lore", "Fortune-Telling Lore",
            "Guild Lore", "Heraldry Lore", "Hunting Lore", "Labor Lore",
            "Legal Lore", "Midwifery Lore", "Mining Lore", "Ocean Lore",
            "Politics Lore", "Sailing Lore", "Scouting Lore", "Settlement Lore",
            "Theatre Lore", "Underworld Lore", "Warfare Lore",
        ]
        taken_lores = {
            fn.split("(", 1)[1].rstrip(")").strip().lower()
            for fn in existing_feat_names
            if "additional lore" in fn.lower() and "(" in fn and ")" in fn
        }
        available_lores = [l for l in lore_pool if l.lower() not in taken_lores]
        return f"{feat_name} ({random.choice(available_lores or lore_pool)})"

    if "arcane tattoos" in fn_lower:
        tattoo_schools = [
            "Abjuration — Shield",
            "Conjuration — Tangle Vine",
            "Enchantment — Daze",
            "Evocation — Electric Arc",
            "Illusion — Figment",
            "Necromancy — Void Warp",
            "Transmutation — Sigil",
        ]
        return f"{feat_name} ({random.choice(tattoo_schools)})"

    if "named artillery" in fn_lower:
        artillery_names = [
            '"Thunderclap" Bombard',
            '"Old Ironsides" Ballista',
            '"Dragons Breath" Catapult',
            '"Skybreaker" Trebuchet',
            '"Iron Sovereign" Cannon',
            '"Stormcaller" Springald',
        ]
        return f"{feat_name} ({random.choice(artillery_names)})"

    return feat_name


def can_take_additional_lore(existing_feat_names: set, cls_name: str, archetype_name: str = "") -> bool:
    is_bard = (cls_name or "").strip().lower() == "bard"
    has_bard_ded = "bard" in (archetype_name or "").lower() or any(
        "bard dedication" in fn.lower() for fn in existing_feat_names
    )
    current_count = sum(1 for fn in existing_feat_names if "additional lore" in fn.lower())
    return current_count < (23 if (is_bard or has_bard_ded) else 2)


def can_take_dedication(feat_name: str, existing_feats: list, existing_feat_names: set) -> bool:
    fn_low = (feat_name or "").strip().lower()
    if "dedication" not in fn_low:
        return True
    if any(fn_low == existing.strip().lower() for existing in existing_feat_names):
        return False
    dedications = [f for f in existing_feats if "dedication" in (getattr(f, "name", "") or "").lower()]
    if not dedications:
        return True
    arch_feats = [
        f for f in existing_feats
        if "archetype" in (getattr(f, "category", "") or "").lower()
        or "archetype" in [t.lower() for t in (getattr(f, "traits", []) or [])]
    ]
    return len(arch_feats) >= 3 * len(dedications)


def enrich_feat_description(feat_name: str, raw_desc: str) -> str:
    desc = raw_desc or ""
    has_parens = "(" in feat_name and ")" in feat_name
    if has_parens and any(k in feat_name.lower() for k in ("domain", "deity")):
        sub_val = feat_name.split("(", 1)[1].rsplit(")", 1)[0].strip()
        if sub_val and sub_val.lower() not in desc.lower():
            d_info = get_domain_info(sub_val)
            sp_name = (d_info.get("domain_spell") or {}).get("name") if isinstance(d_info.get("domain_spell"), dict) else None
            extra = f" Chosen Domain: {sub_val}" + (f" (Domain Spell: {sp_name})." if sp_name else ".")
            desc = f"{desc}{extra}" if desc else extra.strip()
    cleaned = clean_pf2e_text(desc)
    if has_parens:
        subchoice = feat_name.split("(", 1)[1].rstrip(")")
        fn_low = feat_name.lower()
        if "additional lore" in fn_low:
            return f"Chosen Lore: {subchoice}. (Scales automatically: Trained at 1st, Expert at 3rd, Master at 7th, Legendary at 15th).\n\n{cleaned}"
        if "spotter" in fn_low or "stalker" in fn_low:
            return f"Selected Environment: {subchoice}.\n\n{cleaned}"
        if "arcane tattoos" in fn_low:
            return f"Chosen Thassilonian School & Innate Arcane Cantrip: {subchoice}.\n\n{cleaned}"
        if "named artillery" in fn_low:
            return f"Named Siege Weapon: {subchoice}.\n\n{cleaned}"
    return cleaned


def pick_weighted_feat(
    candidates: list,
    class_name: str,
    owned_names: set,
    skill_ranks: dict,
    mods: dict,
    char_level: int,
    subclass_name: str = "",
    archetype_name: str = "",
) -> Optional[dict]:
    valid = [
        f for f in candidates
        if f["name"] not in owned_names
        and check_feat_prerequisites(
            f, skill_ranks, owned_names, mods, char_level,
            subclass_name=subclass_name, archetype_name=archetype_name,
        )
    ]
    if not valid:
        return None
    weights = [calculate_feat_weight(f, class_name, owned_names, skill_ranks) for f in valid]
    if sum(weights) <= 0:
        return random.choice(valid)
    return random.choices(valid, weights=weights, k=1)[0]


def extract_bg_feat(bg_desc: str, feats_list: list) -> str:
    if not bg_desc:
        return ""
    feat_lookup = {f["name"].lower(): f["name"] for f in feats_list}
    m_uuid = re.search(r"@UUID\[[^\]]*feats-srd\.Item\.([^|\]]+)", bg_desc)
    if not m_uuid:
        m_item = re.search(r"@UUID\[[^\]]*Item\.([^|\]]+)", bg_desc)
        if m_item and not re.search(r"equipment-srd|pathfinder-monster-core|spells-srd|actionspf2e", m_item.group(0), re.IGNORECASE):
            m_uuid = m_item
    if m_uuid:
        c_name = m_uuid.group(1).strip()
        return feat_lookup.get(c_name.lower(), c_name)
    m_choice = re.search(
        r"either\s+([A-Za-z\s'’\-]+?)\s+or\s+([A-Za-z\s'’\-]+?)\s+(?:skill|general)?\s*feat",
        bg_desc,
        re.IGNORECASE,
    )
    if m_choice:
        valid = [
            feat_lookup[opt.strip().lower()]
            for opt in (m_choice.group(1), m_choice.group(2))
            if opt.strip().lower() in feat_lookup
        ]
        if valid:
            return random.choice(valid)
    m_gain = re.search(r"gain the\s+([A-Za-z\s'’\-]+?)\s+(?:skill|general)?\s*feat", bg_desc, re.IGNORECASE)
    if m_gain:
        cand = m_gain.group(1).strip()
        return feat_lookup.get(cand.lower(), cand)
    desc_l = bg_desc.lower()
    for f_low, f_real in feat_lookup.items():
        if len(f_low) > 4 and f" {f_low} " in f" {desc_l} ":
            idx = desc_l.find(f_low)
            if "feat" in desc_l[idx:idx + 50]:
                return f_real
    return ""


def character_has_natural_wings(ancestry_name: str, heritage_name: str, feats: List[FeatSummary]) -> bool:
    anc_l = (ancestry_name or "").lower().strip()
    her_l = (heritage_name or "").lower().strip()
    if anc_l in WING_NATURAL_ANCESTRIES or any(h in her_l for h in WING_NATURAL_HERITAGES):
        return True
    feat_text = " ".join(f"{f.name.lower()} {f.description.lower()}" for f in feats)
    return "wing" in feat_text or "fly speed" in feat_text


def apply_wing_graft_investment(
    ancestry_name: str,
    heritage_name: str,
    chosen_feats: List[FeatSummary],
    equipment_loadout: Any,
) -> None:
    """Injects Wing Graft into equipment and adds an Archetype Feature if the character lacks natural wings."""
    if character_has_natural_wings(ancestry_name, heritage_name, chosen_feats):
        return

    if not any(f.name == "Wing Graft Investment" for f in chosen_feats):
        chosen_feats.append(FeatSummary(
            id="graft-wing-beast-graft",
            name="Wing Graft Investment",
            category="Graft Modification",
            action_cost=None,
            traits=["Invested", "Magical", "Transmutation"],
            description=(
                f"{WING_GRAFT_ITEM['name']} ({WING_GRAFT_ITEM['price']}): "
                f"{WING_GRAFT_ITEM['description']} (Occupies 1 Investiture slot)."
            ),
        ))

    for attr in ("items", "worn"):
        container = getattr(equipment_loadout, attr, None)
        if isinstance(container, list):
            if not any("Wing Graft" in (i if isinstance(i, str) else i.get("name", "")) for i in container):
                container.append(WING_GRAFT_ITEM["name"])
            break


def apply_ostilli_host_graft(chosen_feats: List[FeatSummary], equipment_loadout: Any, level: int) -> None:
    """Injects the Ostilli Symbiote graft and refreshes its level-scaled abilities."""
    spit_dice = 1 + max(0, (level - 2) // 4)
    spit_desc = (
        f"Frequency: once per round. Your ostilli fires a magical dart up to 30 feet "
        f"dealing {spit_dice}d6 piercing damage (basic Reflex save against the higher of your Class DC or Spell DC)."
    )

    feat_map = {f.name.lower(): f for f in chosen_feats}
    if "ostilli symbiote graft" not in feat_map:
        chosen_feats.append(FeatSummary(
            id="graft-ostilli-symbiote",
            name="Ostilli Symbiote Graft",
            category="Graft Modification",
            action_cost=None,
            traits=["Graft", "Magical", "Symbiote"],
            description=f"{OSTILLI_GRAFT_ITEM['name']}: {OSTILLI_GRAFT_ITEM['description']}",
        ))

    if hasattr(equipment_loadout, "gear") and isinstance(equipment_loadout.gear, list):
        if not any("Ostilli Symbiote" in g for g in equipment_loadout.gear):
            equipment_loadout.gear.append(f"{OSTILLI_GRAFT_ITEM['name']} (Tiny Symbiote Graft)")

    if "repel ambient magic" not in feat_map:
        chosen_feats.append(FeatSummary(
            id="ostilli-repel-ambient-magic",
            name="Repel Ambient Magic",
            category="Archetype Action (Ostilli Host)",
            action_cost="1",
            traits=["archetype", "concentrate"],
            description="Your ostilli expels stored magic to shield you, granting a +1 circumstance bonus to AC and saving throws against the next spell, focus spell, or magical attack targeting you until your next turn (+2 at 12th level).",
        ))

    if "spit ambient magic" not in feat_map:
        chosen_feats.append(FeatSummary(
            id="ostilli-spit-ambient-magic",
            name="Spit Ambient Magic",
            category="Archetype Action (Ostilli Host)",
            action_cost="1",
            traits=["archetype", "concentrate", "magical"],
            description=spit_desc,
        ))
    else:
        feat_map["spit ambient magic"].description = spit_desc





def apply_background_starting_package(
    bg_desc: str,
    equipment_loadout: Any,
    collected_partners: List[PartnerCreatureData],
    level: int,
    mods: dict,
) -> None:
    if not bg_desc or not equipment_loadout:
        return

    # Extract explicit Item and Actor UUIDs
    item_matches = re.findall(r"@UUID\[[^\]]*\.Item\.([^|\]]+)", bg_desc)
    actor_matches = re.findall(r"@UUID\[[^\]]*\.Actor\.([^|\]]+)", bg_desc)

    # Also detect "shoddy <Name>" if not already captured
    for m in re.finditer(r"\bshoddy\s+([A-Z][A-Za-z\s\-]+?)(?:\s+armor|[.,;)]|$)", bg_desc):
        cand = f"Shoddy {m.group(1).strip()}"
        if cand not in item_matches:
            item_matches.append(cand)

    weapons_list = equipment_loadout.weapons if isinstance(getattr(equipment_loadout, "weapons", None), list) else []
    gear_list = equipment_loadout.gear if isinstance(getattr(equipment_loadout, "gear", None), list) else []
    strikes_list = equipment_loadout.strikes if isinstance(getattr(equipment_loadout, "strikes", None), list) else []

    weapon_specs = {
        "longsword": ("1d8", "Slashing", ["Versatile P"]),
        "lance": ("1d8", "Piercing", ["Deadly d8", "Jousting"]),
    }
    armor_names = {"half plate", "breastplate", "chain mail", "splint mail", "plate", "scale mail", "hide", "studded leather", "leather"}

    from app.engine.models import Item as EqItem

    for raw_item in item_matches:
        clean_item = re.sub(r"\s+", " ", raw_item.replace("’", "'")).strip()
        low_item = clean_item.lower()
        base_item = re.sub(r"^shoddy\s+", "", low_item).strip()
        is_shoddy = "shoddy" in low_item or f"shoddy {base_item}" in bg_desc.lower()
        display_name = f"{clean_item.title()} (Shoddy -2 item penalty)" if (is_shoddy and "shoddy" not in low_item) else clean_item.title()
        if is_shoddy and "(Shoddy" not in display_name:
            display_name = f"{display_name} (-2 item penalty)"

        if base_item in armor_names:
            cur_armor = getattr(equipment_loadout, "armor", None)
            cur_armor_name = (
                getattr(cur_armor, "name", None)
                or (cur_armor.get("name") if isinstance(cur_armor, dict) else None)
                or (str(cur_armor) if cur_armor else "")
            )
            if base_item not in cur_armor_name.lower():
                new_armor_label = f"{display_name} [over {cur_armor_name}]" if cur_armor_name else display_name
                if isinstance(cur_armor, EqItem):
                    equipment_loadout.armor = cur_armor.model_copy(update={"name": new_armor_label})
                else:
                    equipment_loadout.armor = EqItem(name=new_armor_label)
            if display_name not in gear_list:
                gear_list.append(display_name)
        elif base_item in weapon_specs:
            dice_str, dmg_type, w_traits = weapon_specs[base_item]
            existing_w_names = {
                (getattr(w, "name", None) or (w.get("name") if isinstance(w, dict) else str(w))).lower()
                for w in weapons_list
            }
            if display_name.lower() not in existing_w_names:
                weapons_list.append(EqItem(name=display_name))
            if not any(base_item in (st.name or "").lower() for st in strikes_list):
                atk_val = 2 + level + mods.get("str", 0) + (-2 if is_shoddy else 0)
                str_mod = mods.get("str", 0)
                dmg_dice = f"{dice_str}+{str_mod}" if str_mod > 0 else (f"{dice_str}{str_mod}" if str_mod < 0 else dice_str)
                st_traits = list(w_traits) + (["Shoddy"] if is_shoddy else [])
                strikes_list.append(Strike(
                    name=display_name,
                    attack_bonus=f"+{atk_val}" if atk_val >= 0 else str(atk_val),
                    damage=f"{dmg_dice} {dmg_type}",
                    damage_dice=dmg_dice,
                    damage_type=dmg_type,
                    traits=st_traits,
                    map_second=f"+{atk_val - 5}" if (atk_val - 5) >= 0 else str(atk_val - 5),
                    map_third=f"+{atk_val - 10}" if (atk_val - 10) >= 0 else str(atk_val - 10),
                ))
        else:
            if display_name not in gear_list:
                gear_list.append(display_name)

    equipment_loadout.weapons = weapons_list
    equipment_loadout.gear = gear_list
    equipment_loadout.strikes = strikes_list

    for mount_kw in ("riding horse", "pony", "warhorse", "riding dog", "camel"):
        if mount_kw in bg_desc.lower() and not any(mount_kw in a.lower() for a in actor_matches):
            actor_matches.append(mount_kw.title())

    for raw_actor in actor_matches:
        actor_name = re.sub(r"\s+", " ", raw_actor.replace("’", "'")).strip().title()
        if not any(actor_name.lower() in (p.name or "").lower() for p in collected_partners):
            mount_hp = 8 + (6 * level)
            collected_partners.append(PartnerCreatureData(
                name=actor_name,
                creature_type="Mount",
                sub_type="Animal",
                stage="Starting Mount",
                size="Large",
                speed="40 ft",
                ac=12 + level,
                hp=mount_hp,
                fortitude=f"+{3 + level}",
                reflex=f"+{3 + level}",
                will=f"+{2 + level}",
                perception=f"+{3 + level}",
                strikes=[],
                primary_ability="Mount for overland travel and movement when commanded.",
                secondary_ability="Carries rider and gear according to Encumbrance rules.",
                languages=[],
                traits=["Animal", "Mount"],
                senses="Low-Light Vision, Scent (imprecise, 30 feet)",
                attributes={"STR": "+3", "DEX": "+1", "CON": "+2", "INT": "-4", "WIS": "+1", "CHA": "-2"},
                skills={"Athletics": f"+{3 + level}"},
            ))



_EQUIPMENT_WEAPON_LOOKUP: Optional[Dict[str, Dict[str, Any]]] = None


def _get_equipment_weapon_lookup() -> Dict[str, Dict[str, Any]]:
    global _EQUIPMENT_WEAPON_LOOKUP
    if _EQUIPMENT_WEAPON_LOOKUP is not None:
        return _EQUIPMENT_WEAPON_LOOKUP
    lookup: Dict[str, Dict[str, Any]] = {}
    eq_file = Path(__file__).resolve().parents[2] / "data" / "equipment.json"
    if eq_file.exists():
        try:
            raw_items = json.loads(eq_file.read_text(encoding="utf-8"))
            if isinstance(raw_items, list):
                for item in raw_items:
                    if not isinstance(item, dict):
                        continue
                    itype = str(item.get("type") or "").lower()
                    cat = str(item.get("category") or "").lower()
                    if itype == "weapon" or cat in ("simple", "martial", "advanced", "unarmed"):
                        nm = str(item.get("name") or "").strip()
                        if nm and nm.lower() not in lookup:
                            lookup[nm.lower()] = item
        except Exception:
            pass
    _EQUIPMENT_WEAPON_LOOKUP = lookup
    return _EQUIPMENT_WEAPON_LOOKUP


def _is_natural_strike(strike_obj: Any) -> bool:
    name_low = str(getattr(strike_obj, "name", None) or (strike_obj.get("name") if isinstance(strike_obj, dict) else "") or "").lower()
    raw_traits = getattr(strike_obj, "traits", None) or (strike_obj.get("traits") if isinstance(strike_obj, dict) else []) or []
    traits_low = " ".join(str(t).lower() for t in raw_traits)
    natural_markers = (
        "unarmed", "natural", "claw", "jaws", "fang", "horn", "talon",
        "beak", "pincer", "tail", "wing", "rage strike", "elemental blast"
    )
    return any(m in name_low or m in traits_low for m in natural_markers)


def _build_weapon_strike_entry(weapon_name: str, level: int, mods: dict, cls_name: str, strike_cls: Any) -> Any:
    clean_name = weapon_name.strip().title()
    w_info = _get_equipment_weapon_lookup().get(clean_name.lower()) or {}
    dmg_obj = w_info.get("damage") if isinstance(w_info.get("damage"), dict) else {}
    raw_num = dmg_obj.get("dice")
    try:
        base_num = int(raw_num) if raw_num is not None and str(raw_num).strip() != "" else 1
    except (ValueError, TypeError):
        base_num = 1
    raw_die = str(dmg_obj.get("die") or "").strip().lower()
    if not raw_die:
        raw_die = "d6"
    elif not raw_die.startswith("d"):
        raw_die = f"d{raw_die}"
    die_part = f"{max(1, base_num)}{raw_die}"
    dmg_type = str(dmg_obj.get("damageType") or dmg_obj.get("type") or "Slashing").title()
    w_traits = [str(t).title() for t in (w_info.get("traits") or []) if t]
    if not w_traits:
        w_traits = ["Martial"] if str(w_info.get("category") or "").lower() == "martial" else ["Simple"]

    traits_low = " ".join(t.lower() for t in w_traits)
    is_ranged = "range" in traits_low or "thrown" in traits_low or clean_name.lower() in ("shortbow", "longbow", "sling", "crossbow", "dart", "javelin")
    stat_mod = mods.get("dex", 0) if ("finesse" in traits_low or is_ranged) and mods.get("dex", 0) > mods.get("str", 0) else mods.get("str", 0)

    prof = 2 + level + (2 if level >= 5 else 0) + (2 if level >= 13 else 0) + get_weapon_prof_bonus_delta(cls_name, level)
    atk = prof + stat_mod
    is_agile = "agile" in traits_low
    map2 = atk - (4 if is_agile else 5)
    map3 = atk - (8 if is_agile else 10)

    potency = 3 if level >= 16 else (2 if level >= 10 else (1 if level >= 2 else 0))
    dice_mult = 4 if level >= 19 else (3 if level >= 12 else (2 if level >= 4 else 1))
    striking_label = (
        "Major Striking " if dice_mult == 4 else
        ("Greater Striking " if dice_mult == 3 else ("Striking " if dice_mult == 2 else ""))
    )
    prefix = f"+{potency} {striking_label}" if potency > 0 else striking_label
    scaled_dice = die_part.replace("1d", f"{dice_mult}d", 1) if die_part.startswith("1d") else die_part

    dmg_bonus = 0 if (is_ranged and "propulsive" not in traits_low and "thrown" not in traits_low) else stat_mod
    spec_bonus = get_weapon_spec_bonus(cls_name, level)
    total_dmg_mod = dmg_bonus + spec_bonus
    dmg_str = f"{scaled_dice}+{total_dmg_mod}" if total_dmg_mod > 0 else (f"{scaled_dice}{total_dmg_mod}" if total_dmg_mod < 0 else scaled_dice)

    payload = {
        "name": f"{prefix}{clean_name}",
        "attack_bonus": f"{atk:+d}",
        "map_second": f"{map2:+d}",
        "map_third": f"{map3:+d}",
        "damage_dice": dmg_str,
        "damage_type": dmg_type,
        "traits": w_traits,
    }
    return strike_cls.model_validate(payload) if hasattr(strike_cls, "model_validate") else payload



def _normalize_bonus_str(val: Any) -> str:
    if val is None:
        return "+0"
    s = re.sub(r"\s+", "", str(val).strip())
    s = re.sub(r"^\++", "+", s)
    s = re.sub(r"^\+-", "-", s)
    try:
        n = int(s)
        return f"{n:+d}"
    except ValueError:
        if not s.startswith(("+", "-")):
            return f"+{s}"
        return s


def _dedupe_strikes(strikes: list) -> list:
    deduped = []
    seen_idx = {}
    for st in strikes or []:
        raw_name = str(getattr(st, "name", None) or (st.get("name") if isinstance(st, dict) else "") or "").strip()
        base_key = _RE_RUNE_PREFIX.sub("", raw_name).strip().lower()
        if not base_key:
            deduped.append(st)
            continue
        for attr in ("attack_bonus", "map_second", "map_third"):
            if isinstance(st, dict) and attr in st:
                st[attr] = _normalize_bonus_str(st[attr])
            elif hasattr(st, attr):
                setattr(st, attr, _normalize_bonus_str(getattr(st, attr)))
        if base_key not in seen_idx:
            seen_idx[base_key] = len(deduped)
            deduped.append(st)
        else:
            prev = deduped[seen_idx[base_key]]
            prev_name = str(getattr(prev, "name", None) or (prev.get("name") if isinstance(prev, dict) else "") or "")
            if len(raw_name) >= len(prev_name):
                deduped[seen_idx[base_key]] = st
    return deduped


def enforce_weapon_loadout(
    equipment_loadout: Any,
    deity_summary: Optional[DeitySummary],
    level: int,
    mods: dict,
    cls_name: str,
) -> None:
    if not equipment_loadout or not hasattr(equipment_loadout, "strikes"):
        return

    from app.engine.models import Item as EqItem

    existing_strikes = list(equipment_loadout.strikes or [])
    strike_cls = type(existing_strikes[0]) if existing_strikes else Strike

    natural_strikes = [s for s in existing_strikes if _is_natural_strike(s)]
    non_natural_strikes = [s for s in existing_strikes if not _is_natural_strike(s)]

    favored_name = (getattr(deity_summary, "favored_weapon", None) or "").strip()
    if favored_name:
        fav_low = favored_name.lower()
        already_has_fav = any(
            fav_low in str(getattr(s, "name", None) or (s.get("name") if isinstance(s, dict) else "") or "").lower()
            for s in non_natural_strikes
        )
        if not already_has_fav:
            fav_strike = _build_weapon_strike_entry(favored_name, level, mods, cls_name, strike_cls)
            non_natural_strikes.insert(0, fav_strike)

    backup_candidates = ["Dagger", "Shortsword", "Spear", "Shortbow", "Mace", "Greataxe"]
    for cand in backup_candidates:
        if len(non_natural_strikes) >= 2:
            break
        cand_low = cand.lower()
        if any(
            cand_low in str(getattr(s, "name", None) or (s.get("name") if isinstance(s, dict) else "") or "").lower()
            for s in non_natural_strikes
        ):
            continue
        non_natural_strikes.append(_build_weapon_strike_entry(cand, level, mods, cls_name, strike_cls))

    # Cap non-natural weapons at 2 while keeping all natural attacks
    capped_non_natural = non_natural_strikes[:2]
    equipment_loadout.strikes = _dedupe_strikes(capped_non_natural + natural_strikes)

    # Sync equipment_loadout.weapons list cleanly with the non-natural weapons
    if hasattr(equipment_loadout, "weapons") and isinstance(equipment_loadout.weapons, list):
        synced_weapons = []
        seen_w = set()
        for s in capped_non_natural:
            raw_n = str(getattr(s, "name", None) or (s.get("name") if isinstance(s, dict) else "") or "").strip()
            clean_n = _RE_RUNE_PREFIX.sub("", raw_n).strip()
            if clean_n and clean_n.lower() not in seen_w:
                seen_w.add(clean_n.lower())
                synced_weapons.append(EqItem(name=clean_n))
        equipment_loadout.weapons = synced_weapons


def _build_deity_summary(deity_raw: Optional[Dict[str, Any]], feats: List[FeatSummary]) -> Optional[DeitySummary]:
    if not deity_raw:
        return None
    chosen_doms: List[str] = []
    domain_spell_names: List[str] = []
    for f in (feats or []):
        fname = getattr(f, "name", "") or ""
        low = fname.lower()
        if any(k in low for k in ("domain initiate", "deity's domain", "deitys domain", "splinter faith", "domain acumen", "domain fluency", "advanced domain")) and "(" in fname and ")" in fname:
            inside = fname.split("(", 1)[1].rsplit(")", 1)[0]
            for part in inside.split(","):
                d_clean = part.strip().title()
                if d_clean and d_clean not in chosen_doms:
                    chosen_doms.append(d_clean)
                    info = get_domain_info(d_clean)
                    sp_obj = info.get("domain_spell") if isinstance(info.get("domain_spell"), dict) else None
                    if sp_obj and sp_obj.get("name") and sp_obj["name"] not in domain_spell_names:
                        domain_spell_names.append(str(sp_obj["name"]))
    return DeitySummary(
        name=str(deity_raw.get("name") or ""),
        category=str(deity_raw.get("category") or ""),
        attributes=list(deity_raw.get("attributes") or []),
        sanctification=dict(deity_raw.get("sanctification") or {}),
        domains=dict(deity_raw.get("domains") or {"primary": [], "alternate": []}),
        font=list(deity_raw.get("font") or []),
        favored_weapon=deity_raw.get("favored_weapon"),
        skill=deity_raw.get("skill"),
        chosen_domains=chosen_doms,
        domain_spells=domain_spell_names,
    )


def _sync_deity_focus_spells(sheet: CharacterSheet) -> CharacterSheet:
    deity_obj = getattr(sheet, "deity", None)
    if not deity_obj:
        return sheet
    chosen_doms = list(getattr(deity_obj, "chosen_domains", None) or [])
    if not chosen_doms:
        return sheet

    curr_rank = max(1, (int(getattr(sheet, "level", 1) or 1) + 1) // 2)
    wis_mod = int(getattr(getattr(sheet, "attributes", None), "wis", 0) or 0)
    cha_mod = int(getattr(getattr(sheet, "attributes", None), "cha", 0) or 0)
    int_mod = int(getattr(getattr(sheet, "attributes", None), "int", 0) or 0)
    cls_low = str(getattr(sheet, "char_class", "") or "").lower()
    if "cleric" in cls_low or "druid" in cls_low:
        attr_code, attr_mod = "WIS", wis_mod
    elif "champion" in cls_low or "bard" in cls_low or "oracle" in cls_low or "sorcerer" in cls_low:
        attr_code, attr_mod = "CHA", cha_mod
    else:
        attr_code, attr_mod = "INT", int_mod

    prof_bonus = (4 if int(getattr(sheet, "level", 1) or 1) >= 7 else 2) + int(getattr(sheet, "level", 1) or 1)
    spell_dc = 10 + prof_bonus + attr_mod
    spell_attack = prof_bonus + attr_mod

    existing_fs = getattr(sheet, "focus_spells", None)
    spell_list = list(getattr(existing_fs, "spells", None) or [])
    known_names = {str(getattr(s, "name", "") or "").lower() for s in spell_list}

    for dom in chosen_doms:
        info = get_domain_info(dom)
        for key in ("domain_spell", "advanced_domain_spell"):
            sp_info = info.get(key) if isinstance(info, dict) else None
            if isinstance(sp_info, dict) and sp_info.get("name"):
                sp_name = str(sp_info["name"]).strip()
                if sp_name.lower() in known_names:
                    continue
                known_names.add(sp_name.lower())
                spell_list.append(
                    SpellSummary(
                        name=sp_name,
                        rank=max(curr_rank, int(sp_info.get("rank") or 1)),
                        actions=str(sp_info.get("casting_time") or "1 action"),
                        traits=["Domain", "Focus", "Divine"],
                        description=str(sp_info.get("description") or f"Granted by the {dom} domain ({getattr(deity_obj, 'name', '')})."),
                    )
                )

    if spell_list:
        pool = min(3, max(1, len(spell_list)))
        sheet.focus_spells = FocusSpellData(
            focus_points=max(pool, int(getattr(existing_fs, "focus_points", 0) or 0)),
            max_focus_points=max(pool, int(getattr(existing_fs, "max_focus_points", 0) or 0)),
            tradition=getattr(existing_fs, "tradition", None) or "Divine",
            casting_attribute=getattr(existing_fs, "casting_attribute", None) or attr_code,
            spell_dc=int(getattr(existing_fs, "spell_dc", 0) or 0) or spell_dc,
            spell_attack=int(getattr(existing_fs, "spell_attack", 0) or 0) or spell_attack,
            spells=spell_list,
        )
    return sheet

class PF2eGenerator:
    def __init__(self) -> None:
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

    def generate_character_from_concept(self, concept_text: str) -> dict:
        """Parses a natural-language concept and builds the lowest-level legal PF2e Remastered sheet."""
        from app.engine.concept_builder import ConceptToSheetBuilder
        return ConceptToSheetBuilder(self).build_lowest_level_sheet(concept_text)

    def generate_epic_backstory(self, char_data: dict) -> dict:
        """Calls the Google Gemini API to generate a customized three-chapter backstory."""
        try:
            client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

            name = char_data.get("name") or "The Hero"
            ancestry = char_data.get("ancestry") or "Human"
            heritage = char_data.get("heritage", "")
            cls = char_data.get("character_class") or "Adventurer"
            lvl = int(char_data.get("level") or 1)
            bg = char_data.get("background") or "Unknown"
            archetype = char_data.get("archetype", "None")

            feats = [f.get("name") for f in char_data.get("feats", []) if isinstance(f, dict)]
            skills = [s.get("name") for s in char_data.get("all_skills", []) if isinstance(s, dict) and s.get("rank", 0) >= 2]
            equipment = char_data.get("equipment", {})
            strikes = equipment.get("strikes", []) if isinstance(equipment, dict) else []
            weapons = [w.get("name") for w in strikes if isinstance(w, dict)]
            companion = char_data.get("companion")
            companion_info = (
                f"{companion.get('name')} ({companion.get('creature_type')})"
                if companion and isinstance(companion, dict)
                else "None"
            )

            prompt = f"""
            You are a master fantasy novelist and Pathfinder 2e lore master. Write a deeply immersive, rich, 
            and evocative three-chapter backstory for the following character sheet. Avoid formulaic templates, 
            cliché boilerplate openings, or robotic summaries. Weave their mechanical traits organically into the narrative.

            CHARACTER DATA:
- Name: {name}
- Ancestry & Heritage: {ancestry} ({heritage})
- Background: {bg}
- Class & Level: Level {lvl} {cls}
- Archetype: {archetype}
- Key Trained Skills: {', '.join(skills) if skills else 'General frontier skills'}
- Notable Feats & Abilities: {', '.join(feats[:5]) if feats else 'Standard training'}
- Signature Weapons / Gear: {', '.join(weapons) if weapons else 'Standard gear'}
- Animal Companion / Familiar / Partner: {companion_info}

            FORMAT REQUIREMENT:
            Return the response strictly as a JSON list of objects with "chapter" and "narrative" keys matching this structure:
            [
                {{"chapter": "Chapter I: [Evocative Title]", "narrative": "[Prose text...]"}},
                {{"chapter": "Chapter II: [Evocative Title]", "narrative": "[Prose text...]"}},
                {{"chapter": "Chapter III: [Evocative Title]", "narrative": "[Prose text...]"}}
            ]
            """

            response = None
            last_error = None
            for model_name in ("gemini-3.8-flash-lite", "gemini-3.5-flash-lite"):
                for _ in range(2):
                    try:
                        response = client.models.generate_content(
                            model=model_name,
                            contents=prompt,
                            config=types.GenerateContentConfig(
                                response_mime_type="application/json",
                                temperature=0.85,
                            ),
                        )
                        if response and response.text:
                            break
                    except Exception as e:
                        last_error = e
                        time.sleep(1)
                if response and response.text:
                    break

            if not response or not response.text:
                raise RuntimeError(f"All models busy or failed. Last error: {last_error}")

            raw_text = response.text.strip()
            if raw_text.startswith("```json"):
                raw_text = raw_text[7:]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]

            return {"chapters": json.loads(raw_text.strip())}

        except Exception as e:
            print(f"CRITICAL LLM Backstory Generation Error: {e}")
            return {
                "chapters": [
                    {
                        "chapter": "Generation Error",
                        "narrative": f"Could not generate backstory due to server error: {e}",
                    }
                ]
            }

    def _calc_prof(self, rank_val: int, level: int, attr_mod: int) -> Proficiency:
        prof_bonus, letter = RANK_MAP.get(rank_val, (2, "T"))
        return Proficiency(rank=prof_bonus, rank_letter=letter, modifier=prof_bonus + level + attr_mod)

    def _enforce_granted_feat_skill_prereqs(
        self,
        feats_list: list,
        skills_list: list,
        level: int,
        attrs: dict,
        *,
        include_all_feats: bool = False,
        allow_generic_rk: bool = True,
        fallback_lore_name: str = "Scribing Lore",
    ) -> None:
        """Ensures skills required by background/granted feats meet their minimum proficiency rank."""
        if not isinstance(skills_list, list) or not feats_list:
            return

        cat_by_name = {
            f["name"].strip().lower(): f
            for f in (self.feats or [])
            if isinstance(f, dict) and f.get("name")
        }
        rk_skills = ("arcana", "crafting", "lore", "medicine", "nature", "occultism", "religion", "society")
        generic_tokens = ("at least", "a skill", "any skill", "one skill", "two skill", "three skill", "recall knowledge")

        for fobj in feats_list:
            fname = (fobj.get("name", "") if isinstance(fobj, dict) else getattr(fobj, "name", "") or "").strip()
            fcat = (fobj.get("category", "") if isinstance(fobj, dict) else getattr(fobj, "category", "") or "").strip()
            if not fname:
                continue
            base_low = fname.split("(", 1)[0].strip().lower()
            is_bg_or_special = (
                "background" in fcat.lower()
                or base_low in {"natural medicine", "seasoned", "pilgrim's token"}
            )
            if not include_all_feats and not is_bg_or_special:
                continue

            cat_feat = cat_by_name.get(fname.lower()) or cat_by_name.get(base_low)
            prereqs = list((cat_feat or {}).get("prerequisites") or [])
            if base_low == "natural medicine" and "trained in Nature" not in prereqs:
                prereqs.append("trained in Nature")

            for prereq in prereqs:
                p_low = str(prereq).lower()
                if not allow_generic_rk and any(tok in p_low for tok in generic_tokens):
                    continue
                for rank_word, (req_rank, req_letter) in RANK_WORD_SPECS.items():
                    marker = f"{rank_word} in "
                    if marker not in p_low:
                        continue
                    tail = p_low.split(marker, 1)[1]
                    options = [
                        part.removeprefix("or ").strip().rstrip(".")
                        for chunk in tail.split(",")
                        for part in chunk.split(" or ")
                        if part.removeprefix("or ").strip().rstrip(".")
                    ]
                    if not options:
                        break

                    opt_set = {o.lower() for o in options}
                    already_met = any(
                        ((sk.get("name", "") if isinstance(sk, dict) else getattr(sk, "name", "") or "").strip().lower() in opt_set)
                        and int((sk.get("rank") if isinstance(sk, dict) else getattr(sk, "rank", 0)) or 0) >= req_rank
                        for sk in skills_list
                    )
                    if already_met:
                        break

                    target_sk = options[-1].strip().lower()
                    if "at least one skill" in target_sk:
                        break

                    if allow_generic_rk and ("recall knowledge" in target_sk or "a skill with" in target_sk):
                        has_rk = any(
                            any(rk in ((s.get("name", "") if isinstance(s, dict) else getattr(s, "name", "") or "").lower()) for rk in rk_skills)
                            and int((s.get("rank") if isinstance(s, dict) else getattr(s, "rank", 0)) or 0) >= req_rank
                            for s in skills_list
                        )
                        if not has_rk:
                            for s in skills_list:
                                s_name = (s.get("name", "") if isinstance(s, dict) else getattr(s, "name", "") or "").lower()
                                if any(rk in s_name for rk in rk_skills):
                                    cur_r = int((s.get("rank") if isinstance(s, dict) else getattr(s, "rank", 0)) or 0)
                                    if cur_r < req_rank:
                                        delta = req_rank - cur_r
                                        if isinstance(s, dict):
                                            s["rank"] = req_rank
                                            s["rank_letter"] = req_letter
                                            s["modifier"] = int(s.get("modifier") or 0) + delta
                                        else:
                                            s.rank = req_rank
                                            s.rank_letter = req_letter
                                            s.modifier = int(getattr(s, "modifier", 0) or 0) + delta
                                    break
                        break

                    matched = False
                    for sk in skills_list:
                        sk_low = (sk.get("name", "") if isinstance(sk, dict) else getattr(sk, "name", "") or "").strip().lower()
                        if sk_low == target_sk or (target_sk == "lore" and "lore" in sk_low):
                            matched = True
                            cur_r = int((sk.get("rank") if isinstance(sk, dict) else getattr(sk, "rank", 0)) or 0)
                            if cur_r < req_rank:
                                delta = req_rank - cur_r
                                if isinstance(sk, dict):
                                    sk["rank"] = req_rank
                                    sk["rank_letter"] = req_letter
                                    sk["modifier"] = int(sk.get("modifier") or 0) + delta
                                else:
                                    sk.rank = req_rank
                                    sk.rank_letter = req_letter
                                    sk.modifier = int(getattr(sk, "modifier", 0) or 0) + delta

                    if not matched:
                        lore_label = fallback_lore_name if target_sk == "lore" else target_sk.title()
                        attr_code = "INT" if ("lore" in lore_label.lower() or "crafting" in target_sk) else "WIS"
                        attr_mod = int((attrs or {}).get(attr_code.lower(), 0) or 0)
                        sample = skills_list[0] if skills_list else None
                        if isinstance(sample, dict):
                            skills_list.append({
                                "name": lore_label,
                                "attribute": attr_code,
                                "rank": req_rank,
                                "rank_letter": req_letter,
                                "modifier": level + req_rank + attr_mod,
                            })
                        else:
                            skills_list.append(SkillEntry(
                                name=lore_label,
                                attribute=attr_code,
                                rank=req_rank,
                                rank_letter=req_letter,
                                modifier=level + req_rank + attr_mod,
                            ))
                    break

    def _grant_tier3_feats(
        self,
        *,
        lvl: int,
        anc_name: str,
        cls_name: str,
        subclass_name: str = "",
        chosen_feats: List[FeatSummary],
        existing_feat_names: Set[str],
        archetype_data: Optional[dict],
        gate_elements: set,
        mods: dict,
        total_hp: int,
        bonus_speed: int,
    ) -> Tuple[int, int]:
        cls_lower = cls_name.lower()
        anc_lower = anc_name.lower()
        arch_name = archetype_data.get("name", "") if archetype_data else ""

        if lvl in (11, 15, 19):
            gen_pool = [
                f for f in self.feats
                if f.get("category") == "general"
                and f.get("level", 1) <= lvl
                and f["name"] not in existing_feat_names
                and can_take_dedication(f["name"], chosen_feats, existing_feat_names)
                and check_feat_prerequisites(f, {}, existing_feat_names, mods, lvl, subclass_name=subclass_name, archetype_name=arch_name)
            ]
            if gen_pool:
                gf = random.choice(gen_pool)
                gf_name = resolve_feat_subchoices(gf["name"], existing_feat_names)
                if gf["id"] == "toughness":
                    total_hp += lvl
                elif gf["id"] == "fleet":
                    bonus_speed += 5
                chosen_feats.append(FeatSummary(
                    id=gf["id"],
                    name=gf_name,
                    category=f"General (Level {lvl})",
                    action_cost=safe_action_cost(gf.get("action_cost")),
                    traits=gf.get("traits", ["general"]),
                    description=enrich_feat_description(gf_name, gf.get("description", "")),
                ))
                existing_feat_names.add(gf_name)

        if lvl in (12, 14, 16, 18, 20):
            arch_key = f"level_{lvl}_feats"
            arch_pool = [
                f for f in (archetype_data.get(arch_key) or archetype_data.get("level_10_feats") or [])
                if f["name"] not in existing_feat_names
            ] if archetype_data else []
            if arch_pool and random.random() < 0.6:
                af = random.choice(arch_pool)
                chosen_feats.append(FeatSummary(
                    id=af["id"],
                    name=af["name"],
                    category=f"Archetype ({archetype_data['name']})",
                    action_cost=safe_action_cost(af.get("action_cost")),
                    traits=af.get("traits", ["archetype"]),
                    description=clean_pf2e_text(af.get("description", "")),
                ))
                existing_feat_names.add(af["name"])
            else:
                cls_pool = [
                    f for f in self.feats
                    if f.get("category") == "class"
                    and f.get("level") in (lvl - 2, lvl)
                    and cls_lower in [t.lower() for t in f.get("traits", [])]
                    and (cls_lower != "kineticist" or is_kineticist_feat_allowed(f, gate_elements))
                    and f["name"] not in existing_feat_names
                    and check_feat_prerequisites(f, {}, existing_feat_names, mods, lvl, subclass_name=subclass_name, archetype_name=arch_name)
                ]
                if cls_pool:
                    cf = pick_weighted_feat(cls_pool, cls_name, existing_feat_names, {}, mods, lvl, subclass_name=subclass_name, archetype_name=arch_name) or random.choice(cls_pool)
                    chosen_feats.append(FeatSummary(
                        id=cf["id"],
                        name=cf["name"],
                        category=f"Class (Level {lvl})",
                        action_cost=safe_action_cost(cf.get("action_cost")),
                        traits=cf.get("traits", [cls_lower]),
                        description=clean_pf2e_text(cf.get("description", "")),
                    ))
                    existing_feat_names.add(cf["name"])

        if lvl in (13, 17):
            anc_pool = [
                f for f in self.feats
                if f.get("category") == "ancestry"
                and f.get("level", 1) <= lvl
                and anc_lower in [t.lower() for t in f.get("traits", [])]
                and f["name"] not in existing_feat_names
                and can_take_dedication(f["name"], chosen_feats, existing_feat_names)
                and check_feat_prerequisites(f, {}, existing_feat_names, mods, lvl, subclass_name=subclass_name, archetype_name=arch_name)
            ]
            if anc_pool:
                af13 = random.choice(anc_pool)
                chosen_feats.append(FeatSummary(
                    id=af13["id"],
                    name=af13["name"],
                    category=f"Ancestry (Level {lvl})",
                    action_cost=safe_action_cost(af13.get("action_cost")),
                    traits=af13.get("traits", [anc_lower]),
                    description=clean_pf2e_text(af13.get("description", "")),
                ))
                existing_feat_names.add(af13["name"])

        if lvl in (12, 14, 15, 16, 18, 20) or (lvl in (11, 13, 17, 19) and cls_lower in ("rogue", "investigator")):
            sk_pool = [
                f for f in self.feats
                if f.get("category") == "skill"
                and f.get("name", "").lower() != "cushion landing"
                and "archetype" not in [t.lower() for t in f.get("traits", [])]
                and f.get("level", 1) <= lvl
                and f["name"] not in existing_feat_names
                and ("additional lore" not in f["name"].lower() or can_take_additional_lore(existing_feat_names, cls_name, arch_name))
                and check_feat_prerequisites(f, {}, existing_feat_names, mods, lvl, subclass_name=subclass_name, archetype_name=arch_name)
            ]
            if sk_pool:
                sf = pick_weighted_feat(sk_pool, cls_name, existing_feat_names, {}, mods, lvl) or random.choice(sk_pool)
                sf_name = resolve_feat_subchoices(sf["name"], existing_feat_names)
                chosen_feats.append(FeatSummary(
                    id=sf["id"],
                    name=sf_name,
                    category=f"Skill (Level {lvl})",
                    action_cost=safe_action_cost(sf.get("action_cost")),
                    traits=sf.get("traits", ["skill"]),
                    description=enrich_feat_description(sf_name, sf.get("description", "")),
                ))
                existing_feat_names.add(sf_name)

        return total_hp, bonus_speed

    def _finalize_sheet(
        self,
        *,
        name: str,
        level: int,
        anc: dict,
        ancestry_description: str,
        heritage_name: str,
        background_name: str,
        background_description: str,
        cls: dict,
        subclass_data: Optional[dict],
        subclass_obj: Optional[SubclassSummary],
        archetype_name: Optional[str],
        archetype_description: Optional[str],
        size: str,
        speed: int,
        mods: dict,
        calculated_ac: int,
        shield_bonus: int,
        total_hp: int,
        fort_prof: Proficiency,
        ref_prof: Proficiency,
        will_prof: Proficiency,
        perception_prof: Proficiency,
        all_skills: list,
        equipment_loadout: Any,
        chosen_feats: List[FeatSummary],
        traits: List[str],
        existing_partners: Optional[List[PartnerCreatureData]] = None,
        existing_languages: Optional[List[str]] = None,
        old_int: int = 0,
        concept_text: Optional[str] = None,
        deity_name: Optional[str] = None,
        domain_name: Optional[str] = None,
    ) -> CharacterSheet:
        cls_name_lower = cls["name"].lower()
        sub_name = (
            subclass_data.get("name")
            if isinstance(subclass_data, dict)
            else (subclass_obj.name if subclass_obj else None)
        )
        arch_str = (archetype_name or "").lower()

        if cls_name_lower != "necromancer" and "reanimator" not in arch_str:
            chosen_feats = [f for f in chosen_feats if f.name.lower() != "sepulchral sublimation"]
        if cls_name_lower == "inventor" and "construct" not in (sub_name or "").lower() and "clockwork reanimator" not in arch_str:
            chosen_feats = [
                f for f in chosen_feats
                if not any(
                    k in f.name.lower()
                    for k in ("prototype companion", "construct companion", "advanced construct", "incredible construct", "paragon construct")
                )
            ]

        sub_combined = f"{sub_name or ''} {getattr(subclass_obj, 'name', '') or ''}".lower()
        collected_partners: List[PartnerCreatureData] = list(existing_partners) if existing_partners else []
        anc_label = anc["name"] if isinstance(anc, dict) else str(anc or "")

        if cls_name_lower == "summoner" and not any("eidolon" in (p.creature_type or "").lower() for p in collected_partners):
            eidolon_partner = resolve_eidolon(master_hp=total_hp, level=level, eidolon_type=sub_name or "")
            if eidolon_partner:
                collected_partners.append(eidolon_partner)

        if (cls_name_lower == "inventor" and "construct" in sub_combined) or "inventor" in arch_str:
            if not any("construct" in (p.creature_type or "").lower() for p in collected_partners):
                collected_partners.append(resolve_construct_companion(master_int_mod=mods["int"], level=level))

        if cls_name_lower == "druid" and "animal" in sub_combined and not any(is_animal_partner(p) for p in collected_partners):
            comp = resolve_companion(
                class_name=cls["name"],
                feats=chosen_feats or [],
                archetype=None,
                level=level,
                force_qualify=True,
                concept_text=concept_text,
                ancestry_name=anc_label,
                heritage_name=heritage_name or "",
                background_name="",
                subclass_name=sub_name or "",
            )
            if comp:
                collected_partners.append(comp)

        if cls_name_lower == "ranger" and not any(is_animal_partner(p) for p in collected_partners):
            comp = resolve_companion(
                class_name=cls["name"],
                feats=chosen_feats or [],
                archetype=None,
                level=level,
                force_qualify=True,
                concept_text=concept_text,
                ancestry_name=anc_label,
                heritage_name=heritage_name or "",
                background_name="",
                subclass_name=sub_name or "",
            )
            if comp:
                collected_partners.append(comp)

        if cls_name_lower == "champion" and level >= 1 and not any(is_animal_partner(p) for p in collected_partners):
            comp = resolve_companion(class_name="Champion", feats=chosen_feats or [], archetype=None, level=level, force_qualify=True)
            if comp:
                comp.name = "Faithful Steed"
                comp.creature_type = "Animal Companion"
                collected_partners.append(comp)

        if cls_name_lower == "witch" and not any("familiar" in (p.creature_type or "").lower() for p in collected_partners):
            fam_fn = resolve_specific_familiar if (level >= 4 and random.random() < 0.5) else resolve_familiar
            fam_kwargs = dict(
                master_ac=calculated_ac,
                master_fort=fort_prof.modifier,
                master_ref=ref_prof.modifier,
                master_will=will_prof.modifier,
                master_perception=perception_prof.modifier,
                level=level,
            )
            if fam_fn is resolve_familiar:
                fam_kwargs["class_name"] = cls["name"]
                fam_kwargs["description_text"] = concept_text
            collected_partners.append(fam_fn(**fam_kwargs))

        collected_partners = sync_feat_partners(
            existing_partners=collected_partners,
            chosen_feats=chosen_feats,
            archetype_name=archetype_name,
            class_name=cls["name"],
            level=level,
            master_ac=calculated_ac,
            master_fort=fort_prof.modifier,
            master_ref=ref_prof.modifier,
            master_will=will_prof.modifier,
            master_perception=perception_prof.modifier,
            master_hp=total_hp,
            concept_text=concept_text,
            ancestry_name=anc_label,
            heritage_name=heritage_name or "",
            background_name="",
            subclass_name=sub_name or "",
        )

        primary_companion = collected_partners[0] if collected_partners else None
        extra_partners = collected_partners[1:] if len(collected_partners) > 1 else []

        spellcasting_data = resolve_spellcasting(
            class_name=cls["name"],
            attribute_mods=mods,
            level=level,
            subclass_name=sub_name,
            feats=chosen_feats,
            concept_text=concept_text,
        )

        focus_data = resolve_focus_spells(
            class_name=cls["name"],
            feats=chosen_feats,
            attribute_mods=mods,
            subclass_name=sub_name,
            level=level,
        )

        if existing_languages is None:
            assigned_langs: List[str] = []
            assigned_lower: Set[str] = set()

            def add_language(lang_name: str) -> None:
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
                for lang in raw_anc_langs:
                    add_language(lang)
            else:
                add_language("Common")
            if "common" not in assigned_lower:
                add_language("Common")
            int_gain = max(0, mods.get("int", 0))
        else:
            assigned_langs = list(existing_languages)
            assigned_lower = {l.lower() for l in assigned_langs}
            int_gain = max(0, mods.get("int", 0) - old_int)

        for _ in range(int_gain):
            avail_pool = [l for l in COMMON_LANG_POOL if l.lower() not in assigned_lower]
            if avail_pool:
                chosen_bonus = random.choice(avail_pool)
                assigned_langs.append(chosen_bonus)
                assigned_lower.add(chosen_bonus.lower())

        if (
            cls_name_lower == "druid"
            or "druid" in arch_str
            or any("druid dedication" in f.name.lower() for f in chosen_feats)
        ):
            if "wildsong" not in assigned_lower:
                assigned_langs.append("Wildsong")
                assigned_lower.add("wildsong")

        if (
            "ostilli host" in arch_str
            or any("ostilli host" in f.name.lower() or "ostilli symbiote" in f.name.lower() for f in chosen_feats)
        ):
            apply_ostilli_host_graft(chosen_feats, equipment_loadout, level)

        for f in chosen_feats:
            f_low = f.name.lower()
            if f_low == "sneak attack":
                cur_dice = get_sneak_attack_dice(level, is_archetype=False)
                f.description = f"When your Strike hits an off-guard target and deals damage, you deal an extra {cur_dice} precision damage."
            elif f_low == "sneak attacker":
                cur_dice = get_sneak_attack_dice(level, is_archetype=True)
                f.description = f"You gain the Sneak Attack class feature, dealing an extra {cur_dice} precision damage to off-guard targets."

        if any("sneak attack" in f.name.lower() or "sneak attacker" in f.name.lower() for f in chosen_feats):
            is_arch_sneak = any("sneak attacker" in f.name.lower() for f in chosen_feats) and cls_name_lower != "rogue"
            s_dice_val = get_sneak_attack_dice(level, is_archetype=is_arch_sneak)
            for st in equipment_loadout.strikes:
                if "precision" not in st.damage_dice.lower() and "sneak" not in st.damage_dice.lower():
                    st.damage_dice = f"{st.damage_dice} (+{s_dice_val} precision vs off-guard)"

        for partner in collected_partners:
            p_type = (getattr(partner, "creature_type", "") or "").lower()
            p_stage = (getattr(partner, "stage", "") or "").lower()
            if "pet" in p_type or "pet" in p_stage:
                partner.hp = 5 * level
                partner.perception = 3 + level

        # Deduplicate feats while preserving order
        seen_feats: Set[str] = set()
        deduped_feats: List[FeatSummary] = []
        for f in (chosen_feats or []):
            fn = (f.name or "").strip().lower()
            if fn and (fn not in seen_feats or "additional lore" in fn):
                seen_feats.add(fn)
                deduped_feats.append(f)
        chosen_feats = deduped_feats

        # Ensure Hobnobber grants at least Trained Diplomacy
        if any("hobnobber" in (getattr(f, "name", "") or str(f)).lower() for f in chosen_feats):
            for sk in (all_skills or []):
                sk_name = (getattr(sk, "name", None) if not isinstance(sk, dict) else sk.get("name", "")) or ""
                if sk_name.lower() == "diplomacy":
                    cur_rank = (getattr(sk, "rank_letter", None) if not isinstance(sk, dict) else sk.get("rank_letter", "U")) or "U"
                    if cur_rank.upper() == "U":
                        trained_mod = level + 2 + int(mods.get("cha", 0))
                        if isinstance(sk, dict):
                            sk["rank_letter"] = "T"
                            sk["rank"] = 2
                            sk["modifier"] = max(int(sk.get("modifier", 0)), trained_mod)
                        else:
                            sk.rank_letter = "T"
                            if hasattr(sk, "rank"):
                                sk.rank = 2
                            sk.modifier = max(int(getattr(sk, "modifier", 0)), trained_mod)

        # Ensure Yaoguai Historian grants Trained Occultism and Yaoguai Lore
        if any("yaoguai historian" in (getattr(f, "name", "") or str(f)).lower() for f in chosen_feats):
            t_bonus = level + 2 + int(mods.get("int", 0))
            has_yaoguai_lore = False
            for sk in (all_skills or []):
                sk_low = ((getattr(sk, "name", None) if not isinstance(sk, dict) else sk.get("name", "")) or "").strip().lower()
                if sk_low in ("occultism", "yaoguai lore"):
                    if sk_low == "yaoguai lore":
                        has_yaoguai_lore = True
                    cur_rank = (getattr(sk, "rank_letter", None) if not isinstance(sk, dict) else sk.get("rank_letter", "U")) or "U"
                    if cur_rank.upper() == "U":
                        if isinstance(sk, dict):
                            sk["rank_letter"] = "T"
                            sk["rank"] = 2
                            sk["modifier"] = max(int(sk.get("modifier", 0)), t_bonus)
                        else:
                            sk.rank_letter = "T"
                            if hasattr(sk, "rank"):
                                sk.rank = 2
                            sk.modifier = max(int(getattr(sk, "modifier", 0)), t_bonus)
            if not has_yaoguai_lore and isinstance(all_skills, list):
                sample = all_skills[0] if all_skills else None
                if isinstance(sample, dict):
                    all_skills.append({
                        "name": "Yaoguai Lore",
                        "attribute": "INT",
                        "rank_letter": "T",
                        "rank": 2,
                        "modifier": t_bonus,
                        "is_lore": True,
                    })
                elif sample is not None:
                    try:
                        all_skills.append(type(sample)(
                            name="Yaoguai Lore",
                            attribute="INT",
                            rank_letter="T",
                            rank=2,
                            modifier=t_bonus,
                        ))
                    except Exception:
                        pass

        # Surface core subclass / methodology features as earned entries on the sheet
        sub_lower = (sub_name or "").strip().lower()
        earned_sub_features = []
        if cls_name_lower == "investigator" and "interrogation" in sub_lower:
            earned_sub_features.append({
                "id": "feat-class-feature-pointed-question",
                "name": "Pointed Question",
                "level": 1,
                "category": "Class Feature",
                "action_cost": 1,
                "traits": ["concentrate", "investigator", "linguistic", "mental"],
                "description": (
                    "1 Action. You press a suspect with a sharp, targeted question. "
                    "Attempt a Diplomacy or Intimidation check against the target's Will DC "
                    "(adding your Pursue a Lead investigation bonus if the target relates to an active investigation). "
                    "On a success, they answer truthfully or reveal a useful clue; on a critical success, "
                    "they reveal additional details and cannot lie about the answer."
                ),
            })

        existing_feat_names_lower = {(getattr(f, "name", "") or "").strip().lower() for f in chosen_feats}
        for ef in earned_sub_features:
            if ef["name"].lower() not in existing_feat_names_lower:
                chosen_feats.append(FeatSummary(**ef))
                existing_feat_names_lower.add(ef["name"].lower())

        # Resolve any remaining parenthetical feat subchoices
        all_feat_names_final = {getattr(f, "name", str(f)) for f in chosen_feats}
        for f_obj in chosen_feats:
            orig_n = getattr(f_obj, "name", None)
            if isinstance(orig_n, str) and "(" not in orig_n:
                _fin_cls_name = cls.get("name") if isinstance(cls, dict) else getattr(cls, "name", None)
                _fin_deity = select_deity(deity_name=deity_name, class_name=_fin_cls_name, background_name=background_name, ancestry_name=anc.get("name") if isinstance(anc, dict) else getattr(anc, "name", None), subclass_name=sub_name, domain_name=domain_name, concept_text=concept_text)
                updated_n = resolve_feat_subchoices(orig_n, all_feat_names_final, _fin_deity.get("name") if isinstance(_fin_deity, dict) else None)
                if updated_n != orig_n:
                    f_obj.name = updated_n
                    all_feat_names_final.add(updated_n)
                    if hasattr(f_obj, "description"):
                        f_obj.description = enrich_feat_description(updated_n, getattr(f_obj, "description", "") or "")

        _fin_cls_name = cls.get("name") if isinstance(cls, dict) else getattr(cls, "name", None)
        _fin_deity_raw = select_deity(deity_name=deity_name, class_name=_fin_cls_name, background_name=background_name, ancestry_name=anc.get("name") if isinstance(anc, dict) else getattr(anc, "name", None), subclass_name=sub_name, domain_name=domain_name, concept_text=concept_text)
        deity_summary = _build_deity_summary(_fin_deity_raw, chosen_feats)
        enforce_weapon_loadout(equipment_loadout, deity_summary, level, mods, cls["name"])
        if deity_summary and domain_name and domain_name.strip().lower() not in ("", "any", "any domain", "none"):
            clean_dom = domain_name.strip().title()
            if clean_dom not in deity_summary.chosen_domains:
                deity_summary.chosen_domains.insert(0, clean_dom)
            dom_info = get_domain_info(clean_dom)
            sp_obj = dom_info.get("domain_spell") if isinstance(dom_info, dict) else None
            if isinstance(sp_obj, dict) and sp_obj.get("name"):
                if sp_obj["name"] not in deity_summary.domain_spells:
                    deity_summary.domain_spells.insert(0, sp_obj["name"])
        apply_background_starting_package(
            bg_desc=background_description or "",
            equipment_loadout=equipment_loadout,
            collected_partners=collected_partners,
            level=level,
            mods=mods,
        )
        primary_companion = collected_partners[0] if collected_partners else None
        extra_partners = collected_partners[1:] if len(collected_partners) > 1 else []
        raw_sheet = CharacterSheet(
            name=name,
            level=level,
            ancestry=anc["name"],
            ancestry_description=ancestry_description,
            heritage=heritage_name,
            background=background_name,
            background_description=background_description,
            character_class=cls["name"],
            subclass=subclass_obj,
            deity=deity_summary,
            archetype=archetype_name,
            archetype_description=archetype_description,
            size=size,
            speed=speed,
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
            languages=assigned_langs,
            traits=traits,
        )

        try:
            validated_dict = sanitize_and_validate_sheet(raw_sheet.model_dump())
            validated_dict.pop("validation_warnings", None)
            self._enforce_granted_feat_skill_prereqs(
                validated_dict.get("feats") or [],
                validated_dict.get("all_skills") or [],
                int(validated_dict.get("level") or 1),
                validated_dict.get("attributes") or {},
                include_all_feats=False,
                allow_generic_rk=True,
                fallback_lore_name="Scribing Lore",
            )
            return CharacterSheet.model_validate(validated_dict)
        except Exception as exc:
            print(f"Pre-export validator warning (falling back to raw sheet): {exc}")
            return raw_sheet

    def _sync_feat_skill_prereqs(self, sheet: CharacterSheet) -> CharacterSheet:
        """Ensures skills required by granted feats (such as Nature for Natural Medicine) meet required ranks."""
        attrs_obj = getattr(sheet, "attributes", None)
        attrs_dict = attrs_obj.model_dump() if hasattr(attrs_obj, "model_dump") else (attrs_obj if isinstance(attrs_obj, dict) else {})
        self._enforce_granted_feat_skill_prereqs(
            getattr(sheet, "feats", None) or [],
            getattr(sheet, "all_skills", None) or [],
            int(getattr(sheet, "level", 1) or 1),
            attrs_dict,
            include_all_feats=True,
            allow_generic_rk=False,
            fallback_lore_name="Lore",
        )
        return sheet

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
        subclass_name: Optional[str] = None,
        concept_text: Optional[str] = None,
        requested_feats: Optional[List[str]] = None,
        deity_name: Optional[str] = None,
        domain_name: Optional[str] = None,
    ) -> CharacterSheet:
        level = max(1, min(20, int(level)))

        if ancestry_name:
            ancestry_name = ancestry_name.replace("Sukri", "Surki").replace("sukri", "surki")
        anc = (
            self.ancestries[ancestry_name.lower()]
            if ancestry_name and ancestry_name.lower() in self.ancestries
            else random.choice(list(self.ancestries.values()))
        )
        cls = (
            self.classes[class_name.lower()]
            if class_name and class_name.lower() in self.classes
            else random.choice(list(self.classes.values()))
        )
        cls_name_lower = (cls["name"] if isinstance(cls, dict) else str(cls)).lower()

        if background_name and background_name.strip():
            matched_bg = next(
                (b for b in self.backgrounds.values() if b["name"].lower() == background_name.strip().lower()),
                None,
            )
            bg = matched_bg or random.choice(list(self.backgrounds.values()))
        else:
            char_anc_name = anc.get("name", "") if isinstance(anc, dict) else getattr(anc, "name", "")
            eligible_bgs = [b for b in self.backgrounds.values() if is_background_compatible_with_ancestry(b, char_anc_name)]
            bg = random.choice(eligible_bgs) if eligible_bgs else random.choice(list(self.backgrounds.values()))

        surki_heritages = {h["name"].lower(): h for h in ANCESTRY_HERITAGES.get("surki", [])}
        clean_her = str(heritage_name).strip() if heritage_name else ""
        if clean_her and clean_her.lower() not in ("none", ""):
            if clean_her.lower() in surki_heritages and anc["name"].lower() != "surki":
                heritage_data = resolve_heritage(anc["name"])
            elif clean_her.lower() in surki_heritages:
                heritage_data = dict(surki_heritages[clean_her.lower()])
            else:
                heritage_data = {"name": clean_her, "description": ""}
        else:
            heritage_data = resolve_heritage(anc["name"])

        if subclass_name and str(subclass_name).strip() and str(subclass_name).strip().lower() not in ("none", ""):
            subclass_data = {"name": str(subclass_name).strip(), "title": "Subclass", "description": ""}
        else:
            subclass_data = resolve_subclass(cls["name"])

        sub_n_val = subclass_data.get("name", "") if isinstance(subclass_data, dict) else getattr(subclass_data, "name", "")

        try:
            fallback_name = generate_golarion_name(anc["name"])
        except Exception:
            fallback_name = f"Hero of {anc['name'].capitalize()}"
        resolved_name = char_name.strip() if char_name and char_name.strip() else fallback_name

        raw_arch = archetype_name.strip() if archetype_name and archetype_name.strip() else ""
        clean_arch_input = None if raw_arch.lower() in ("", "any", "any archetype", "none", "random") else raw_arch
        archetype_data = None
        if clean_arch_input:
            clean_arch_input = clean_arch_input.replace("-multiclass", "").replace("-", " ").strip()
            archetype_data = resolve_dynamic_archetype(clean_arch_input, self.feats)

        # Attribute boosts & flaws
        mods = {attr: 0 for attr in ATTRIBUTES}
        key_options = (
            [ATTR_NAME_TO_SHORT[k.lower()] for k in cls.get("key_attributes", []) if k.lower() in ATTR_NAME_TO_SHORT]
            or (["int", "cha"] if cls_name_lower == "psychic" else [])
        )
        key_attr = random.choice(key_options) if key_options else "str"

        applied_anc_boosts: Set[str] = set()
        for boost_option in anc.get("boosts", []):
            valid_targets = [b.lower() for b in boost_option if b.lower() in ATTRIBUTES and b.lower() not in applied_anc_boosts]
            if not valid_targets:
                valid_targets = [a for a in ATTRIBUTES if a not in applied_anc_boosts]
            chosen_target = key_attr if key_attr in valid_targets else random.choice(valid_targets)
            mods[chosen_target] += 1
            applied_anc_boosts.add(chosen_target)

        for flaw_option in anc.get("flaws", []):
            for fl in flaw_option:
                fl_low = fl.lower()
                if fl_low in mods and fl_low != key_attr:
                    mods[fl_low] -= 1

        applied_bg_boosts: Set[str] = set()
        for boost_option in bg.get("boosts", []):
            valid_targets = [
                b.lower() for b in boost_option
                if b.lower() in ATTRIBUTES and b.lower() not in applied_bg_boosts and mods[b.lower()] < 4
            ]
            if not valid_targets:
                valid_targets = [a for a in ATTRIBUTES if a not in applied_bg_boosts and mods[a] < 4]
            if valid_targets:
                chosen_target = key_attr if key_attr in valid_targets else random.choice(valid_targets)
                mods[chosen_target] += 1
                applied_bg_boosts.add(chosen_target)

        if mods[key_attr] < 4:
            mods[key_attr] += 1

        free_boosts_applied: Set[str] = set()
        for attr in [key_attr, "con", "dex", "wis", "str", "cha", "int"] + ATTRIBUTES:
            if len(free_boosts_applied) < 4 and attr not in free_boosts_applied and mods[attr] < 4:
                mods[attr] += 1
                free_boosts_applied.add(attr)
            if mods[attr] > 4:
                mods[attr] = 4

        if not archetype_data and use_dedication and level >= 2:
            archetype_data = pick_archetype(cls["name"], {}, mods, self.feats)

        mods = apply_remaster_level_boosts(mods, key_attr, level)

        # Saves & Perception
        fort_rank, ref_rank, will_rank, perception_rank = get_class_saving_throws(
            cls["name"],
            cls.get("saving_throws", {}).get("fortitude", 1),
            cls.get("saving_throws", {}).get("reflex", 1),
            cls.get("saving_throws", {}).get("will", 1),
            cls.get("perception", 1),
            level,
        )
        resilient_bonus = get_fundamental_rune_tiers(level)["save_item_bonus"]
        fort_prof = self._calc_prof(fort_rank, level, mods["con"])
        ref_prof = self._calc_prof(ref_rank, level, mods["dex"])
        will_prof = self._calc_prof(will_rank, level, mods["wis"])
        fort_prof.modifier += resilient_bonus
        ref_prof.modifier += resilient_bonus
        will_prof.modifier += resilient_bonus
        perception_prof = self._calc_prof(perception_rank, level, mods["wis"])

        arch_n = clean_arch_input or (archetype_data["name"] if archetype_data else "")
        pinned_req_feats = [
            matched
            for rf in (requested_feats or [])
            if str(rf).strip()
            for matched in [next(
                (f for f in self.feats if isinstance(f, dict) and str(f.get("name", "")).strip().lower() == str(rf).strip().lower()),
                None,
            )]
            if matched is not None
        ]

        equipment_loadout, calculated_ac, shield_bonus = resolve_equipment(
            cls["name"],
            str_mod=mods["str"],
            dex_mod=mods["dex"],
            level=level,
            ancestry_name=anc["name"],
            heritage_name=heritage_data["name"],
            subclass_name=sub_n_val,
            archetype_name=arch_n,
            feats=pinned_req_feats,
        )

        # Archer Archetype 3rd Weapon Bow Guarantee
        if level >= 2 and "archer" in (arch_n or "").lower() and equipment_loadout and equipment_loadout.strikes:
            if not any(any(kw in (st.name or "").lower() for kw in ("bow", "shortbow", "longbow")) for st in equipment_loadout.strikes):
                equipment_loadout.strikes.append(_build_archer_bow_strike(level, mods.get("dex", 0)))

        # Barbarian Animal Instinct Bestial Strike
        if cls_name_lower == "barbarian" and subclass_data:
            sub_name = subclass_data.get("name", "")
            if "Animal Instinct" in sub_name:
                matched_animal = next(
                    (a for a in BARBARIAN_ANIMAL_CHOICES if f"({a['name']})" in sub_name or a["name"].lower() in sub_name.lower()),
                    None,
                )
                if matched_animal:
                    s_mod = mods.get("str", 4)
                    unarmed_atk = level + 2 + s_mod
                    dice_count = 2 if level >= 4 else 1
                    die_size = matched_animal["die"].replace("1", "", 1)
                    damage_dice_str = f"{dice_count}{die_size}"
                    rage_dmg = 2 if level < 7 else 6
                    traits_list = list(matched_animal["traits"]) + ["rage"]
                    is_agile = "agile" in traits_list
                    map2_val = unarmed_atk - (4 if is_agile else 5)
                    map3_val = unarmed_atk - (8 if is_agile else 10)
                    equipment_loadout.strikes.insert(0, Strike(
                        name=f"{matched_animal['strike']} ({matched_animal['name']} Rage Strike)",
                        attack_bonus=str(unarmed_atk).replace("+", ""),
                        map_second=f"+{map2_val}" if map2_val >= 0 else str(map2_val),
                        map_third=f"+{map3_val}" if map3_val >= 0 else str(map3_val),
                        damage_dice=damage_dice_str,
                        damage=f"{damage_dice_str} + {s_mod} (+{rage_dmg} Rage)",
                        damage_type=matched_animal["type"],
                        traits=traits_list,
                    ))

        _apply_extra_weapon_stats(equipment_loadout, cls["name"], level)

        base_hp = anc.get("hp", 8) + ((cls.get("hp_per_level", 8) + mods["con"]) * level)
        bonus_speed = 0
        if cls_name_lower == "kineticist":
            _inject_kineticist_blasts(equipment_loadout, level, mods)
        total_hp = max(1, base_hp)

        gate_elements: Set[str] = set()
        extra_trained_skill: Optional[str] = None
        chosen_feats: List[FeatSummary] = []
        added_feat_names: Set[str] = set()

        bg_desc = bg.get("description", "")
        for _bg_sk in (bg.get("trained_skills") or []):
            _sk_clean = str(_bg_sk or "").strip().lower()
            if _sk_clean and "trained_skills" in locals() and isinstance(trained_skills, (set, list)):
                if isinstance(trained_skills, set):
                    trained_skills.add(_sk_clean)
                elif _sk_clean not in trained_skills:
                    trained_skills.append(_sk_clean)
        bg_feat_name = extract_bg_feat(bg_desc, self.feats)
        if bg_feat_name and any(act_key in bg_feat_name.lower() for act_key in BACKGROUND_CUSTOM_ACTIONS):
            bg_feat_name = ""

        if bg_feat_name and bg_feat_name.lower() not in added_feat_names:
            matched_feat_def = next((f for f in self.feats if f["name"].lower() == bg_feat_name.lower()), None)
            feat_desc = (
                clean_pf2e_text(matched_feat_def.get("description", ""))
                if matched_feat_def
                else f"Granted by the {bg['name']} background."
            )
            chosen_feats.append(FeatSummary(
                id=f"feat-bg-{bg_feat_name.lower().replace(' ', '-')}",
                name=bg_feat_name,
                category="Background Feat",
                action_cost=safe_action_cost(matched_feat_def.get("action_cost")) if matched_feat_def else None,
                traits=matched_feat_def.get("traits", ["General", "Skill"]) if matched_feat_def else ["General", "Skill"],
                description=feat_desc,
            ))
            added_feat_names.add(bg_feat_name.lower())

        for act_key, c_act in BACKGROUND_CUSTOM_ACTIONS.items():
            if act_key in bg_desc.lower() and c_act["name"].lower() not in added_feat_names:
                chosen_feats.append(FeatSummary(
                    id=f"feat-bg-action-{act_key.replace(' ', '-')}",
                    name=c_act["name"],
                    category="Background Action",
                    action_cost=c_act.get("action_cost", 1),
                    traits=c_act.get("traits", ["Background", "Action"]),
                    description=c_act["description"],
                ))
                added_feat_names.add(c_act["name"].lower())

        # Level 1 Ancestry Feat
        anc_l1 = anc["name"].lower()
        lvl1_anc_feats = [
            f for f in self.feats
            if f.get("category") == "ancestry"
            and f.get("level") == 1
            and anc_l1 in [t.lower() for t in f.get("traits", [])]
            and f["name"].lower() not in added_feat_names
            and check_feat_prerequisites(f, {}, {cf.name for cf in chosen_feats}, mods, 1, subclass_name=sub_n_val)
        ]
        req_feat_names_low = {str(x).strip().lower() for x in (requested_feats or []) if str(x).strip()}
        pinned_lvl1 = [f for f in lvl1_anc_feats if str(f.get("name", "")).strip().lower() in req_feat_names_low]
        if pinned_lvl1 or lvl1_anc_feats:
            af1 = pinned_lvl1[0] if pinned_lvl1 else random.choice(lvl1_anc_feats)
            chosen_feats.append(FeatSummary(
                id=af1["id"],
                name=af1["name"],
                category="Ancestry (Level 1)",
                action_cost=safe_action_cost(af1.get("action_cost")),
                traits=af1.get("traits", [anc_l1]),
                description=clean_pf2e_text(af1.get("description", "")),
            ))
            added_feat_names.add(af1["name"].lower())
        else:
            chosen_feats.append(FeatSummary(
                id=f"anc-feat-{anc_l1}-1",
                name=f"{anc['name']} Lore",
                category="Ancestry (Level 1)",
                action_cost=None,
                traits=[anc_l1],
                description=f"You are deeply versed in the traditions, stories, and customs of the {anc['name']} people.",
            ))
            added_feat_names.add(f"{anc_l1} lore")

        pre_arch = archetype_name.strip() if archetype_name and archetype_name.strip() else None
        if archetype_data and archetype_data.get("level_2_dedication"):
            ded_obj = archetype_data["level_2_dedication"]
            cat_ded = next((f for f in self.feats if f.get("name", "").lower() == ded_obj.get("name", "").lower()), ded_obj)
            ded_p = cat_ded.get("prerequisites") or ded_obj.get("prerequisites") or []
            ded_str = " ".join(ded_p).lower() if isinstance(ded_p, list) else str(ded_p).lower()
            for ak, ab in ATTR_FULL_TO_SHORT:
                am = re.search(rf"\b{ak}\s*\+(\d+)\b", ded_str)
                if am:
                    mods[ab] = max(mods.get(ab, 0), int(am.group(1)))
            if "battle medicine" in ded_str and not any(f.name.lower() == "battle medicine" for f in chosen_feats):
                chosen_feats.append(FeatSummary(
                    id="skill-feat-battle-medicine",
                    name="Battle Medicine",
                    category="Skill (Background/Bonus)",
                    action_cost=1,
                    traits=["general", "healing", "manipulate", "skill"],
                    description="You can patch up wounds, even in combat.",
                ))
            if "shield block" in ded_str and not any(f.name.lower() == "shield block" for f in chosen_feats):
                chosen_feats.append(FeatSummary(
                    id="general-feat-shield-block",
                    name="Shield Block",
                    category="General (Bonus)",
                    action_cost=safe_action_cost("reaction"),
                    traits=["general"],
                    description="You snap your shield in place to ward off a blow.",
                ))
            sk_req = re.search(r"\btrained in ([a-z]+)", ded_str)
            if sk_req:
                extra_trained_skill = sk_req.group(1).title()

        early_skills = resolve_character_skills(
            class_name=cls["name"],
            background_data=bg,
            attribute_mods=mods,
            level=level,
            feats=chosen_feats,
            planned_archetype=pre_arch,
            subclass_name=sub_n_val,
        )
        req_trained: Set[str] = set()
        if extra_trained_skill:
            req_trained.add(extra_trained_skill.lower())
        for cf in chosen_feats:
            if "background" in cf.category.lower():
                cat_bgf = next((f for f in self.feats if f.get("name", "").lower() == cf.name.lower()), None)
                if cat_bgf:
                    for bp in (cat_bgf.get("prerequisites") or []):
                        bp_l = str(bp).lower()
                        bm = re.search(r"\btrained in (.+)$", bp_l)
                        if bm:
                            opts = [x.strip() for x in re.split(r",|\bor\b", bm.group(1)) if x.strip()]
                            if opts:
                                req_trained.add(opts[-1])
                        for ak, ab in ATTR_FULL_TO_SHORT:
                            am = re.search(rf"\b{ak}\s*\+(\d+)\b", bp_l)
                            if am:
                                mods[ab] = max(mods.get(ab, 0), int(am.group(1)))

        for sk in early_skills:
            if sk.name.lower() in req_trained and int(sk.rank) < 2:
                sk.rank = 2
                sk.rank_letter = "T"
                sk.modifier += 2 + level

        pre_skill_ranks = {sk.name.title(): int(sk.rank) for sk in early_skills}
        arch_n_val = archetype_data.get("name", "") if archetype_data else ""
        is_non_versatile = "versatile" not in heritage_data.get("name", "").lower()

        def _is_valid_class_feat(f: dict) -> bool:
            f_low = f.get("name", "").lower()
            return (
                f.get("category") == "class"
                and cls_name_lower in [t.lower() for t in f.get("traits", [])]
                and (cls_name_lower != "kineticist" or is_kineticist_feat_allowed(f, gate_elements))
                and ("sepulchral sublimation" not in f_low or cls_name_lower == "necromancer")
                and ("ascended dragonet heritage" not in f_low or is_non_versatile)
            )

        # Level 1 Class Feat
        lvl1_feats = [f for f in self.feats if f.get("level") == 1 and _is_valid_class_feat(f)]
        if lvl1_feats:
            f1 = pick_weighted_feat(lvl1_feats, cls["name"], {f.name for f in chosen_feats}, pre_skill_ranks, mods, 1, subclass_name=sub_n_val, archetype_name=arch_n_val)
            if f1:
                chosen_feats.append(FeatSummary(
                    id=f1["id"],
                    name=f1["name"],
                    category="Class (Level 1)",
                    action_cost=safe_action_cost(f1.get("action_cost")),
                    traits=f1.get("traits", []),
                    description=clean_pf2e_text(f1.get("description", "")),
                ))

        # Level 2
        if level >= 2:
            if archetype_data and archetype_data.get("level_2_dedication"):
                ded = archetype_data["level_2_dedication"]
                chosen_feats.append(FeatSummary(
                    id=ded["id"],
                    name=ded["name"],
                    category=f"Archetype ({archetype_data['name']})",
                    action_cost=ded.get("action_cost"),
                    traits=ded.get("traits", []),
                    description=clean_pf2e_text(ded["description"]),
                ))
                if ded["name"] in ARCHETYPE_GRANTED_FEATURES:
                    granted_feat = ARCHETYPE_GRANTED_FEATURES[ded["name"]]
                    if not any(f.name.lower() == granted_feat.name.lower() for f in chosen_feats):
                        chosen_feats.append(granted_feat)
                if "bloodrager dedication" in ded["name"].lower() and not any("harvest blood" in f.name.lower() for f in chosen_feats):
                    chosen_feats.append(FeatSummary(
                        id="bloodrager-harvest-blood",
                        name="Harvest Blood",
                        category="Archetype Action (Bloodrager)",
                        action_cost="1",
                        traits=["archetype", "concentrate", "rage"],
                        description="Requirements: Your last action was a successful melee Strike that dealt slashing or piercing damage to a living creature with blood. You drink or absorb the spilled blood to gain temporary HP equal to half your level and empower your bloodrager spells.",
                    ))
                if "ostilli host" in archetype_data["name"].lower():
                    apply_ostilli_host_graft(chosen_feats, equipment_loadout, level)
                if "winged warrior" in archetype_data["name"].lower():
                    apply_wing_graft_investment(
                        ancestry_name=anc["name"],
                        heritage_name=heritage_data["name"],
                        chosen_feats=chosen_feats,
                        equipment_loadout=equipment_loadout,
                    )
            else:
                lvl2_feats = [f for f in self.feats if f.get("level") == 2 and _is_valid_class_feat(f)]
                if lvl2_feats:
                    f2 = pick_weighted_feat(lvl2_feats, cls["name"], {f.name for f in chosen_feats}, pre_skill_ranks, mods, 2, subclass_name=sub_n_val, archetype_name=arch_n_val)
                    if f2:
                        chosen_feats.append(FeatSummary(
                            id=f2["id"],
                            name=f2["name"],
                            category="Class (Level 2)",
                            action_cost=safe_action_cost(f2.get("action_cost")),
                            traits=f2.get("traits", []),
                            description=clean_pf2e_text(f2.get("description", "")),
                        ))

            owned_names = {f.name for f in chosen_feats}
            skill_feats_2 = [
                f for f in self.feats
                if f.get("category") == "skill"
                and f.get("name", "").lower() != "cushion landing"
                and "archetype" not in [t.lower() for t in f.get("traits", [])]
                and f.get("level") in (1, 2)
                and ("additional lore" not in f["name"].lower() or can_take_additional_lore(owned_names, cls["name"]))
            ]
            sf = pick_weighted_feat(skill_feats_2, cls["name"], owned_names, pre_skill_ranks, mods, 2, subclass_name=sub_n_val, archetype_name=arch_n_val)
            if sf:
                resolved_feat_name2 = resolve_feat_subchoices(sf["name"], owned_names)
                chosen_feats.append(FeatSummary(
                    id=sf["id"],
                    name=resolved_feat_name2,
                    category="Skill (Level 2)",
                    action_cost=sf.get("action_cost"),
                    traits=sf.get("traits", []),
                    description=enrich_feat_description(resolved_feat_name2, sf.get("description", "")),
                ))

        # Level 3
        feats_by_lower = {f.get("name", "").lower(): f for f in self.feats if isinstance(f, dict) and f.get("name")}
        if level >= 3:
            gf_pool3 = [
                g for g in GENERAL_FEATS_LVL3
                if g["name"] not in {cf.name for cf in chosen_feats}
                and check_feat_prerequisites(feats_by_lower.get(g["name"].lower(), g), pre_skill_ranks, {cf.name for cf in chosen_feats}, mods, 3, subclass_name=sub_n_val, archetype_name=arch_n_val)
            ] or [g for g in GENERAL_FEATS_LVL3 if g["id"] in ("toughness", "fleet", "diehard", "incredible-initiative", "canny-acumen")]
            gf = random.choice(gf_pool3)
            gf_name = gf["name"]
            gf_desc = clean_pf2e_text(gf["description"])
            if gf["id"] == "toughness":
                total_hp += level
            elif gf["id"] == "fleet":
                bonus_speed += 5
            elif gf["id"] == "ancestral-paragon":
                owned_f_names = {f.name.lower() for f in chosen_feats}
                avail_anc_feats = [
                    f for f in self.feats
                    if f.get("category") == "ancestry"
                    and f.get("level") == 1
                    and anc_l1 in [t.lower() for t in f.get("traits", [])]
                    and f["name"].lower() not in owned_f_names
                    and check_feat_prerequisites(f, pre_skill_ranks, {cf.name for cf in chosen_feats}, mods, 3, subclass_name=sub_n_val, archetype_name=arch_n_val)
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
                description=gf_desc,
            ))

            if cls_name_lower in CLASS_FEATURES_LVL3:
                cf = CLASS_FEATURES_LVL3[cls_name_lower]
                chosen_feats.append(FeatSummary(
                    id=f"class-feat-{cf['name'].lower().replace(' ', '-')}",
                    name=cf["name"],
                    category="Class Feature (Level 3)",
                    action_cost=None,
                    traits=[cls_name_lower],
                    description=clean_pf2e_text(cf["description"]),
                ))

        # Level 4
        if level >= 4:
            owned_lvl4 = {f.name for f in chosen_feats}
            arch_lvl4 = None
            if archetype_data:
                valid_arch_4 = [
                    f for f in archetype_data.get("level_4_feats", [])
                    if f["name"] not in owned_lvl4
                    and check_feat_prerequisites(f, pre_skill_ranks, owned_lvl4, mods, 4, subclass_name=sub_n_val, archetype_name=arch_n_val)
                ]
                arch_lvl4 = random.choice(valid_arch_4) if valid_arch_4 else None
            if archetype_data and arch_lvl4:
                chosen_feats.append(FeatSummary(
                    id=arch_lvl4["id"],
                    name=arch_lvl4["name"],
                    category=f"Archetype ({archetype_data['name']})",
                    action_cost=arch_lvl4.get("action_cost"),
                    traits=arch_lvl4.get("traits", []),
                    description=clean_pf2e_text(arch_lvl4["description"]),
                ))
            else:
                lvl4_feats = [f for f in self.feats if f.get("level") in (1, 2, 4) and _is_valid_class_feat(f) and f["name"] not in owned_lvl4]
                if lvl4_feats:
                    f4 = pick_weighted_feat(lvl4_feats, cls["name"], owned_lvl4, pre_skill_ranks, mods, 4, subclass_name=sub_n_val, archetype_name=arch_n_val)
                    if f4:
                        chosen_feats.append(FeatSummary(
                            id=f4["id"],
                            name=f4["name"],
                            category="Class (Level 4)",
                            action_cost=safe_action_cost(f4.get("action_cost")),
                            traits=f4.get("traits", []),
                            description=clean_pf2e_text(f4.get("description", "")),
                        ))

            owned_names_4 = {f.name for f in chosen_feats}
            skill_feats_4 = [
                f for f in self.feats
                if f.get("category") == "skill"
                and f.get("name", "").lower() != "cushion landing"
                and "archetype" not in [t.lower() for t in f.get("traits", [])]
                and f.get("level") in (1, 2, 4)
                and f["name"] not in owned_names_4
                and ("additional lore" not in f["name"].lower() or can_take_additional_lore(owned_names_4, cls["name"]))
                and check_feat_prerequisites(f, pre_skill_ranks, owned_names_4, mods, 4, subclass_name=sub_n_val, archetype_name=arch_n_val)
            ]
            sf4 = pick_weighted_feat(skill_feats_4, cls["name"], owned_names_4, pre_skill_ranks, mods, 4, subclass_name=sub_n_val, archetype_name=arch_n_val)
            if sf4:
                resolved_name4 = resolve_feat_subchoices(sf4["name"], owned_names_4)
                chosen_feats.append(FeatSummary(
                    id=sf4["id"],
                    name=resolved_name4,
                    category="Skill (Level 4)",
                    action_cost=sf4.get("action_cost"),
                    traits=sf4.get("traits", []),
                    description=enrich_feat_description(resolved_name4, sf4.get("description", "")),
                ))

        # Level 5
        if level >= 5:
            lvl5_anc_feats = [
                f for f in self.feats
                if f.get("category") == "ancestry"
                and f.get("level") == 5
                and anc_l1 in [t.lower() for t in f.get("traits", [])]
                and check_feat_prerequisites(f, pre_skill_ranks, {cf.name for cf in chosen_feats}, mods, 5, subclass_name=sub_n_val, archetype_name=arch_n_val)
            ]
            if lvl5_anc_feats:
                af5 = random.choice(lvl5_anc_feats)
                chosen_feats.append(FeatSummary(
                    id=af5["id"],
                    name=af5["name"],
                    category="Ancestry (Level 5)",
                    action_cost=af5.get("action_cost"),
                    traits=af5.get("traits", []),
                    description=clean_pf2e_text(af5.get("description", "")),
                ))
            else:
                fallback_af = CURATED_ANCESTRY_FEATS_LVL5.get(
                    anc_l1,
                    {"name": f"{anc['name']} Resiliency", "description": "You draw deep upon your heritage to endure hardships, gaining a +1 circumstance bonus to saving throws."},
                )
                chosen_feats.append(FeatSummary(
                    id=f"anc-feat-{anc_l1}-5",
                    name=fallback_af["name"],
                    category="Ancestry (Level 5)",
                    action_cost=None,
                    traits=[anc_l1],
                    description=clean_pf2e_text(fallback_af["description"]),
                ))

            if cls_name_lower in CLASS_FEATURES_LVL5:
                cf5 = CLASS_FEATURES_LVL5[cls_name_lower]
                chosen_feats.append(FeatSummary(
                    id=f"class-feat-{cf5['name'].lower().replace(' ', '-')}",
                    name=cf5["name"],
                    category="Class Feature (Level 5)",
                    action_cost=None,
                    traits=[cls_name_lower],
                    description=clean_pf2e_text(cf5["description"]),
                ))

        # Level 6
        if level >= 6:
            lvl6_class_feats = [f for f in self.feats if f.get("level") in (4, 6) and _is_valid_class_feat(f)]
            if lvl6_class_feats:
                cf6 = pick_weighted_feat(lvl6_class_feats, cls["name"], {f.name for f in chosen_feats}, pre_skill_ranks, mods, 6, subclass_name=sub_n_val, archetype_name=arch_n_val)
                if cf6:
                    chosen_feats.append(FeatSummary(
                        id=cf6["id"],
                        name=cf6["name"],
                        category="Class Feat (Level 6)",
                        action_cost=safe_action_cost(cf6.get("action_cost")),
                        traits=cf6.get("traits", []),
                        description=clean_pf2e_text(cf6.get("description", "")),
                    ))

            owned_names = {f.name for f in chosen_feats}
            skill_feats_6 = [
                f for f in self.feats
                if f.get("category") == "skill"
                and f.get("name", "").lower() != "cushion landing"
                and "archetype" not in [t.lower() for t in f.get("traits", [])]
                and f.get("level") in (1, 2, 4, 6)
                and ("additional lore" not in f["name"].lower() or can_take_additional_lore(owned_names, cls["name"]))
                and check_feat_prerequisites(f, pre_skill_ranks, owned_names, mods, 6, subclass_name=sub_n_val, archetype_name=arch_n_val)
            ]
            sf6 = pick_weighted_feat(skill_feats_6, cls["name"], owned_names, pre_skill_ranks, mods, 6, subclass_name=sub_n_val, archetype_name=arch_n_val)
            if sf6:
                resolved_name6 = resolve_feat_subchoices(sf6["name"], owned_names)
                chosen_feats.append(FeatSummary(
                    id=sf6["id"],
                    name=resolved_name6,
                    category="Skill (Level 6)",
                    action_cost=sf6.get("action_cost"),
                    traits=sf6.get("traits", []),
                    description=enrich_feat_description(resolved_name6, sf6.get("description", "")),
                ))

        # Level 7
        if level >= 7:
            owned_names = {f.name for f in chosen_feats}
            gf_pool_7 = [
                f for f in GENERAL_FEATS_LVL3
                if f["name"] not in owned_names
                and check_feat_prerequisites(feats_by_lower.get(f["name"].lower(), f), pre_skill_ranks, owned_names, mods, 7, subclass_name=sub_n_val, archetype_name=arch_n_val)
            ] or [f for f in GENERAL_FEATS_LVL3 if f["name"] not in owned_names and f["id"] in ("toughness", "fleet", "diehard", "incredible-initiative", "canny-acumen")]
            if gf_pool_7:
                gf7 = random.choice(gf_pool_7)
                chosen_feats.append(FeatSummary(
                    id=f"{gf7['id']}-7",
                    name=gf7["name"],
                    category="General (Level 7)",
                    action_cost=None,
                    traits=["general"],
                    description=clean_pf2e_text(gf7["description"]),
                ))
                owned_names.add(gf7["name"])

            if cls_name_lower == "thaumaturge":
                for tid, tname, taction, tdesc in [
                    ("class-feat-exploit-vulnerability", "Exploit Vulnerability", 1, "Attempt an Esoteric Lore check against a creature's standard DC to identify its highest weakness (Mortal Weakness) or create a custom weakness equal to 2 + half your level (Personal Antithesis)."),
                    ("class-feat-implements-empowerment", "Implement's Empowerment", None, "When you Strike with a one-handed weapon while holding an implement in your other hand (and no non-implement items), you deal 2 additional damage per weapon damage die."),
                ]:
                    if tname not in owned_names:
                        chosen_feats.append(FeatSummary(id=tid, name=tname, category="Class Feature (Level 1)", action_cost=taction, traits=["thaumaturge"], description=tdesc))
                        owned_names.add(tname)
                if level >= 9 and "Intensify Vulnerability" not in owned_names:
                    chosen_feats.append(FeatSummary(
                        id="class-feat-intensify-vulnerability",
                        name="Intensify Vulnerability",
                        category="Class Feature (Level 9)",
                        action_cost=1,
                        traits=["thaumaturge"],
                        description="Activate the special intensify vulnerability benefit of one of your implements against the target of your Exploit Vulnerability.",
                    ))
                    owned_names.add("Intensify Vulnerability")

            chosen_feats.append(FeatSummary(
                id="class-feat-weapon-specialization",
                name="Weapon Specialization",
                category="Class Feature (Level 7)",
                action_cost=None,
                traits=[cls_name_lower],
                description="You have learned how to inflict greater injuries with your favored weapons. You deal 2 additional damage with weapons and unarmed attacks in which you are trained.",
            ))

        # Level 8
        if level >= 8:
            owned_names = {f.name for f in chosen_feats}
            arch_feats_8 = [
                f for f in archetype_data.get("level_8_feats", [])
                if f["name"] not in owned_names
                and check_feat_prerequisites(f, pre_skill_ranks, owned_names, mods, 8, subclass_name=sub_n_val, archetype_name=arch_n_val)
            ] if archetype_data else []

            if arch_feats_8 and random.random() < 0.6:
                af8 = random.choice(arch_feats_8)
                af8_name = resolve_feat_subchoices(af8["name"], owned_names)
                chosen_feats.append(FeatSummary(
                    id=af8["id"],
                    name=af8_name,
                    category=f"Archetype Feat (Level 8 - {archetype_data['name']})",
                    action_cost=None,
                    traits=["archetype"],
                    description=enrich_feat_description(af8_name, af8.get("description", "")),
                ))
            else:
                lvl8_class_feats = [
                    f for f in self.feats
                    if f.get("category") == "class"
                    and f.get("level") in (6, 8)
                    and cls_name_lower in [t.lower() for t in f.get("traits", [])]
                    and (cls_name_lower != "kineticist" or is_kineticist_feat_allowed(f, gate_elements))
                    and f["name"] not in owned_names
                ]
                if lvl8_class_feats:
                    cf8 = pick_weighted_feat(lvl8_class_feats, cls["name"], owned_names, pre_skill_ranks, mods, 8, subclass_name=sub_n_val, archetype_name=arch_n_val)
                    if cf8:
                        chosen_feats.append(FeatSummary(
                            id=cf8["id"],
                            name=cf8["name"],
                            category="Class Feat (Level 8)",
                            action_cost=None,
                            traits=[cls_name_lower],
                            description=clean_pf2e_text(cf8["description"]),
                        ))

            owned_names_8 = {f.name for f in chosen_feats}
            skill_feats_8 = [
                f for f in self.feats
                if f.get("category") == "skill"
                and f.get("name", "").lower() != "cushion landing"
                and "archetype" not in [t.lower() for t in f.get("traits", [])]
                and f.get("level", 1) <= 8
                and f["name"] not in owned_names_8
                and ("additional lore" not in f["name"].lower() or can_take_additional_lore(owned_names_8, cls["name"]))
                and check_feat_prerequisites(f, pre_skill_ranks, owned_names_8, mods, 8, subclass_name=sub_n_val, archetype_name=arch_n_val)
            ]
            if skill_feats_8:
                sf8 = pick_weighted_feat(skill_feats_8, cls["name"], owned_names_8, pre_skill_ranks, mods, 8, subclass_name=sub_n_val, archetype_name=arch_n_val)
                if sf8:
                    resolved_name8 = resolve_feat_subchoices(sf8["name"], owned_names_8)
                    chosen_feats.append(FeatSummary(
                        id=sf8["id"],
                        name=resolved_name8,
                        category="Skill (Level 8)",
                        action_cost=safe_action_cost(sf8.get("action_cost")),
                        traits=sf8.get("traits", ["skill"]),
                        description=enrich_feat_description(resolved_name8, sf8.get("description", "")),
                    ))

        # Level 9
        if level >= 9:
            owned_f_names = {f.name.lower() for f in chosen_feats}
            lvl9_anc_feats = [
                f for f in self.feats
                if f.get("category") == "ancestry"
                and f.get("level") in (5, 9)
                and anc_l1 in [t.lower() for t in f.get("traits", [])]
                and f["name"].lower() not in owned_f_names
                and check_feat_prerequisites(f, pre_skill_ranks, {cf.name for cf in chosen_feats}, mods, 9, subclass_name=sub_n_val, archetype_name=arch_n_val)
            ]
            if lvl9_anc_feats:
                af9 = random.choice(lvl9_anc_feats)
                chosen_feats.append(FeatSummary(
                    id=af9["id"],
                    name=af9["name"],
                    category="Ancestry (Level 9)",
                    action_cost=af9.get("action_cost"),
                    traits=af9.get("traits", []),
                    description=clean_pf2e_text(af9.get("description", "")),
                ))
            else:
                chosen_feats.append(FeatSummary(
                    id=f"anc-feat-{anc_l1}-9",
                    name=f"{anc['name']} Expertise",
                    category="Ancestry (Level 9)",
                    action_cost=None,
                    traits=[anc_l1],
                    description=clean_pf2e_text("You draw on deeper heritage resilience."),
                ))

        planned_arch = archetype_name.strip() if archetype_name and archetype_name.strip() else None
        if planned_arch:
            arch_lower = planned_arch.lower()
            if "champion" in arch_lower:
                mods["str"] = max(mods.get("str", 0), 2)
                mods["cha"] = max(mods.get("cha", 0), 2)
            elif "rogue" in arch_lower:
                mods["dex"] = max(mods.get("dex", 0), 2)

        for rf_obj in pinned_req_feats:
            rf_name = str(rf_obj.get("name", "")).strip()
            rf_lvl = int(rf_obj.get("level") or 1)
            if rf_name and rf_lvl <= level and rf_name.lower() not in added_feat_names:
                rf_cat = str(rf_obj.get("category") or "Feat").title()
                chosen_feats.append(FeatSummary(
                    id=rf_obj.get("id") or f"req-feat-{rf_name.lower().replace(' ', '-')}",
                    name=rf_name,
                    category=f"{rf_cat} (Level {rf_lvl})",
                    action_cost=safe_action_cost(rf_obj.get("action_cost")),
                    traits=rf_obj.get("traits") or [],
                    description=clean_pf2e_text(rf_obj.get("description", "")),
                ))
                added_feat_names.add(rf_name.lower())

        # Levels 11-20
        if level >= 11:
            owned_t3 = {f.name for f in chosen_feats}
            for t3_lvl in range(11, level + 1):
                total_hp, bonus_speed = self._grant_tier3_feats(
                    subclass_name=sub_n_val or "",
                    lvl=t3_lvl,
                    anc_name=anc["name"],
                    cls_name=cls["name"],
                    chosen_feats=chosen_feats,
                    existing_feat_names=owned_t3,
                    archetype_data=archetype_data,
                    gate_elements=gate_elements,
                    mods=mods,
                    total_hp=total_hp,
                    bonus_speed=bonus_speed,
                )

        # Dual-wielding weapon loadout refresh
        dw_triggers = (
            "twin takedown", "second sting", "impossible flurry", "twin parry",
            "twin riposte", "double slice", "two-weapon flurry", "twin feint", "dual-weapon",
        )
        if any(any(t in f.name.lower() for t in dw_triggers) for f in chosen_feats):
            equipment_loadout, _, _ = resolve_equipment(
                cls["name"],
                str_mod=mods["str"],
                dex_mod=mods["dex"],
                level=level,
                ancestry_name=anc["name"],
                heritage_name=heritage_data["name"],
                subclass_name=sub_n_val,
                archetype_name=planned_arch,
                feats=chosen_feats,
            )
            extra_prof_dw = get_weapon_prof_bonus_delta(cls["name"], level)
            if extra_prof_dw > 0:
                for st in equipment_loadout.strikes:
                    try:
                        new_atk = int(str(st.attack_bonus).replace("+", "")) + extra_prof_dw
                        st.attack_bonus = f"+{new_atk}" if new_atk >= 0 else str(new_atk)
                        m2 = int(str(st.map_second).replace("+", "")) + extra_prof_dw
                        m3 = int(str(st.map_third).replace("+", "")) + extra_prof_dw
                        st.map_second = f"+{m2}" if m2 >= 0 else str(m2)
                        st.map_third = f"+{m3}" if m3 >= 0 else str(m3)
                    except ValueError:
                        pass

        # Skills consistency
        all_skills = early_skills
        for sk in all_skills:
            expected_r = pre_skill_ranks.get(sk.name.title())
            if expected_r is not None and int(sk.rank) < int(expected_r):
                sk.rank = int(expected_r)

        if extra_trained_skill:
            for sk in all_skills:
                if sk.name.lower() == extra_trained_skill.lower() and sk.rank == 0:
                    sk.rank = 2
                    sk.proficiency = "Trained"
                    sk.rank_letter = "T"
                    sk.modifier += 2 + level

        # Ancestral Paragon bonus feat
        if any(f.name.lower() == "ancestral paragon" for f in chosen_feats):
            owned_ap = {f.name.lower() for f in chosen_feats}
            ap_pool = [
                f for f in self.feats
                if f.get("category") == "ancestry"
                and f.get("level") == 1
                and anc_l1 in [t.lower() for t in f.get("traits", [])]
                and f["name"].lower() not in owned_ap
                and check_feat_prerequisites(f, pre_skill_ranks, {cf.name for cf in chosen_feats}, mods, level, subclass_name=sub_n_val, archetype_name=arch_n_val)
            ]
            if ap_pool:
                ap_f = random.choice(ap_pool)
                chosen_feats.append(FeatSummary(
                    id=ap_f["id"],
                    name=ap_f["name"],
                    category="Ancestry (Ancestral Paragon)",
                    action_cost=safe_action_cost(ap_f.get("action_cost")),
                    traits=ap_f.get("traits", [anc_l1]),
                    description=clean_pf2e_text(ap_f.get("description", "")),
                ))

        # Backfill allotted Skill Feat slots
        existing_skill_cats = {f.category for f in chosen_feats}
        owned_all = {f.name for f in chosen_feats}
        sk_step = 1 if cls_name_lower in ("rogue", "investigator") else 2
        for ev_lvl in range(2, level + 1, sk_step):
            cat_label = f"Skill (Level {ev_lvl})"
            if cat_label not in existing_skill_cats:
                ev_pool = [
                    f for f in self.feats
                    if f.get("category") == "skill"
                    and f.get("name", "").lower() != "cushion landing"
                    and "archetype" not in [t.lower() for t in f.get("traits", [])]
                    and f.get("level", 1) <= ev_lvl
                    and f["name"] not in owned_all
                    and ("additional lore" not in f["name"].lower() or can_take_additional_lore(owned_all, cls["name"]))
                    and check_feat_prerequisites(f, pre_skill_ranks, owned_all, mods, ev_lvl, subclass_name=sub_n_val, archetype_name=arch_n_val)
                ]
                if ev_pool:
                    ev_sf = pick_weighted_feat(ev_pool, cls["name"], owned_all, pre_skill_ranks, mods, ev_lvl, subclass_name=sub_n_val, archetype_name=arch_n_val)
                    if ev_sf:
                        ev_sf_name = resolve_feat_subchoices(ev_sf["name"], owned_all)
                        chosen_feats.append(FeatSummary(
                            id=ev_sf["id"],
                            name=ev_sf_name,
                            category=cat_label,
                            action_cost=safe_action_cost(ev_sf.get("action_cost")),
                            traits=ev_sf.get("traits", ["skill"]),
                            description=enrich_feat_description(ev_sf_name, ev_sf.get("description", "")),
                        ))
                        owned_all.add(ev_sf_name)
                        existing_skill_cats.add(cat_label)

        # Ensure Archer 3rd weapon bow is present
        arch_gen = f"{clean_arch_input or ''} {archetype_data.get('name', '') if archetype_data else ''}".lower()
        if level >= 2 and "archer" in arch_gen and equipment_loadout and equipment_loadout.strikes:
            if not any(any(kw in (st.name or "").lower() for kw in ("bow", "shortbow", "longbow")) for st in equipment_loadout.strikes):
                new_bow = _build_archer_bow_strike(level, mods.get("dex", 0))
                phys = [
                    s for s in equipment_loadout.strikes
                    if not any(k in (s.name or "").lower() for k in ("elemental blast", "rage strike", "alchemist's fire"))
                ]
                if len(phys) >= 3:
                    equipment_loadout.strikes[equipment_loadout.strikes.index(phys[-1])] = new_bow
                else:
                    equipment_loadout.strikes.append(new_bow)

        _attach_named_artillery_strike(chosen_feats, equipment_loadout, level, mods)
        self._enforce_granted_feat_skill_prereqs(
            chosen_feats,
            all_skills,
            level,
            mods,
            include_all_feats=False,
            allow_generic_rk=True,
            fallback_lore_name="Scribing Lore",
        )

        return _sync_deity_focus_spells(self._sync_feat_skill_prereqs(self._finalize_sheet(
            name=resolved_name,
            level=level,
            anc=anc,
            ancestry_description=clean_pf2e_text(anc.get("description", "")),
            heritage_name=heritage_data["name"],
            background_name=bg["name"],
            background_description=clean_pf2e_text(bg.get("description", "")),
            cls=cls,
            subclass_data=subclass_data,
            subclass_obj=SubclassSummary(**subclass_data) if subclass_data else None,
            archetype_name=(clean_arch_input or (archetype_data["name"] if archetype_data else None)) if level >= 2 else None,
            archetype_description=clean_pf2e_text(archetype_data.get("level_2_dedication", {}).get("description", "")) if archetype_data else None,
            size=anc.get("size", "med"),
            speed=anc.get("speed", 25) + bonus_speed,
            mods=mods,
            calculated_ac=calculated_ac,
            shield_bonus=shield_bonus,
            total_hp=total_hp,
            fort_prof=fort_prof,
            ref_prof=ref_prof,
            will_prof=will_prof,
            perception_prof=perception_prof,
            all_skills=all_skills,
            equipment_loadout=equipment_loadout,
            chosen_feats=chosen_feats,
            traits=[anc["name"].lower(), cls["name"].lower()],
            concept_text=concept_text,
            deity_name=deity_name,
            domain_name=domain_name,
        )))

    def level_up(
        self,
        current_char: Dict[str, Any],
        target_level: int,
        use_dedication: bool = False,
        archetype_name: Optional[str] = None,
    ) -> CharacterSheet:
        target_level = max(1, min(20, int(target_level)))
        old_level = int(current_char.get("target_level", 1))

        anc_name = (current_char.get("ancestry") or "").strip().lower()
        cls_name = (current_char.get("character_class") or "").strip().lower()
        bg_name = (current_char.get("background") or "").strip().lower()

        anc = self.ancestries.get(anc_name) or next(
            (a for a in self.ancestries.values() if a["name"].lower() == anc_name),
            next(iter(self.ancestries.values())),
        )
        cls = self.classes.get(cls_name) or next(
            (c for c in self.classes.values() if c["name"].lower() == cls_name),
            next(iter(self.classes.values())),
        )
        cls_name_lower = (cls["name"] if isinstance(cls, dict) else str(cls)).lower()
        bg = self.backgrounds.get(bg_name) or next(
            (b for b in self.backgrounds.values() if b["name"].lower() == bg_name),
            next(iter(self.backgrounds.values())),
        )

        raw_attrs = current_char.get("attributes", {})
        attr_aliases = {
            "str": ("str", "strength"),
            "dex": ("dex", "dexterity"),
            "con": ("con", "constitution"),
            "int": ("int", "intelligence"),
            "wis": ("wis", "wisdom"),
            "cha": ("cha", "charisma"),
        }
        mods = {
            short_name: next((_parse_int_bonus(raw_attrs[a], 0) for a in aliases if a in raw_attrs), 0)
            for short_name, aliases in attr_aliases.items()
        }

        key_options = (
            [ATTR_NAME_TO_SHORT[k.lower()] for k in cls.get("key_attributes", []) if k.lower() in ATTR_NAME_TO_SHORT]
            or (["int", "cha"] if cls_name_lower == "psychic" else [])
        )
        key_attr = key_options[0] if key_options else "str"

        def _milestone_gains(lvl_from: int, lvl_to: int, attr_val: int, is_top_attr: bool) -> int:
            milestones = [5, 10, 15, 20]
            if lvl_to > lvl_from:
                val = attr_val
                for m in milestones:
                    if lvl_from < m <= lvl_to:
                        if val < 4:
                            val += 1
                        elif val == 4 and m >= 10:
                            val = 5
                        elif val == 5 and m >= 20:
                            val = 6
                return val
            if lvl_to < lvl_from:
                val = attr_val
                floor = 4 if is_top_attr else 0
                for m in sorted(milestones, reverse=True):
                    if lvl_to < m <= lvl_from:
                        if val == 6 and m == 20:
                            val = 5
                        elif val == 5 and m == 10:
                            val = 4
                        elif val > floor and not (val >= 4 and m in (5, 15)):
                            val = max(floor, val - 1)
                return val
            return attr_val

        boost_priority: List[str] = []
        for a in [key_attr, "con", "dex", "wis", "str", "int", "cha"]:
            if a not in boost_priority:
                boost_priority.append(a)
        for idx, attr in enumerate(boost_priority[:4]):
            mods[attr] = _milestone_gains(old_level, target_level, mods[attr], idx == 0)

        hard_cap = 6 if target_level >= 20 else (5 if target_level >= 10 else 4)
        for a in ATTRIBUTES:
            mods[a] = min(mods[a], hard_cap)
        min_sum = 8 + (target_level // 5) * 2
        for a in boost_priority:
            if sum(mods.values()) < min_sum and mods[a] < hard_cap:
                mods[a] += 1

        # Defenses & Proficiencies
        fort_rank, ref_rank, will_rank, perception_rank = get_class_saving_throws(
            cls["name"],
            cls.get("saving_throws", {}).get("fortitude", 1),
            cls.get("saving_throws", {}).get("reflex", 1),
            cls.get("saving_throws", {}).get("will", 1),
            cls.get("perception", 1),
            target_level,
        )
        resilient_bonus = get_fundamental_rune_tiers(target_level)["save_item_bonus"]
        fort_prof = self._calc_prof(fort_rank, target_level, mods["con"])
        ref_prof = self._calc_prof(ref_rank, target_level, mods["dex"])
        will_prof = self._calc_prof(will_rank, target_level, mods["wis"])
        fort_prof.modifier += resilient_bonus
        ref_prof.modifier += resilient_bonus
        will_prof.modifier += resilient_bonus
        perception_prof = self._calc_prof(perception_rank, target_level, mods["wis"])

        # Equipment & Weapons
        current_sub = (current_char.get("subclass") or {}).get("name", "") if isinstance(current_char.get("subclass"), dict) else ""
        gate_elements = extract_gate_elements(current_sub) if cls_name_lower == "kineticist" else set()
        current_arch = current_char.get("archetype") or ""
        raw_eq = current_char.get("equipment")
        if isinstance(raw_eq, dict):
            existing_weps = raw_eq.get("strikes") or raw_eq.get("weapons")
        elif raw_eq is not None:
            existing_weps = getattr(raw_eq, "strikes", None) or getattr(raw_eq, "weapons", None)
        else:
            existing_weps = None

        saved_strikes = copy.deepcopy(existing_weps or [])

        equipment_loadout, calculated_ac, shield_bonus = resolve_equipment(
            cls["name"],
            str_mod=mods["str"],
            dex_mod=mods["dex"],
            level=target_level,
            ancestry_name=anc["name"],
            heritage_name=current_char.get("heritage", ""),
            subclass_name=current_sub,
            archetype_name=current_arch,
            existing_weapons=existing_weps,
        )

        if saved_strikes:
            existing_base_names = {
                _RE_RUNE_PREFIX.sub("", (s.name or "").strip()).lower()
                for s in equipment_loadout.strikes
            }
            potency = 3 if target_level >= 16 else (2 if target_level >= 10 else (1 if target_level >= 2 else 0))
            dice_mult = 4 if target_level >= 19 else (3 if target_level >= 12 else (2 if target_level >= 4 else 1))
            striking_label = (
                "Major Striking " if dice_mult == 4 else
                ("Greater Striking " if dice_mult == 3 else ("Striking " if dice_mult == 2 else ""))
            )
            prefix = f"+{potency} {striking_label}" if potency > 0 else striking_label

            custom_preserved = []
            for ps in saved_strikes:
                ps_dict = ps if isinstance(ps, dict) else ps.model_dump()
                raw_name = (ps_dict.get("name") or "").strip()
                base_name = _RE_RUNE_PREFIX.sub("", raw_name)
                if (
                    not base_name
                    or base_name.lower().startswith("elemental blast")
                    or "(rage strike)" in base_name.lower()
                    or base_name.lower() in existing_base_names
                ):
                    continue
                traits = list(ps_dict.get("traits") or [])
                traits_low = [t.lower() for t in traits]
                is_ranged = any(k in base_name.lower() for k in ("bow", "crossbow", "sling", "dart", "pistol", "musket"))
                use_dex = is_ranged or ("finesse" in traits_low and mods.get("dex", 0) > mods.get("str", 0))
                best_mod = mods.get("dex", 0) if use_dex else mods.get("str", 0)
                atk = target_level + 2 + best_mod + potency
                step = 4 if "agile" in traits_low else 5

                raw_dmg = str(ps_dict.get("damage_dice") or "1d6")
                m_die = re.match(r"^(\d+)(d\d+)", raw_dmg)
                die_part = f"{dice_mult}{m_die.group(2)}" if m_die else raw_dmg
                dmg_mod = 0 if (is_ranged and "propulsive" not in traits_low and "thrown" not in traits_low) else mods.get("str", 0)
                dmg_str = f"{die_part}+{dmg_mod}" if dmg_mod > 0 else (f"{die_part}{dmg_mod}" if dmg_mod < 0 else die_part)

                strike_cls = type(equipment_loadout.strikes[0]) if equipment_loadout.strikes else dict
                new_st = {
                    "name": f"{prefix}{base_name}",
                    "attack_bonus": str(atk),
                    "map_second": str(atk - step),
                    "map_third": str(atk - (step * 2)),
                    "damage_dice": dmg_str,
                    "damage_type": ps_dict.get("damage_type") or "Slashing",
                    "traits": traits,
                }
                custom_preserved.append(strike_cls.model_validate(new_st) if hasattr(strike_cls, "model_validate") else new_st)

            if custom_preserved:
                equipment_loadout.strikes = custom_preserved + list(equipment_loadout.strikes)

        prev_gear = (raw_eq.get("gear") if isinstance(raw_eq, dict) else getattr(raw_eq, "gear", None)) or []
        if any("shield" in str(g).lower() for g in prev_gear):
            if not any("shield" in str(g).lower() for g in (equipment_loadout.gear or [])):
                equipment_loadout.gear.append("Steel Shield (+2 AC when raised)")

        _apply_extra_weapon_stats(equipment_loadout, cls["name"], target_level)

        base_hp = anc.get("hp", 8) + ((cls.get("hp_per_level", 8) + mods["con"]) * target_level)
        if cls_name_lower == "kineticist":
            _inject_kineticist_blasts(equipment_loadout, target_level, mods)
        total_hp = max(1, base_hp)

        # Resolve Archetype
        archetype_data = None
        existing_arch_name = current_char.get("archetype")
        clean_target_arch = (
            archetype_name.strip()
            if archetype_name and archetype_name.strip().lower() not in ("", "any", "any archetype", "none")
            else None
        )
        if existing_arch_name and existing_arch_name.lower() not in ("any", "any archetype", "none"):
            norm_existing = existing_arch_name.replace("-multiclass", "").replace("-", " ").strip()
            archetype_data = resolve_dynamic_archetype(norm_existing, self.feats)
            resolved_arch_name = archetype_data["name"] if archetype_data and archetype_data.get("name") else norm_existing.title()
        elif clean_target_arch:
            norm_target = clean_target_arch.replace("-multiclass", "").replace("-", " ").strip()
            archetype_data = resolve_dynamic_archetype(norm_target, self.feats)
            resolved_arch_name = archetype_data["name"] if archetype_data and archetype_data.get("name") else norm_target.title()
        elif use_dedication and target_level >= 2:
            archetype_data = pick_archetype(cls["name"], {}, mods, self.feats)
            resolved_arch_name = archetype_data["name"] if archetype_data else None
        else:
            resolved_arch_name = None

        # Preserve and advance/trim feats
        chosen_feats: List[FeatSummary] = [
            FeatSummary(**f) if isinstance(f, dict) else f
            for f in current_char.get("feats", [])
        ]

        if target_level < old_level:
            filtered_feats = []
            for f in chosen_feats:
                cat = (f.category or "").lower()
                fid = (f.id or "").lower()
                m = re.search(r"target_level\s*(\d+)", cat)
                m_id = re.search(r"-(\d+)$", fid) or re.search(r"lvl(\d+)", fid)
                f_lvl = int(m.group(1)) if m else (int(m_id.group(1)) if m_id else None)
                if f_lvl and f_lvl > target_level:
                    continue
                if target_level < 7 and f.name == "Weapon Specialization":
                    continue
                if target_level < 2 and (
                    f.id == "graft-wing-beast-graft"
                    or "dedication" in (f.name or "").lower()
                    or "archetype" in cat
                ):
                    continue
                filtered_feats.append(f)
            chosen_feats = filtered_feats

        existing_feat_names = {f.name for f in chosen_feats}
        existing_skills_data = current_char.get("skills") or current_char.get("all_skills")
        existing_lore_name = current_char.get("lore")
        if not existing_lore_name and existing_skills_data:
            for sk in existing_skills_data:
                sk_dict = sk if isinstance(sk, dict) else getattr(sk, "__dict__", {})
                if sk_dict.get("is_lore") or "Lore" in sk_dict.get("name", ""):
                    existing_lore_name = sk_dict.get("name")
                    break

        lu_sub_name = (current_char.get("subclass") or {}).get("name") if isinstance(current_char.get("subclass"), dict) else None
        all_skills = resolve_character_skills(
            class_name=cls["name"],
            background_data=bg,
            attribute_mods=mods,
            level=target_level,
            feats=chosen_feats,
            existing_skills=existing_skills_data,
            existing_lore=existing_lore_name,
            subclass_name=lu_sub_name,
        )
        lu_skill_ranks = {sk.name.title(): int(sk.rank or 0) for sk in all_skills}
        lu_perc_rank = int(getattr(perception_prof, "rank", 2) or 2)
        is_non_versatile_lu = "versatile" not in str(current_char.get("heritage", "")).lower()

        def _lu_valid(feat_dict: dict, at_lvl: int) -> bool:
            return check_feat_prerequisites(
                feat_dict,
                skill_ranks=lu_skill_ranks,
                owned_feat_names=existing_feat_names,
                attribute_mods=mods,
                character_level=at_lvl,
                subclass_name=lu_sub_name,
                archetype_name=resolved_arch_name,
                perception_rank=lu_perc_rank,
            )

        def _is_lu_class_feat(f: dict) -> bool:
            f_low = f.get("name", "").lower()
            return (
                f.get("category") == "class"
                and cls_name_lower in [t.lower() for t in f.get("traits", [])]
                and (cls_name_lower != "kineticist" or is_kineticist_feat_allowed(f, gate_elements))
                and ("sepulchral sublimation" not in f_low or cls_name_lower == "necromancer")
                and ("ascended dragonet heritage" not in f_low or is_non_versatile_lu)
                and f["name"] not in existing_feat_names
            )

        lu_cat_by_low = {cf.get("name", "").strip().lower(): cf for cf in self.feats if isinstance(cf, dict) and cf.get("name")}

        for lvl in range(old_level + 1, target_level + 1):
            if lvl == 2:
                if archetype_data and archetype_data.get("level_2_dedication") and archetype_data["level_2_dedication"]["name"] not in existing_feat_names:
                    ded = archetype_data["level_2_dedication"]
                    chosen_feats.append(FeatSummary(
                        id=ded["id"],
                        name=ded["name"],
                        category=f"Archetype ({archetype_data['name']})",
                        action_cost=ded.get("action_cost"),
                        traits=ded.get("traits", []),
                        description=clean_pf2e_text(ded["description"]),
                    ))
                    existing_feat_names.add(ded["name"])
                    if ded["name"] in ARCHETYPE_GRANTED_FEATURES:
                        extra_feat = ARCHETYPE_GRANTED_FEATURES[ded["name"]]
                        if extra_feat.name not in existing_feat_names:
                            chosen_feats.append(extra_feat)
                            existing_feat_names.add(extra_feat.name)
                    if "winged warrior" in archetype_data["name"].lower():
                        apply_wing_graft_investment(
                            ancestry_name=anc["name"],
                            heritage_name=current_char.get("heritage", ""),
                            chosen_feats=chosen_feats,
                            equipment_loadout=equipment_loadout,
                        )
                    if "ostilli host" in archetype_data["name"].lower():
                        apply_ostilli_host_graft(chosen_feats, equipment_loadout, target_level)
                else:
                    lvl2_feats = [f for f in self.feats if f.get("target_level") == 2 and _is_lu_class_feat(f) and _lu_valid(f, 2)]
                    f2 = pick_weighted_feat(lvl2_feats, cls["name"], existing_feat_names, lu_skill_ranks, mods, 2, subclass_name=lu_sub_name, archetype_name=resolved_arch_name)
                    if f2:
                        chosen_feats.append(FeatSummary(
                            id=f2["id"],
                            name=f2["name"],
                            category="Class (Level 2)",
                            action_cost=safe_action_cost(f2.get("action_cost")),
                            traits=f2.get("traits", []),
                            description=clean_pf2e_text(f2.get("description", "")),
                        ))
                        existing_feat_names.add(f2["name"])

                skill_feats_2 = [
                    f for f in self.feats
                    if f.get("category") == "skill"
                    and f.get("name", "").lower() != "cushion landing"
                    and "archetype" not in [t.lower() for t in f.get("traits", [])]
                    and f.get("target_level") in (1, 2)
                    and f["name"] not in existing_feat_names
                    and ("additional lore" not in f["name"].lower() or can_take_additional_lore(existing_feat_names, cls["name"]))
                    and _lu_valid(f, 2)
                ]
                sf = pick_weighted_feat(skill_feats_2, cls["name"], existing_feat_names, lu_skill_ranks, mods, 2, subclass_name=lu_sub_name, archetype_name=resolved_arch_name)
                if sf:
                    resolved_feat_name2 = resolve_feat_subchoices(sf["name"], existing_feat_names)
                    chosen_feats.append(FeatSummary(
                        id=sf["id"],
                        name=resolved_feat_name2,
                        category="Skill (Level 2)",
                        action_cost=sf.get("action_cost"),
                        traits=sf.get("traits", []),
                        description=enrich_feat_description(resolved_feat_name2, sf.get("description", "")),
                    ))
                    existing_feat_names.add(resolved_feat_name2)

            elif lvl == 3:
                gf_pool = [
                    f for f in GENERAL_FEATS_LVL3
                    if f["name"] not in existing_feat_names
                    and _lu_valid(lu_cat_by_low.get(f["name"].strip().lower(), f), 3)
                    and (f["name"].strip().lower() != "fast recovery" or int(mods.get("con", 0) or 0) >= 2)
                ]
                gf = pick_weighted_feat(gf_pool, cls["name"], existing_feat_names, lu_skill_ranks, mods, 3, subclass_name=lu_sub_name, archetype_name=resolved_arch_name)
                if gf:
                    chosen_feats.append(FeatSummary(
                        id=gf["id"],
                        name=gf["name"],
                        category="General (Level 3)",
                        action_cost=None,
                        traits=["general"],
                        description=clean_pf2e_text(gf["description"]),
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
                            description=clean_pf2e_text(cf["description"]),
                        ))
                        existing_feat_names.add(cf["name"])

            elif lvl == 4:
                if archetype_data:
                    arch_lvl4 = [f for f in archetype_data.get("level_4_feats", []) if f["name"] not in existing_feat_names and _lu_valid(f, 4)]
                    af4 = pick_weighted_feat(arch_lvl4, cls["name"], existing_feat_names, lu_skill_ranks, mods, 4, subclass_name=lu_sub_name, archetype_name=resolved_arch_name)
                    if af4:
                        chosen_feats.append(FeatSummary(
                            id=af4["id"],
                            name=af4["name"],
                            category=f"Archetype ({archetype_data['name']})",
                            action_cost=af4.get("action_cost"),
                            traits=af4.get("traits", []),
                            description=clean_pf2e_text(af4["description"]),
                        ))
                        existing_feat_names.add(af4["name"])
                else:
                    lvl4_feats = [f for f in self.feats if f.get("target_level") in (1, 2, 4) and _is_lu_class_feat(f) and _lu_valid(f, 4)]
                    f4 = pick_weighted_feat(lvl4_feats, cls["name"], existing_feat_names, lu_skill_ranks, mods, 4, subclass_name=lu_sub_name, archetype_name=resolved_arch_name)
                    if f4:
                        chosen_feats.append(FeatSummary(
                            id=f4["id"],
                            name=f4["name"],
                            category="Class (Level 4)",
                            action_cost=safe_action_cost(f4.get("action_cost")),
                            traits=f4.get("traits", []),
                            description=clean_pf2e_text(f4.get("description", "")),
                        ))
                        existing_feat_names.add(f4["name"])

                skill_feats_4 = [
                    f for f in self.feats
                    if f.get("category") == "skill"
                    and f.get("name", "").lower() != "cushion landing"
                    and "archetype" not in [t.lower() for t in f.get("traits", [])]
                    and f.get("target_level") in (1, 2, 4)
                    and f["name"] not in existing_feat_names
                    and ("additional lore" not in f["name"].lower() or can_take_additional_lore(existing_feat_names, cls["name"]))
                    and _lu_valid(f, 4)
                ]
                sf4 = pick_weighted_feat(skill_feats_4, cls["name"], existing_feat_names, lu_skill_ranks, mods, 4, subclass_name=lu_sub_name, archetype_name=resolved_arch_name)
                if sf4:
                    resolved_name4 = resolve_feat_subchoices(sf4["name"], existing_feat_names)
                    chosen_feats.append(FeatSummary(
                        id=sf4["id"],
                        name=resolved_name4,
                        category="Skill (Level 4)",
                        action_cost=sf4.get("action_cost"),
                        traits=sf4.get("traits", []),
                        description=enrich_feat_description(resolved_name4, sf4.get("description", "")),
                    ))
                    existing_feat_names.add(resolved_name4)

            elif lvl == 5:
                anc_name_lower = anc["name"].lower()
                lvl5_anc_feats = [
                    f for f in self.feats
                    if f.get("category") == "ancestry"
                    and f.get("target_level") == 5
                    and anc_name_lower in [t.lower() for t in f.get("traits", [])]
                    and f["name"] not in existing_feat_names
                    and _lu_valid(f, 5)
                ]
                af5 = pick_weighted_feat(lvl5_anc_feats, cls["name"], existing_feat_names, lu_skill_ranks, mods, 5, subclass_name=lu_sub_name, archetype_name=resolved_arch_name)
                if af5:
                    chosen_feats.append(FeatSummary(
                        id=af5["id"],
                        name=af5["name"],
                        category="Ancestry (Level 5)",
                        action_cost=af5.get("action_cost"),
                        traits=af5.get("traits", []),
                        description=clean_pf2e_text(af5.get("description", "")),
                    ))
                    existing_feat_names.add(af5["name"])
                else:
                    curated_af = CURATED_ANCESTRY_FEATS_LVL5.get(anc_name_lower)
                    curated_cat = next(
                        (f for f in self.feats if isinstance(f, dict) and curated_af and f.get("name", "").lower() == curated_af["name"].lower()),
                        None,
                    )
                    if curated_af and (not curated_cat or _lu_valid(curated_cat, 5)):
                        fallback_af = curated_af
                    else:
                        lvl1_anc_pool = [
                            f for f in self.feats
                            if f.get("category") == "ancestry"
                            and f.get("target_level", 1) <= 5
                            and anc_name_lower in [t.lower() for t in f.get("traits", [])]
                            and f["name"] not in existing_feat_names
                            and _lu_valid(f, 5)
                        ]
                        picked_l1_af = pick_weighted_feat(lvl1_anc_pool, cls["name"], existing_feat_names, lu_skill_ranks, mods, 5, subclass_name=lu_sub_name, archetype_name=resolved_arch_name)
                        fallback_af = picked_l1_af or {
                            "name": f"{anc['name']} Resilience",
                            "description": "You draw deep upon your heritage to endure hardships, gaining a +1 circumstance bonus to saving throws.",
                        }
                    chosen_feats.append(FeatSummary(
                        id=f"anc-feat-{anc_name_lower}-5",
                        name=fallback_af["name"],
                        category="Ancestry (Level 5)",
                        action_cost=None,
                        traits=[anc_name_lower],
                        description=clean_pf2e_text(fallback_af["description"]),
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
                            description=clean_pf2e_text(cf5["description"]),
                        ))
                        existing_feat_names.add(cf5["name"])

            elif lvl == 6:
                lvl6_class_feats = [f for f in self.feats if f.get("target_level") in (4, 6) and _is_lu_class_feat(f) and _lu_valid(f, 6)]
                cf6 = pick_weighted_feat(lvl6_class_feats, cls["name"], existing_feat_names, lu_skill_ranks, mods, 6, subclass_name=lu_sub_name, archetype_name=resolved_arch_name)
                if cf6:
                    chosen_feats.append(FeatSummary(
                        id=cf6["id"],
                        name=cf6["name"],
                        category="Class Feat (Level 6)",
                        action_cost=safe_action_cost(cf6.get("action_cost")),
                        traits=cf6.get("traits", []),
                        description=clean_pf2e_text(cf6.get("description", "")),
                    ))
                    existing_feat_names.add(cf6["name"])

            elif lvl == 7:
                if "Weapon Specialization" not in existing_feat_names:
                    chosen_feats.append(FeatSummary(
                        id="class-feat-weapon-specialization",
                        name="Weapon Specialization",
                        category="Class Feature (Level 7)",
                        action_cost=None,
                        traits=[cls_name_lower],
                        description="You deal 2 additional damage with weapons and unarmed attacks in which you are trained.",
                    ))
                    existing_feat_names.add("Weapon Specialization")

                gen_feats_7 = [
                    f for f in self.feats
                    if f.get("category") == "general"
                    and f.get("target_level", 1) <= 7
                    and f["name"] not in existing_feat_names
                    and _lu_valid(f, 7)
                ]
                gf7 = pick_weighted_feat(gen_feats_7, cls["name"], existing_feat_names, lu_skill_ranks, mods, 7, subclass_name=lu_sub_name, archetype_name=resolved_arch_name)
                if gf7:
                    chosen_feats.append(FeatSummary(
                        id=gf7["id"],
                        name=gf7["name"],
                        category="General Feat (Level 7)",
                        action_cost=None,
                        traits=["general"],
                        description=clean_pf2e_text(gf7["description"]),
                    ))
                    existing_feat_names.add(gf7["name"])

            elif lvl == 8:
                arch_feats_8 = [
                    f for f in archetype_data.get("level_8_feats", [])
                    if f["name"] not in existing_feat_names and _lu_valid(f, 8)
                ] if archetype_data else []

                if arch_feats_8 and random.random() < 0.6:
                    af8 = pick_weighted_feat(arch_feats_8, cls["name"], existing_feat_names, lu_skill_ranks, mods, 8, subclass_name=lu_sub_name, archetype_name=resolved_arch_name)
                    if af8:
                        af8_name = resolve_feat_subchoices(af8["name"], existing_feat_names)
                        chosen_feats.append(FeatSummary(
                            id=af8["id"],
                            name=af8_name,
                            category=f"Archetype Feat (Level 8 - {archetype_data['name']})",
                            action_cost=None,
                            traits=["archetype"],
                            description=enrich_feat_description(af8_name, af8.get("description", "")),
                        ))
                        existing_feat_names.add(af8_name)
                else:
                    lvl8_class_feats = [
                        f for f in self.feats
                        if f.get("category") == "class"
                        and f.get("target_level") in (6, 8)
                        and cls_name_lower in [t.lower() for t in f.get("traits", [])]
                        and f["name"] not in existing_feat_names
                        and _lu_valid(f, 8)
                    ]
                    cf8 = pick_weighted_feat(lvl8_class_feats, cls["name"], existing_feat_names, lu_skill_ranks, mods, 8, subclass_name=lu_sub_name, archetype_name=resolved_arch_name)
                    if cf8:
                        chosen_feats.append(FeatSummary(
                            id=cf8["id"],
                            name=cf8["name"],
                            category="Class Feat (Level 8)",
                            action_cost=None,
                            traits=[cls_name_lower],
                            description=clean_pf2e_text(cf8["description"]),
                        ))
                        existing_feat_names.add(cf8["name"])

            elif lvl == 9:
                anc_name_lower = (current_char.get("ancestry") or "").lower().strip()
                lvl9_anc_feats = [
                    f for f in self.feats
                    if f.get("category") == "ancestry"
                    and f.get("target_level") in (1, 5, 9)
                    and (not anc_name_lower or anc_name_lower in [t.lower() for t in f.get("traits", [])])
                    and f["name"] not in existing_feat_names
                    and _lu_valid(f, 9)
                ]
                af9 = pick_weighted_feat(lvl9_anc_feats, cls["name"], existing_feat_names, lu_skill_ranks, mods, 9, subclass_name=lu_sub_name, archetype_name=resolved_arch_name)
                if af9:
                    chosen_feats.append(FeatSummary(
                        id=af9["id"],
                        name=af9["name"],
                        category="Ancestry Feat (Level 9)",
                        action_cost=None,
                        traits=af9.get("traits", ["ancestry"]),
                        description=clean_pf2e_text(af9.get("description", "")),
                    ))
                    existing_feat_names.add(af9["name"])
                else:
                    fallback_name9 = f"{anc_name_lower.capitalize()} Resilience"
                    chosen_feats.append(FeatSummary(
                        id=f"anc-feat-{anc_name_lower}-9",
                        name=fallback_name9,
                        category="Ancestry Feat (Level 9)",
                        action_cost=None,
                        traits=["ancestry"],
                        description="Your bond with your heritage deepens, granting increased durability against ancestry-specific hazards.",
                    ))
                    existing_feat_names.add(fallback_name9)

            elif lvl == 10:
                arch_feats_10 = [
                    f for f in archetype_data.get("level_10_feats", archetype_data.get("level_8_feats", []))
                    if f["name"] not in existing_feat_names and _lu_valid(f, 10)
                ] if archetype_data else []

                if arch_feats_10 and random.random() < 0.6:
                    af10 = pick_weighted_feat(arch_feats_10, cls["name"], existing_feat_names, lu_skill_ranks, mods, 10, subclass_name=lu_sub_name, archetype_name=resolved_arch_name)
                    if af10:
                        af10_name = resolve_feat_subchoices(af10["name"], existing_feat_names)
                        chosen_feats.append(FeatSummary(
                            id=af10["id"],
                            name=af10_name,
                            category=f"Archetype Feat (Level 10 - {archetype_data['name']})",
                            action_cost=None,
                            traits=["archetype"],
                            description=enrich_feat_description(af10_name, af10.get("description", "")),
                        ))
                        existing_feat_names.add(af10_name)
                else:
                    lvl10_class_feats = [f for f in self.feats if f.get("target_level") in (8, 10) and _is_lu_class_feat(f) and _lu_valid(f, 10)]
                    cf10 = pick_weighted_feat(lvl10_class_feats, cls["name"], existing_feat_names, lu_skill_ranks, mods, 10, subclass_name=lu_sub_name, archetype_name=resolved_arch_name)
                    if cf10:
                        chosen_feats.append(FeatSummary(
                            id=cf10["id"],
                            name=cf10["name"],
                            category="Class Feat (Level 10)",
                            action_cost=safe_action_cost(cf10.get("action_cost")),
                            traits=cf10.get("traits", [cls_name_lower]),
                            description=clean_pf2e_text(cf10["description"]),
                        ))
                        existing_feat_names.add(cf10["name"])

                skill_feats_10 = [
                    f for f in self.feats
                    if f.get("category") == "skill"
                    and f.get("name", "").lower() != "cushion landing"
                    and "archetype" not in [t.lower() for t in f.get("traits", [])]
                    and f.get("target_level", 1) <= 10
                    and f["name"] not in existing_feat_names
                    and _lu_valid(f, 10)
                ]
                sf10 = pick_weighted_feat(skill_feats_10, cls["name"], existing_feat_names, lu_skill_ranks, mods, 10, subclass_name=lu_sub_name, archetype_name=resolved_arch_name)
                if sf10:
                    chosen_feats.append(FeatSummary(
                        id=sf10["id"],
                        name=sf10["name"],
                        category="Skill Feat (Level 10)",
                        action_cost=safe_action_cost(sf10.get("action_cost")),
                        traits=sf10.get("traits", ["skill"]),
                        description=clean_pf2e_text(sf10.get("description", "")),
                    ))
                    existing_feat_names.add(sf10["name"])

            elif 11 <= lvl <= 20:
                total_hp, _ = self._grant_tier3_feats(
                    subclass_name=lu_sub_name or "",
                    lvl=lvl,
                    anc_name=anc["name"],
                    cls_name=cls["name"],
                    chosen_feats=chosen_feats,
                    existing_feat_names=existing_feat_names,
                    archetype_data=archetype_data,
                    gate_elements=gate_elements,
                    mods=mods,
                    total_hp=total_hp,
                    bonus_speed=0,
                )

        # Backfill allotted Skill Feat slots
        existing_skill_cats_lu = {f.category for f in chosen_feats}
        owned_all_lu = {f.name for f in chosen_feats}
        sk_step_lu = 1 if cls_name_lower in ("rogue", "investigator") else 2
        for ev_lvl in range(2, target_level + 1, sk_step_lu):
            cat_label = f"Skill (Level {ev_lvl})"
            if cat_label not in existing_skill_cats_lu:
                ev_pool = [
                    f for f in self.feats
                    if f.get("category") == "skill"
                    and f.get("name", "").lower() != "cushion landing"
                    and "archetype" not in [t.lower() for t in f.get("traits", [])]
                    and f.get("target_level", 1) <= ev_lvl
                    and f["name"] not in owned_all_lu
                    and ("additional lore" not in f["name"].lower() or can_take_additional_lore(owned_all_lu, cls["name"]))
                    and check_feat_prerequisites(
                        f,
                        skill_ranks=lu_skill_ranks,
                        owned_feat_names=owned_all_lu,
                        attribute_mods=mods,
                        character_level=ev_lvl,
                        subclass_name=lu_sub_name,
                        archetype_name=resolved_arch_name,
                        perception_rank=lu_perc_rank,
                    )
                ]
                ev_sf = pick_weighted_feat(ev_pool, cls["name"], owned_all_lu, lu_skill_ranks, mods, ev_lvl, subclass_name=lu_sub_name, archetype_name=resolved_arch_name)
                if ev_sf:
                    ev_sf_name = resolve_feat_subchoices(ev_sf["name"], owned_all_lu)
                    chosen_feats.append(FeatSummary(
                        id=ev_sf["id"],
                        name=ev_sf_name,
                        category=cat_label,
                        action_cost=safe_action_cost(ev_sf.get("action_cost")),
                        traits=ev_sf.get("traits", ["skill"]),
                        description=enrich_feat_description(ev_sf_name, ev_sf.get("description", "")),
                    ))
                    owned_all_lu.add(ev_sf_name)
                    existing_skill_cats_lu.add(cat_label)

        if any(f.name.lower() == "toughness" for f in chosen_feats):
            total_hp += target_level

        raw_sub = current_char.get("subclass")
        if raw_sub and raw_sub.get("name"):
            subclass_obj = SubclassSummary(**raw_sub)
        elif current_char.get("companion") and current_char["companion"].get("name"):
            comp = current_char["companion"]
            subclass_obj = SubclassSummary(
                title="Eidolon" if cls_name_lower == "summoner" else "Companion",
                name=comp["name"],
                description=comp.get("creature_type", ""),
            )
        else:
            subclass_obj = None

        sub_name = subclass_obj.name if subclass_obj else None

        spellcasting_data = resolve_spellcasting(
            class_name=cls["name"],
            attribute_mods=mods,
            level=target_level,
            subclass_name=sub_name,
            feats=chosen_feats,
            concept_text=None,
        )

        existing_deity_name = (current_char.get("deity") or {}).get("name") if isinstance(current_char.get("deity"), dict) else getattr(current_char.get("deity"), "name", None)
        selected_deity = select_deity(
            deity_name=existing_deity_name,
            class_name=cls["name"],
            background_name=bg["name"],
            ancestry_name=anc["name"],
            subclass_name=sub_name,
            domain_name=current_char.get("domain") or (next(iter((current_char.get("deity") or {}).get("chosen_domains") or []), None) if isinstance(current_char.get("deity"), dict) else None),
        )
        deity_summary = _build_deity_summary(selected_deity, chosen_feats)
        focus_data = resolve_focus_spells(
            class_name=cls["name"],
            feats=chosen_feats,
            attribute_mods=mods,
            subclass_name=sub_name,
            level=target_level,
            deity_data=selected_deity,
        )

        raw_companion = current_char.get("companion")
        if raw_companion and raw_companion.get("name"):
            companion_data = PartnerCreatureData(**scale_existing_companion(
                companion_data=raw_companion,
                old_level=old_level,
                target_level=target_level,
                master_hp=total_hp,
            ))
        else:
            companion_data = resolve_companion(
                class_name=cls["name"],
                feats=chosen_feats,
                archetype=resolved_arch_name,
                level=target_level,
            )

        raw_extra_partners = current_char.get("additional_partners") or []
        existing_extra_partners = [
            PartnerCreatureData(**scale_existing_companion(p, old_level, target_level, total_hp)) if isinstance(p, dict) else p
            for p in raw_extra_partners
        ]
        combined_partners = ([companion_data] if companion_data else []) + existing_extra_partners

        if target_level >= 2 and resolved_arch_name and "archer" in resolved_arch_name.lower() and equipment_loadout and equipment_loadout.strikes:
            if not any(any(kw in (st.name or "").lower() for kw in ("bow", "shortbow", "longbow")) for st in equipment_loadout.strikes):
                new_bow = _build_archer_bow_strike(target_level, mods.get("dex", 0))
                phys = [
                    s for s in equipment_loadout.strikes
                    if not any(k in (s.name or "").lower() for k in ("elemental blast", "rage strike", "alchemist's fire"))
                ]
                if len(phys) >= 3:
                    equipment_loadout.strikes[equipment_loadout.strikes.index(phys[-1])] = new_bow
                else:
                    equipment_loadout.strikes.append(new_bow)

        _attach_named_artillery_strike(chosen_feats, equipment_loadout, target_level, mods)
        self._enforce_granted_feat_skill_prereqs(
            chosen_feats,
            all_skills,
            target_level,
            mods,
            include_all_feats=False,
            allow_generic_rk=False,
            fallback_lore_name="Scribing Lore",
        )

        return self._sync_feat_skill_prereqs(self._finalize_sheet(
            name=current_char["name"],
            level=target_level,
            anc=anc,
            ancestry_description=clean_pf2e_text(anc.get("description", "")) or current_char.get("ancestry_description", ""),
            heritage_name=current_char["heritage"],
            background_name=current_char["background"],
            background_description=clean_pf2e_text(bg.get("description", "")) or current_char.get("background_description", ""),
            cls=cls,
            subclass_data=None,
            subclass_obj=subclass_obj,
            archetype_name=resolved_arch_name,
            archetype_description=current_char.get("archetype_description") or (
                clean_pf2e_text(archetype_data.get("level_2_dedication", {}).get("description", "")) if archetype_data else None
            ),
            size=anc.get("size", current_char.get("size", "med")),
            speed=anc.get("speed", current_char.get("speed", 25)),
            mods=mods,
            calculated_ac=calculated_ac,
            shield_bonus=shield_bonus,
            total_hp=total_hp,
            fort_prof=fort_prof,
            ref_prof=ref_prof,
            will_prof=will_prof,
            perception_prof=perception_prof,
            all_skills=all_skills,
            equipment_loadout=equipment_loadout,
            chosen_feats=chosen_feats,
            traits=current_char.get("traits", [anc["name"].lower(), cls["name"].lower()]),
            existing_partners=combined_partners,
            existing_languages=list(current_char.get("languages") or ["Common"]),
            old_int=raw_attrs.get("int", raw_attrs.get("intelligence", 0)),
            deity_name=(selected_deity.get("name") if isinstance(selected_deity, dict) else None) or locals().get("existing_deity_name"),
            domain_name=(current_char.get("domain") or (next(iter((current_char.get("deity") or {}).get("chosen_domains") or []), None) if isinstance(current_char.get("deity"), dict) else None)),
        ))
