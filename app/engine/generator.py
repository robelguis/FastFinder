
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
from app.engine.progression import (
    get_class_saving_throws,
    get_weapon_prof_bonus_delta,
    get_weapon_spec_bonus,
    apply_remaster_level_boosts,
)
from app.engine.names import generate_ancestry_name
from app.engine.equipment import resolve_equipment, get_fundamental_rune_tiers
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
) -> list:
    partners = list(existing_partners)
    feat_names = [f.name.lower() for f in chosen_feats]
    all_feat_str = " ".join(feat_names)
    arch_str = (archetype_name or "").lower()
    cls_lower = class_name.lower()

    existing_types = {(p.creature_type or "").lower() for p in partners}
    existing_subs = {(p.sub_type or "").lower() for p in partners}

    has_familiar = any("familiar" in t or "familiar" in s for t, s in zip(existing_types, existing_subs))
    has_animal = any("animal" in t or "companion" in t for t in existing_types)
    has_undead = any("undead" in t for t in existing_types)
    has_plant = any("plant" in t for t in existing_types)
    has_construct = any("construct" in t for t in existing_types)

    # 1. Undead Companion / Undead Master
    if not has_undead and ("undead master" in arch_str or "undead companion" in all_feat_str):
        partners.append(resolve_undead_companion(level=level))
        has_undead = True

    # 2. Construct Companion / Clockwork Reanimator
    if not has_construct and ("clockwork reanimator" in arch_str or "construct companion" in all_feat_str or "prototype companion" in all_feat_str):
        partners.append(resolve_construct_companion(master_int_mod=2, level=level))
        has_construct = True

    # 3. Plant Companion (only when Plant Companion feat is actually taken)
    if not has_plant and "plant companion" in all_feat_str:
        partners.append(resolve_plant_companion(level=level))
        has_plant = True

    # 4. Animal Companion / Mounts (Beastmaster, Cavalier, Mammoth Lord, Animal Companion)
    animal_triggers = ("animal companion", "mature animal companion", "mount", "bonded animal")
    animal_arch_triggers = ("beastmaster", "cavalier", "mammoth lord")
    if not has_animal and (
        any(tr in all_feat_str for tr in animal_triggers)
        or (level >= 2 and any(ar in arch_str for ar in animal_arch_triggers))
    ):
        comp = resolve_companion(
            class_name=class_name,
            feats=chosen_feats,
            archetype=archetype_name if (archetype_name and level >= 2) else None,
            level=level,
        )
        if comp:
            partners.append(comp)
            has_animal = True

    # 5. Familiars & Pets (Leaf Order Leshy Familiar, Marine Ally, Familiar, Pet, Familiar Master, etc.)
    has_marine_ally = "marine ally" in feat_names
    is_leaf_leshy = ("leshy familiar" in all_feat_str) or (cls_lower == "druid" and "leaf" in all_feat_str)
    familiar_triggers = (
        "familiar",
        "marine ally",
        "leshy familiar",
        "elemental familiar",
        "shadow familiar",
        "spirit guide",
        "glyph familiar",
        "call wizardly tools",
    )
    has_pet_feat = "pet" in feat_names

    if not has_familiar and cls_lower != "witch":
        if has_marine_ally or is_leaf_leshy or any(tr in all_feat_str for tr in familiar_triggers) or (level >= 2 and "familiar master" in arch_str):
            partners.append(
                resolve_familiar(
                    master_ac=master_ac,
                    master_fort=master_fort,
                    master_ref=master_ref,
                    master_will=master_will,
                    master_perception=master_perception,
                    class_name=class_name,
                    level=level,
                    aquatic_only=has_marine_ally,
                    is_pet=False,
                    forced_species="leshy" if is_leaf_leshy else None,
                )
            )
            has_familiar = True
        elif has_pet_feat:
            partners.append(
                resolve_familiar(
                    master_ac=master_ac,
                    master_fort=master_fort,
                    master_ref=master_ref,
                    master_will=master_will,
                    master_perception=master_perception,
                    class_name=class_name,
                    level=level,
                    aquatic_only=False,
                    is_pet=True,
                )
            )
            has_familiar = True

    return partners


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
        taken_lores = {
            fn.split("(", 1)[1].rstrip(")").strip().lower()
            for fn in existing_feat_names
            if "additional lore" in fn.lower() and "(" in fn and ")" in fn
        }
        available_lores = [l for l in lore_pool if l.lower() not in taken_lores]
        chosen = random.choice(available_lores) if available_lores else random.choice(lore_pool)
        return f"{feat_name} ({chosen})"

    return feat_name


def can_take_additional_lore(existing_feat_names: set, cls_name: str, archetype_name: str = "") -> bool:
    is_bard = (cls_name or "").strip().lower() == "bard"
    has_bard_ded = "bard" in (archetype_name or "").lower() or any(
        "bard dedication" in fn.lower() for fn in existing_feat_names
    )
    current_count = sum(1 for fn in existing_feat_names if "additional lore" in fn.lower())
    if is_bard or has_bard_ded:
        return current_count < 23
    return current_count < 2


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
    },
    "stellar misfortune": {
        "name": "Stellar Misfortune",
        "action_cost": 1,
        "traits": ["Concentrate", "Occult", "Prediction"],
        "description": "You call upon the indifferent cold of the stars to curse an enemy's next step, imposing misdirection or misfortune on their rolls. Attempt an Occultism check or spell attack against the target."
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
WING_NATURAL_ANCESTRIES = {"strix", "sprite", "awakened animal"}
WING_NATURAL_HERITAGES = {"dragonblood", "beastkin", "tiefling", "aasimar", "nephilim", "sylph"}

def character_has_natural_wings(ancestry_name: str, heritage_name: str, feats: List[FeatSummary]) -> bool:
    anc_l = (ancestry_name or "").lower().strip()
    her_l = (heritage_name or "").lower().strip()
    
    if anc_l in WING_NATURAL_ANCESTRIES:
        return True
    if any(h in her_l for h in WING_NATURAL_HERITAGES):
        return True
    
    feat_text = " ".join([f.name.lower() + " " + f.description.lower() for f in feats])
    if "wing" in feat_text or "fly speed" in feat_text:
        return True
        
    return False

def apply_wing_graft_investment(
    ancestry_name: str,
    heritage_name: str,
    chosen_feats: List[FeatSummary],
    equipment_loadout: Any
):
    """
    If the character takes Winged Warrior and does not have natural wings,
    injects the Wing Graft (Beast Graft) into equipment and adds an Archetype Feature feat.
    """
    if character_has_natural_wings(ancestry_name, heritage_name, chosen_feats):
        return

    # 1. Prevent duplicate feat injection
    feat_names = {f.name for f in chosen_feats}
    if "Wing Graft Investment" not in feat_names:
        chosen_feats.append(FeatSummary(
            id="graft-wing-beast-graft",
            name="Wing Graft Investment",
            category="Graft Modification",
            action_cost=None,
            traits=["Invested", "Magical", "Transmutation"],
            description=(
                f"{WING_GRAFT_ITEM['name']} ({WING_GRAFT_ITEM['price']}): "
                f"{WING_GRAFT_ITEM['description']} (Occupies 1 Investiture slot)."
            )
        ))

    # 2. Add to equipment loadout if an items/worn list exists
    if hasattr(equipment_loadout, "items") and isinstance(equipment_loadout.items, list):
        if not any("Wing Graft" in (i if isinstance(i, str) else i.get("name", "")) for i in equipment_loadout.items):
            equipment_loadout.items.append(WING_GRAFT_ITEM["name"])
    elif hasattr(equipment_loadout, "worn") and isinstance(equipment_loadout.worn, list):
        if not any("Wing Graft" in (i if isinstance(i, str) else i.get("name", "")) for i in equipment_loadout.worn):
            equipment_loadout.worn.append(WING_GRAFT_ITEM["name"])


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

    def _grant_tier3_feats(
        self,
        *,
        lvl: int,
        anc_name: str,
        cls_name: str,
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

        if lvl in (11, 15, 19):
            gen_pool = [
                f for f in self.feats
                if f.get("category") == "general"
                and f.get("level", 1) <= lvl
                and f["name"] not in existing_feat_names
                and can_take_dedication(f["name"], chosen_feats, existing_feat_names)
                and check_feat_prerequisites(f, {}, existing_feat_names, mods, lvl)
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
                    and check_feat_prerequisites(f, {}, existing_feat_names, mods, lvl)
                ]
                if cls_pool:
                    cf = pick_weighted_feat(cls_pool, cls_name, existing_feat_names, {}, mods, lvl) or random.choice(cls_pool)
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
                and check_feat_prerequisites(f, {}, existing_feat_names, mods, lvl)
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

        # Skill feats at 12, 14 (all classes) and 11, 13, 15 (Rogue/Investigator; 15 for all classes too)
        if lvl in (12, 14, 15, 16, 18, 20) or (lvl in (11, 13, 17, 19) and cls_lower in ("rogue", "investigator")):
            sk_pool = [
                f for f in self.feats
                if f.get("category") == "skill"
                and f.get("level", 1) <= lvl
                and f["name"] not in existing_feat_names
                and ("additional lore" not in f["name"].lower() or can_take_additional_lore(existing_feat_names, cls_name, archetype_data.get("name", "") if archetype_data else ""))
                and check_feat_prerequisites(f, {}, existing_feat_names, mods, lvl)
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
        fort_prof,
        ref_prof,
        will_prof,
        perception_prof,
        all_skills: list,
        equipment_loadout,
        chosen_feats: List[FeatSummary],
        traits: List[str],
        existing_partners: Optional[List[PartnerCreatureData]] = None,
        existing_languages: Optional[List[str]] = None,
        old_int: int = 0,
    ) -> CharacterSheet:
        cls_name_lower = cls["name"].lower()
        sub_name = (
            subclass_data.get("name")
            if isinstance(subclass_data, dict)
            else (subclass_obj.name if subclass_obj else None)
        )

        # Partners: seed class-innate partners on fresh generation, or preserve existing on level-up
        if existing_partners is None:
            collected_partners: List[PartnerCreatureData] = []
            if cls_name_lower == "summoner":
                eidolon_partner = resolve_eidolon(master_hp=total_hp, level=level, eidolon_type=sub_name or "")
                collected_partners.append(eidolon_partner)
                if eidolon_partner:
                    e_type = getattr(eidolon_partner, "creature_type", "")
                    if not e_type or e_type == "Eidolon":
                        e_type = getattr(eidolon_partner, "stage", "Eidolon")
                    subclass_obj = SubclassSummary(name=e_type, title="Eidolon", description=f"{e_type} tactical partner")
                    sub_name = e_type
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
                        level=level,
                    ))
                else:
                    collected_partners.append(resolve_familiar(
                        master_ac=calculated_ac,
                        master_fort=fort_prof.modifier,
                        master_ref=ref_prof.modifier,
                        master_will=will_prof.modifier,
                        master_perception=perception_prof.modifier,
                        class_name=cls["name"],
                        level=level,
                    ))
        else:
            collected_partners = list(existing_partners)

        collected_partners = sync_feat_partners(
            existing_partners=collected_partners,
            chosen_feats=chosen_feats,
            archetype_name=archetype_name if level >= 2 else None,
            class_name=cls["name"],
            level=level,
            master_ac=calculated_ac,
            master_fort=fort_prof.modifier,
            master_ref=ref_prof.modifier,
            master_will=will_prof.modifier,
            master_perception=perception_prof.modifier,
        )

        primary_companion = collected_partners[0] if collected_partners else None
        extra_partners = collected_partners[1:] if len(collected_partners) > 1 else []

        spellcasting_data = resolve_spellcasting(
            class_name=cls["name"],
            attribute_mods=mods,
            level=level,
            subclass_name=sub_name,
            feats=chosen_feats,
        )

        focus_data = resolve_focus_spells(
            class_name=cls["name"],
            feats=chosen_feats,
            attribute_mods=mods,
            subclass_name=sub_name,
            level=level,
        )

        COMMON_LANG_POOL = [
            "Common", "Dwarven", "Elven", "Gnomish", "Goblin", "Halfling",
            "Orcish", "Draconic", "Sylvan", "Undercommon", "Jotun", "Necril",
            "Aklo", "Celestial", "Abyssal", "Infernal", "Shadowtongue", "Iruxi",
        ]

        if existing_languages is None:
            assigned_langs: List[str] = []
            assigned_lower: Set[str] = set()

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

        # Refresh & annotate Sneak Attack damage dice
        for f in chosen_feats:
            if f.name.lower() == "sneak attack":
                cur_dice = get_sneak_attack_dice(level, is_archetype=False)
                f.description = f"When your Strike hits an off-guard target and deals damage, you deal an extra {cur_dice} precision damage."
            elif f.name.lower() == "sneak attacker":
                cur_dice = get_sneak_attack_dice(level, is_archetype=True)
                f.description = f"You gain the Sneak Attack class feature, dealing an extra {cur_dice} precision damage to off-guard targets."

        has_sneak = any("sneak attack" in f.name.lower() or "sneak attacker" in f.name.lower() for f in chosen_feats)
        if has_sneak:
            is_arch_sneak = any("sneak attacker" in f.name.lower() for f in chosen_feats) and cls_name_lower != "rogue"
            s_dice_val = get_sneak_attack_dice(level, is_archetype=is_arch_sneak)
            for st in equipment_loadout.strikes:
                if "precision" not in st.damage_dice.lower() and "sneak" not in st.damage_dice.lower():
                    st.damage_dice = f"{st.damage_dice} (+{s_dice_val} precision vs off-guard)"

        return CharacterSheet(
            name=name,
            level=level,
            ancestry=anc["name"],
            ancestry_description=ancestry_description,
            heritage=heritage_name,
            background=background_name,
            background_description=background_description,
            character_class=cls["name"],
            subclass=subclass_obj,
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
        level = max(1, min(20, int(level)))

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

        if level >= 10:
            lvl10_boosts_applied: Set[str] = set()
            lvl10_priority = [key_attr, "con", "dex", "wis", "str", "int", "cha"]
            for attr in lvl10_priority:
                if len(lvl10_boosts_applied) < 4 and attr not in lvl10_boosts_applied:
                    mods[attr] += 1
                    lvl10_boosts_applied.add(attr)

        if level >= 15:
            # PF2e Remaster partial boost rule: attributes >= +4 require 2 boosts (10->partial, 15->+1)
            lvl15_boosts_applied: Set[str] = set()
            lvl15_priority = [key_attr, "con", "dex", "wis", "str", "int", "cha"]
            for attr in lvl15_priority:
                if len(lvl15_boosts_applied) < 4 and attr not in lvl15_boosts_applied:
                    if mods[attr] < 4 or attr in lvl10_boosts_applied:
                        mods[attr] += 1
                    lvl15_boosts_applied.add(attr)

        if level >= 20:
            lvl20_boosts_applied: Set[str] = set()
            lvl20_priority = [key_attr, "con", "dex", "wis", "str", "int", "cha"]
            for attr in lvl20_priority:
                if len(lvl20_boosts_applied) < 4 and attr not in lvl20_boosts_applied:
                    if mods[attr] < 4 or attr in lvl15_boosts_applied:
                        mods[attr] += 1
                    lvl20_boosts_applied.add(attr)

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

        extra_prof = get_weapon_prof_bonus_delta(cls["name"], level)
        if extra_prof:
            for strike in equipment_loadout.strikes:
                strike.attack_bonus += extra_prof
                strike.map_second += extra_prof
                strike.map_third += extra_prof
        spec_dmg = get_weapon_spec_bonus(cls["name"], level)
        if spec_dmg:
            for strike in equipment_loadout.strikes:
                if f"+{spec_dmg}" not in strike.damage_dice and "Weapon Spec" not in strike.damage_dice:
                    strike.damage_dice = f"{strike.damage_dice} + {spec_dmg}" 

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
        extra_trained_skill: Optional[str] = None
        chosen_feats: List[FeatSummary] = []
        added_feat_names = set()
        
        bg_desc = bg.get("description", "")
        bg_feat_name = extract_bg_feat(bg_desc, self.feats)

        # 0. Prevent background actions (like Stellar Misfortune) from being treated as passive feats
        if bg_feat_name and any(act_key in bg_feat_name.lower() for act_key in BACKGROUND_CUSTOM_ACTIONS.keys()):
            bg_feat_name = None

        # 1. Handle Background Feat (General/Skill feat granted by background)
        if bg_feat_name and bg_feat_name.lower() not in added_feat_names:
            matched_feat_def = next((f for f in self.feats if f["name"].lower() == bg_feat_name.lower()), None)
            feat_desc = clean_pf2e_text(matched_feat_def.get("description", "")) if matched_feat_def else f"Granted by the {bg['name']} background."

            chosen_feats.append(FeatSummary(
                id=f"feat-bg-{bg_feat_name.lower().replace(' ', '-')}",
                name=bg_feat_name,
                category="Background Feat",
                action_cost=safe_action_cost(matched_feat_def.get("action_cost")) if matched_feat_def else None,
                traits=matched_feat_def.get("traits", ["General", "Skill"]) if matched_feat_def else ["General", "Skill"],
                description=feat_desc
            ))
            added_feat_names.add(bg_feat_name.lower())

        # 2. Handle Explicit Background Actions via BACKGROUND_CUSTOM_ACTIONS registry only
        for act_key, c_act in BACKGROUND_CUSTOM_ACTIONS.items():
            if act_key in bg_desc.lower() and c_act["name"].lower() not in added_feat_names:
                chosen_feats.append(FeatSummary(
                    id=f"feat-bg-action-{act_key.replace(' ', '-')}",
                    name=c_act["name"],
                    category="Background Action",
                    action_cost=c_act.get("action_cost", 1),
                    traits=c_act.get("traits", ["Background", "Action"]),
                    description=c_act["description"]
                ))
                added_feat_names.add(c_act["name"].lower())

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
                if "bloodrager dedication" in ded["name"].lower() and not any("harvest blood" in f.name.lower() for f in chosen_feats):
                    chosen_feats.append(FeatSummary(
                        id="bloodrager-harvest-blood",
                        name="Harvest Blood",
                        category="Archetype Action (Bloodrager)",
                        action_cost="1",
                        traits=["archetype", "concentrate", "rage"],
                        description="Requirements: Your last action was a successful melee Strike that dealt slashing or piercing damage to a living creature with blood. You drink or absorb the spilled blood to gain temporary HP equal to half your level and empower your bloodrager spells."
                    ))

                # --- HOOK: Winged Warrior Graft Investment ---
                if "winged warrior" in archetype_data["name"].lower():
                    apply_wing_graft_investment(
                        ancestry_name=anc["name"],
                        heritage_name=heritage_data["name"],
                        chosen_feats=chosen_feats,
                        equipment_loadout=equipment_loadout
                    )
                # ---------------------------------------------
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
            skill_feats_2 = [f for f in self.feats if f.get("category") == "skill" and f.get("level") in [1, 2] and ("additional lore" not in f["name"].lower() or can_take_additional_lore(owned_names, cls["name"]))]
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
            arch_lvl4 = None
            if archetype_data:
                owned_lvl4 = {f.name for f in chosen_feats}
                valid_arch_4 = [f for f in archetype_data.get("level_4_feats", []) if f["name"] not in owned_lvl4]
                arch_lvl4 = random.choice(valid_arch_4) if valid_arch_4 else None
            if archetype_data and arch_lvl4:
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
             and ("additional lore" not in f["name"].lower() or can_take_additional_lore(owned_names, cls["name"]))]
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

        if level >= 9:
            anc_name_lower = anc["name"].lower()
            owned_f_names = {f.name.lower() for f in chosen_feats}
            lvl9_anc_feats = [
                f for f in self.feats
                if f.get("category") == "ancestry"
                and f.get("level") in (5, 9)
                and anc_name_lower in [t.lower() for t in f.get("traits", [])]
                and f["name"].lower() not in owned_f_names
            ]
            if lvl9_anc_feats:
                af9 = random.choice(lvl9_anc_feats)
                chosen_feats.append(FeatSummary(
                    id=af9["id"],
                    name=af9["name"],
                    category="Ancestry (Level 9)",
                    action_cost=af9.get("action_cost"),
                    traits=af9.get("traits", []),
                    description=clean_pf2e_text(af9.get("description", ""))
                ))
            else:
                fallback_af9 = {"name": f"{anc['name']} Expertise", "description": "You draw on deeper heritage resilience."}
                chosen_feats.append(FeatSummary(
                    id=f"anc-feat-{anc_name_lower}-9",
                    name=fallback_af9["name"],
                    category="Ancestry (Level 9)",
                    action_cost=None,
                    traits=[anc_name_lower],
                    description=clean_pf2e_text(fallback_af9["description"])
                ))

        planned_arch = archetype_name.strip() if archetype_name and archetype_name.strip() else None
        if planned_arch:
            arch_lower = planned_arch.lower()
            if "champion" in arch_lower:
                mods["str"] = max(mods.get("str", 0), 2)
                mods["cha"] = max(mods.get("cha", 0), 2)
            elif "rogue" in arch_lower:
                mods["dex"] = max(mods.get("dex", 0), 2)

        if level >= 11:
            owned_t3 = {f.name for f in chosen_feats}
            for t3_lvl in range(11, level + 1):
                total_hp, bonus_speed = self._grant_tier3_feats(
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

        return self._finalize_sheet(
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
            archetype_name=clean_arch_input or (archetype_data["name"] if archetype_data and level >= 2 else None),
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
        )
    def generate_epic_backstory(char_data: dict) -> list:
    name = char_data.get("name") or "The Hero"
    ancestry = char_data.get("ancestry") or "Human"
    cls = char_data.get("character_class") or "Adventurer"
    lvl = int(char_data.get("level") or 1)
    bg = char_data.get("background") or "unknown origins"
    
    # Scale narrative tone dynamically based on level
    if lvl == 1:
        zenith_narrative = f"Now taking their first steps at Level {lvl} as a {cls}, {name} leaves the safety of life as a {bg} behind, stepping out into a vast and dangerous world with little more than raw determination."
    elif lvl <= 5:
        zenith_narrative = f"Having grown accustomed to the perils of the road at Level {lvl}, {name}'s early trials as a {cls} have begun to forge a genuine reputation across the local frontier."
    elif lvl <= 15:
        zenith_narrative = f"Now a seasoned adventurer at Level {lvl}, {name}'s exploits as a {cls} are spoken of with growing respect as regional powers take notice of their rising influence."
    else:
        zenith_narrative = f"Standing at the absolute zenith of power as a Level {lvl} {cls}, {name} commands a legendary presence across the realm, their epic feats echoing through history like a force of nature."

    return [
        {
            "chapter": "Chapter I: Roots in the Dust",
            "narrative": f"Long before the weight of legendary arms rested upon {name}'s shoulders, there were quiet days spent as a {bg}. Raised amidst the rugged trials of the frontier, {name} learned early that survival is carved out of stubborn endurance rather than divine favor."
        },
        {
            "chapter": "Chapter II: The Awakening Spark",
            "narrative": f"As a {ancestry} navigating a world scarred by ancient powers, {name}'s path shifted when a latent calling took root. Stepping onto the path of the {cls}, every trial forged a sharper resolve, turning simple grit into disciplined power."
        },
        {
            "chapter": "Chapter III: The Legend Unfolds",
            "narrative": zenith_narrative
        }
    ]
    def level_up(
        self,
        current_char: Dict[str, Any],
        target_level: int,
        use_dedication: bool = False,
        archetype_name: Optional[str] = None
    ) -> CharacterSheet:
        target_level = max(1, min(20, int(target_level)))
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

        if old_level < 10 and target_level >= 10:
            lvl10_boosts_applied: Set[str] = set()
            lvl10_priority = [key_attr, "con", "dex", "wis", "str", "int", "cha"]
            for attr in lvl10_priority:
                if len(lvl10_boosts_applied) < 4 and attr not in lvl10_boosts_applied:
                    mods[attr] += 1
                    lvl10_boosts_applied.add(attr)
        elif old_level >= 10 and target_level < 10:
            lvl10_boosts_applied: Set[str] = set()
            lvl10_priority = [key_attr, "con", "dex", "wis", "str", "int", "cha"]
            for attr in lvl10_priority:
                if len(lvl10_boosts_applied) < 4 and attr not in lvl10_boosts_applied:
                    mods[attr] = max(0, mods[attr] - 1)
                    lvl10_boosts_applied.add(attr)

        if old_level < 15 and target_level >= 15:
            lvl15_boosts_applied: Set[str] = set()
            lvl15_priority = [key_attr, "con", "dex", "wis", "str", "int", "cha"]
            for attr in lvl15_priority:
                if len(lvl15_boosts_applied) < 4 and attr not in lvl15_boosts_applied:
                    mods[attr] += 1
                    lvl15_boosts_applied.add(attr)
        elif old_level >= 15 and target_level < 15:
            lvl15_boosts_applied: Set[str] = set()
            lvl15_priority = [key_attr, "con", "dex", "wis", "str", "int", "cha"]
            for attr in lvl15_priority:
                if len(lvl15_boosts_applied) < 4 and attr not in lvl15_boosts_applied:
                    mods[attr] = max(0, mods[attr] - 1)
                    lvl15_boosts_applied.add(attr)

        if old_level < 20 and target_level >= 20:
            lvl20_boosts_applied: Set[str] = set()
            lvl20_priority = [key_attr, "con", "dex", "wis", "str", "int", "cha"]
            for attr in lvl20_priority:
                if len(lvl20_boosts_applied) < 4 and attr not in lvl20_boosts_applied:
                    mods[attr] += 1
                    lvl20_boosts_applied.add(attr)
        elif old_level >= 20 and target_level < 20:
            lvl20_boosts_applied: Set[str] = set()
            lvl20_priority = [key_attr, "con", "dex", "wis", "str", "int", "cha"]
            for attr in lvl20_priority:
                if len(lvl20_boosts_applied) < 4 and attr not in lvl20_boosts_applied:
                    mods[attr] = max(0, mods[attr] - 1)
                    lvl20_boosts_applied.add(attr)

        # 3. Defenses & Proficiencies
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

        # 4. Equipment & Weapons Locking (Scales Runes, Armor, Shields, Consumables & Wealth to target_level)
        current_sub = (current_char.get("subclass") or {}).get("name", "") if isinstance(current_char.get("subclass"), dict) else ""
        gate_elements = extract_gate_elements(current_sub) if cls_name_lower == "kineticist" else set()
        current_arch = current_char.get("archetype") or ""
        raw_eq = current_char.get("equipment")
        if isinstance(raw_eq, dict):
            existing_weps = raw_eq.get("weapons") or raw_eq.get("strikes")
        elif raw_eq is not None:
            existing_weps = getattr(raw_eq, "weapons", None) or getattr(raw_eq, "strikes", None)
        else:
            existing_weps = None

        equipment_loadout, calculated_ac, shield_bonus = resolve_equipment(
            cls["name"],
            str_mod=mods["str"],
            dex_mod=mods["dex"],
            level=target_level,
            ancestry_name=anc["name"],
            subclass_name=current_sub,
            archetype_name=current_arch,
            existing_weapons=existing_weps,
        )

        extra_prof = get_weapon_prof_bonus_delta(cls["name"], target_level)
        if extra_prof:
            for strike in equipment_loadout.strikes:
                strike.attack_bonus += extra_prof
                strike.map_second += extra_prof
                strike.map_third += extra_prof
        spec_dmg = get_weapon_spec_bonus(cls["name"], target_level)
        if spec_dmg:
            for strike in equipment_loadout.strikes:
                if f"+{spec_dmg}" not in strike.damage_dice and "Weapon Spec" not in strike.damage_dice:
                    strike.damage_dice = f"{strike.damage_dice} + {spec_dmg}"

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
                fid = (f.id or "").lower()
                
                # Check level tags in category or ID (e.g. "Level 9", "-9", "level-8")
                m = re.search(r"level\s*(\d+)", cat)
                m_id = re.search(r"-(\d+)$", fid) or re.search(r"lvl(\d+)", fid)
                
                f_lvl = None
                if m:
                    f_lvl = int(m.group(1))
                elif m_id:
                    f_lvl = int(m_id.group(1))
                    
                if f_lvl and f_lvl > target_level:
                    continue
                    
                if target_level < 7 and f.name == "Weapon Specialization":
                    continue
                if target_level < 2 and f.id == "graft-wing-beast-graft":
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
                # --- HOOK: Winged Warrior Graft Investment on Level Up ---
                    if "winged warrior" in archetype_data["name"].lower():
                        apply_wing_graft_investment(
                            ancestry_name=anc["name"],
                            heritage_name=current_char.get("heritage", ""),
                            chosen_feats=chosen_feats,
                            equipment_loadout=equipment_loadout
                        )
                    # --------------------------------------------------------
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
                 and ("additional lore" not in f["name"].lower() or can_take_additional_lore(existing_feat_names, cls["name"]))]
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
                 and ("additional lore" not in f["name"].lower() or can_take_additional_lore(existing_feat_names, cls["name"]))]
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

            elif 11 <= lvl <= 20:
                total_hp, _ = self._grant_tier3_feats(
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
            elif lvl == 10:
                # Level 10: Class Feat (or Archetype Feat) & Skill Feat
                arch_feats_10 = []
                if archetype_data:
                    arch_feats_10 = [
                        f for f in archetype_data.get("level_10_feats", archetype_data.get("level_8_feats", []))
                        if f["name"] not in existing_feat_names
                    ]

                if arch_feats_10 and random.random() < 0.6:
                    af10 = random.choice(arch_feats_10)
                    chosen_feats.append(FeatSummary(
                        id=af10["id"],
                        name=af10["name"],
                        category=f"Archetype Feat (Level 10 - {archetype_data['name']})",
                        action_cost=None,
                        traits=["archetype"],
                        description=clean_pf2e_text(af10["description"])
                    ))
                    existing_feat_names.add(af10["name"])
                else:
                    lvl10_class_feats = [
                        f for f in self.feats
                        if f.get("category") == "class"
                        and f.get("level") in (8, 10)
                        and cls_name_lower in [t.lower() for t in f.get("traits", [])]
                        and (cls_name_lower != "kineticist" or is_kineticist_feat_allowed(f, gate_elements))
                        and f["name"] not in existing_feat_names
                    ]
                    if lvl10_class_feats:
                        skill_ranks_tmp = {s.get("name"): s.get("rank", 0) for s in current_char.get("skills", []) if isinstance(s, dict)}
                        cf10 = pick_weighted_feat(lvl10_class_feats, cls_name_lower, existing_feat_names, skill_ranks_tmp, {}, 10) or random.choice(lvl10_class_feats)
                        chosen_feats.append(FeatSummary(
                            id=cf10["id"],
                            name=cf10["name"],
                            category="Class Feat (Level 10)",
                            action_cost=safe_action_cost(cf10.get("action_cost")),
                            traits=cf10.get("traits", [cls_name_lower]),
                            description=clean_pf2e_text(cf10["description"])
                        ))
                        existing_feat_names.add(cf10["name"])

                # Level 10: Skill Feat
                skill_feats_10 = [
                    f for f in self.feats
                    if f.get("category") == "skill"
                    and f.get("level", 1) <= 10
                    and f["name"] not in existing_feat_names
                ]
                if skill_feats_10:
                    sf10 = random.choice(skill_feats_10)
                    chosen_feats.append(FeatSummary(
                        id=sf10["id"],
                        name=sf10["name"],
                        category="Skill Feat (Level 10)",
                        action_cost=safe_action_cost(sf10.get("action_cost")),
                        traits=sf10.get("traits", ["skill"]),
                        description=clean_pf2e_text(sf10.get("description", ""))
                    ))
                    existing_feat_names.add(sf10["name"])

            elif lvl == 9:
                # Level 9: Ancestry Feat
                anc_name_lower = (current_char.get("ancestry") or "").lower().strip()
                lvl9_anc_feats = [
                    f for f in self.feats
                    if f.get("category") == "ancestry"
                    and f.get("level") in (1, 5, 9)
                    and (not anc_name_lower or anc_name_lower in [t.lower() for t in f.get("traits", [])])
                    and f["name"] not in existing_feat_names
                ]
                if lvl9_anc_feats:
                    af9 = random.choice(lvl9_anc_feats)
                    chosen_feats.append(FeatSummary(
                        id=af9["id"],
                        name=af9["name"],
                        category="Ancestry Feat (Level 9)",
                        action_cost=None,
                        traits=af9.get("traits", ["ancestry"]),
                        description=clean_pf2e_text(af9.get("description", ""))
                    ))
                    existing_feat_names.add(af9["name"])
                else:
                    fallback_af9 = {
                        "name": f"{anc_name_lower.capitalize()} Resilience",
                        "description": "Your bond with your heritage deepens, granting increased durability against ancestry-specific hazards."
                    }
                    chosen_feats.append(FeatSummary(
                        id=f"anc-feat-{anc_name_lower}-9",
                        name=fallback_af9["name"],
                        category="Ancestry Feat (Level 9)",
                        action_cost=None,
                        traits=["ancestry"],
                        description=fallback_af9["description"]
                    ))
                    existing_feat_names.add(fallback_af9["name"])

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
                 and ("additional lore" not in f["name"].lower() or can_take_additional_lore(existing_feat_names, cls["name"]))]
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
            subclass_name=sub_name,
            feats=chosen_feats,
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
            PartnerCreatureData(**scale_existing_companion(p, old_level, target_level, total_hp)) if isinstance(p, dict)
            else p
            for p in raw_extra_partners
        ]
        combined_partners = ([companion_data] if companion_data else []) + existing_extra_partners

        return self._finalize_sheet(
            name=current_char["name"],
            level=target_level,
            anc=anc,
            ancestry_description=clean_pf2e_text(anc.get("description", "")) or current_char.get("ancestry_description", ""),
            heritage_name=current_char["heritage"],
            background_name=current_char["background"],
            background_description=current_char.get("background_description") or clean_pf2e_text(bg.get("description", "")),
            cls=cls,
            subclass_data=None,
            subclass_obj=subclass_obj,
            archetype_name=resolved_arch_name,
            archetype_description=current_char.get("archetype_description") or (clean_pf2e_text(archetype_data.get("level_2_dedication", {}).get("description", "")) if archetype_data else None),
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
        )
