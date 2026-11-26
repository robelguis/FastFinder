from app.engine.compendium import can_equip_item, COMPENDIUM_MAGIC_ITEMS
ALCHEMICAL_BOMBS = {
    "lesser": [
        {
            "name": "Alchemist's Fire (Lesser)",
            "dice": "1d8",
            "type": "Fire",
            "persistent": "1 persistent fire",
            "splash": "1 splash fire",
            "item_bonus": 0,
            "traits": ["Alchemical", "Bomb", "Consumable", "Fire", "Splash", "Thrown 20 ft"]
        },
        {
            "name": "Bottled Lightning (Lesser)",
            "dice": "1d6",
            "type": "Electricity",
            "persistent": "Off-Guard until start of next turn",
            "splash": "1 splash electricity",
            "item_bonus": 0,
            "traits": ["Alchemical", "Bomb", "Consumable", "Electricity", "Splash", "Thrown 20 ft"]
        },
        {
            "name": "Acid Flask (Lesser)",
            "dice": "1",
            "type": "Acid",
            "persistent": "1d6 persistent acid",
            "splash": "1 splash acid",
            "item_bonus": 0,
            "traits": ["Alchemical", "Acid", "Bomb", "Consumable", "Splash", "Thrown 20 ft"]
        },
        {
            "name": "Frost Vial (Lesser)",
            "dice": "1d6",
            "type": "Cold",
            "persistent": "-5 ft circumstance penalty to Speeds",
            "splash": "1 splash cold",
            "item_bonus": 0,
            "traits": ["Alchemical", "Bomb", "Cold", "Consumable", "Splash", "Thrown 20 ft"]
        }
    ],
    "moderate": [
        {
            "name": "Alchemist's Fire (Moderate)",
            "dice": "2d8",
            "type": "Fire",
            "persistent": "2 persistent fire",
            "splash": "2 splash fire",
            "item_bonus": 1,
            "traits": ["Alchemical", "Bomb", "Consumable", "Fire", "Splash", "Thrown 20 ft"]
        },
        {
            "name": "Bottled Lightning (Moderate)",
            "dice": "2d6",
            "type": "Electricity",
            "persistent": "Off-Guard until start of next turn",
            "splash": "2 splash electricity",
            "item_bonus": 1,
            "traits": ["Alchemical", "Bomb", "Consumable", "Electricity", "Splash", "Thrown 20 ft"]
        },
        {
            "name": "Acid Flask (Moderate)",
            "dice": "2",
            "type": "Acid",
            "persistent": "2d6 persistent acid",
            "splash": "2 splash acid",
            "item_bonus": 1,
            "traits": ["Alchemical", "Acid", "Bomb", "Consumable", "Splash", "Thrown 20 ft"]
        },
        {
            "name": "Frost Vial (Moderate)",
            "dice": "2d6",
            "type": "Cold",
            "persistent": "-10 ft circumstance penalty to Speeds",
            "splash": "2 splash cold",
            "item_bonus": 1,
            "traits": ["Alchemical", "Bomb", "Cold", "Consumable", "Splash", "Thrown 20 ft"]
        }
    ]
}

import re
import random
from typing import Dict, Any, List, Tuple, Optional
from app.engine.models import EquipmentLoadout, Item, Strike, Wealth, ConsumableItem
from app.engine.strikes import (
    compute_alchemical_bomb_strike,
    compute_strike,
    format_runed_strike_name,
)

# PF2e Remaster Character Wealth by Level (Lump sum alternative)
# Level: (lump_sum_gp, min_consumables, typical_permanent_items)
WEALTH_BY_LEVEL: Dict[int, Dict[str, Any]] = {
    1: {"lump_gp": 15, "permanent_count": 0},
    2: {"lump_gp": 30, "permanent_count": 1},
    3: {"lump_gp": 75, "permanent_count": 1},
    4: {"lump_gp": 140, "permanent_count": 2},
    5: {"lump_gp": 270, "permanent_count": 3},
    6: {"lump_gp": 450, "permanent_count": 4},
    7: {"lump_gp": 720, "permanent_count": 5},
    8: {"lump_gp": 1100, "permanent_count": 6},
    9: {"lump_gp": 1600, "permanent_count": 7},
    10: {"lump_gp": 2300, "permanent_count": 8},
    11: {"lump_gp": 3200, "permanent_count": 8},
    12: {"lump_gp": 4500, "permanent_count": 9},
    13: {"lump_gp": 6400, "permanent_count": 9},
    14: {"lump_gp": 9300, "permanent_count": 10},
    15: {"lump_gp": 13500, "permanent_count": 10},
    16: {"lump_gp": 20000, "permanent_count": 11},
    17: {"lump_gp": 30000, "permanent_count": 11},
    18: {"lump_gp": 45000, "permanent_count": 12},
    19: {"lump_gp": 69000, "permanent_count": 12},
    20: {"lump_gp": 112000, "permanent_count": 13},
}


def get_fundamental_rune_tiers(level: int) -> Dict[str, Any]:
    lvl = max(1, min(20, int(level)))
    wep_potency = 3 if lvl >= 16 else (2 if lvl >= 10 else (1 if lvl >= 2 else 0))
    if lvl >= 19:
        striking_label, dice_count = "Major Striking", 4
    elif lvl >= 12:
        striking_label, dice_count = "Greater Striking", 3
    elif lvl >= 4:
        striking_label, dice_count = "Striking", 2
    else:
        striking_label, dice_count = "", 1

    armor_potency = 3 if lvl >= 18 else (2 if lvl >= 11 else (1 if lvl >= 5 else 0))
    if lvl >= 20:
        resilient_label, save_item_bonus = "Major Resilient", 3
    elif lvl >= 14:
        resilient_label, save_item_bonus = "Greater Resilient", 2
    elif lvl >= 8:
        resilient_label, save_item_bonus = "Resilient", 1
    else:
        resilient_label, save_item_bonus = "", 0

    return {
        "wep_potency": wep_potency,
        "striking_label": striking_label,
        "dice_count": dice_count,
        "armor_potency": armor_potency,
        "resilient_label": resilient_label,
        "save_item_bonus": save_item_bonus,
    }


def _get_property_runes_and_crit_spec(weapon_name: str, traits: list, level: int, class_name: str = "") -> tuple[list[str], str]:
    w_low = (weapon_name or "").lower()
    t_low = [str(t).lower() for t in (traits or [])]
    tiers = get_fundamental_rune_tiers(level)
    pot = tiers.get("wep_potency", 0)
    dice = tiers.get("dice_count", 1)

    prop_runes: list[str] = []
    if pot >= 3 or dice >= 4:
        prop_runes = ["Flaming", "Shock", "Holy"]
    elif pot >= 2 or dice >= 3:
        prop_runes = ["Flaming", "Holy"]
    elif pot >= 1 or dice >= 2:
        prop_runes = ["Flaming"]

    if "shortsword" in w_low or "short sword" in w_low:
        crit_note = "Crit Spec (Sword/Agile/Finesse): Target is off-guard until start of your next turn; pairs with Agile/Finesse."
    elif "longbow" in w_low or "bow" in w_low:
        crit_note = "Crit Spec (Bow/Deadly d10): Target is pinned to an adjacent surface on crit (DC 10 Escape); Deadly d10 adds extra crit dice."
    elif "horn" in w_low or "gore" in w_low or "antler" in w_low or "unarmed" in t_low or "brawling" in t_low:
        crit_note = "Crit Spec (Brawling/Unarmed): Target must succeed at a Fortitude save or be slowed 1 until end of your next turn."
    elif any("sword" in tr or "blade" in tr or "rapier" in tr or "scimitar" in tr for tr in t_low):
        crit_note = "Crit Spec (Sword): Target is off-guard until the start of your next turn."
    elif any("axe" in tr for tr in t_low):
        crit_note = "Crit Spec (Axe): Choose one creature adjacent to target; deal 1 damage per weapon damage die to it."
    elif any("hammer" in tr or "flail" in tr or "club" in tr for tr in t_low):
        crit_note = "Crit Spec (Hammer/Flail): Target is knocked prone or pushed 5 feet on a failed Fortitude/Reflex check."
    elif any("spear" in tr or "polearm" in tr for tr in t_low):
        crit_note = "Crit Spec (Spear/Polearm): Target is off-guard until the start of your next turn."
    else:
        crit_note = "Crit Spec: Applies weapon group critical specialization effect on a critical hit."

    cls_low = (class_name or "").lower()
    has_crit_spec = (
        (cls_low == "exemplar" and level >= 1)
        or (cls_low == "fighter" and level >= 5)
        or (cls_low in ("barbarian", "champion", "monk", "ranger", "rogue", "swashbuckler", "gunslinger", "magus", "inventor", "thaumaturge", "commander", "guardian") and level >= 5)
        or (pot >= 2)
    )
    if not has_crit_spec:
        crit_note = ""
    elif cls_low == "exemplar":
        crit_note = f"{crit_note} [Ikon/Transcendence active]"

    return prop_runes, crit_note


def format_runed_weapon_name(base_name: str, level: int) -> str:
    return format_runed_strike_name(base_name, level, apply_prefix=True)


def format_runed_armor_name(base_name: str, level: int) -> str:
    tiers = get_fundamental_rune_tiers(level)
    parts = []
    if tiers["armor_potency"]:
        parts.append(f"+{tiers['armor_potency']}")
    if tiers["resilient_label"]:
        parts.append(tiers["resilient_label"])
    parts.append(base_name)
    return " ".join(parts)


def format_scaled_shield_name(base_shield: str, level: int) -> str:
    if level >= 19:
        return f"Sturdy Shield (Supreme) [{base_shield}]"
    if level >= 16:
        return f"Sturdy Shield (Major) [{base_shield}]"
    if level >= 13:
        return f"Sturdy Shield (Greater) [{base_shield}]"
    if level >= 10:
        return f"Sturdy Shield (Moderate) [{base_shield}]"
    if level >= 7:
        return f"Sturdy Shield (Lesser) [{base_shield}]"
    if level >= 4:
        return f"Sturdy Shield (Minor) [{base_shield}]"
    return base_shield

PERMANENT_MAGIC_ITEMS: List[Dict[str, Any]] = [
    {"name": "Healer's Gloves", "level": 3, "cost_gp": 50, "bulk": "L", "description": "+1 item bonus to Medicine; 1/day activate to heal 2d6+7 HP."},
    {"name": "Crafter's Eyepiece", "level": 3, "cost_gp": 60, "bulk": "-", "description": "+1 item bonus to Crafting checks and repairing."},
    {"name": "Hat of Disguise", "level": 2, "cost_gp": 30, "bulk": "L", "description": "Cast illusory disguise as an innate arcane spell at will."},
    {"name": "Boots of Elvenkind", "level": 5, "cost_gp": 145, "bulk": "L", "description": "+1 item bonus to Acrobatics; ignore difficult terrain 1/day."},
    {"name": "Cloak of the Bat", "level": 5, "cost_gp": 160, "bulk": "L", "description": "+1 item bonus to Stealth; 1/day fly or turn into a bat."},
    {"name": "Bracers of Missile Deflection", "level": 3, "cost_gp": 52, "bulk": "L", "description": "+1 circumstance bonus to AC against ranged attacks with reaction."}
]

# Categorized PF2e Weapon Pools for Rich Randomized Selection
MARTIAL_TWO_HANDED = [
    {"name": "Greatsword", "dice": "1d12", "type": "Slashing", "traits": ["Versatile P"]},
    {"name": "Greataxe", "dice": "1d12", "type": "Slashing", "traits": ["Sweep"]},
    {"name": "Maul", "dice": "1d12", "type": "Bludgeoning", "traits": ["Shove"]},
    {"name": "Halberd", "dice": "1d10", "type": "Piercing", "traits": ["Reach", "Versatile S"]},
    {"name": "Glaive", "dice": "1d8", "type": "Slashing", "traits": ["Deadly d8", "Forceful", "Reach"]},
    {"name": "Guisarme", "dice": "1d10", "type": "Slashing", "traits": ["Reach", "Trip"]},
    {"name": "Greatpick", "dice": "1d10", "type": "Piercing", "traits": ["Fatal d12"]},
]

MARTIAL_ONE_HANDED = [
    {"name": "Longsword", "dice": "1d8", "type": "Slashing", "traits": ["Versatile P"]},
    {"name": "Warhammer", "dice": "1d8", "type": "Bludgeoning", "traits": ["Shove"]},
    {"name": "Battleaxe", "dice": "1d8", "type": "Slashing", "traits": ["Sweep"]},
    {"name": "Flail", "dice": "1d6", "type": "Bludgeoning", "traits": ["Disarm", "Sweep", "Trip"]},
    {"name": "Pick", "dice": "1d6", "type": "Piercing", "traits": ["Fatal d10"]},
    {"name": "Scimitar", "dice": "1d6", "type": "Slashing", "traits": ["Forceful", "Sweep"]},
    {"name": "Trident", "dice": "1d8", "type": "Piercing", "traits": ["Thrown 20 ft"]},
]

MARTIAL_FINESSE = [
    {"name": "Rapier", "dice": "1d6", "type": "Piercing", "traits": ["Deadly d8", "Disarm", "Finesse"]},
    {"name": "Shortsword", "dice": "1d6", "type": "Piercing", "traits": ["Agile", "Finesse", "Versatile S"]},
    {"name": "Scourge", "dice": "1d4", "type": "Slashing", "traits": ["Agile", "Disarm", "Finesse", "Nonlethal", "Sweep"]},
    {"name": "Kukri", "dice": "1d6", "type": "Slashing", "traits": ["Agile", "Finesse", "Trip"]},
    {"name": "Sap", "dice": "1d6", "type": "Bludgeoning", "traits": ["Agile", "Finesse", "Nonlethal"]},
]

MARTIAL_RANGED = [
    {"name": "Composite Longbow", "dice": "1d8", "type": "Piercing", "traits": ["Deadly d10", "Propulsive", "Range 100 ft", "Volley 30 ft"]},
    {"name": "Composite Shortbow", "dice": "1d6", "type": "Piercing", "traits": ["Deadly d10", "Propulsive", "Range 60 ft"]},
    {"name": "Longbow", "dice": "1d8", "type": "Piercing", "traits": ["Deadly d10", "Range 100 ft", "Volley 30 ft"]},
    {"name": "Shortbow", "dice": "1d6", "type": "Piercing", "traits": ["Deadly d10", "Range 60 ft"]},
    {"name": "Heavy Crossbow", "dice": "1d10", "type": "Piercing", "traits": ["Range 120 ft", "Reload 2"]},
]

SIMPLE_MELEE = [
    {"name": "Spear", "dice": "1d6", "type": "Piercing", "traits": ["Thrown 20 ft"]},
    {"name": "Morningstar", "dice": "1d6", "type": "Bludgeoning", "traits": ["Versatile P"]},
    {"name": "Mace", "dice": "1d6", "type": "Bludgeoning", "traits": ["Shove"]},
    {"name": "Club", "dice": "1d6", "type": "Bludgeoning", "traits": ["Thrown 10 ft"]},
    {"name": "Longspear", "dice": "1d8", "type": "Piercing", "traits": ["Reach"]},
    {"name": "Sickle", "dice": "1d4", "type": "Slashing", "traits": ["Agile", "Finesse", "Trip"]},
    {"name": "Hatchet", "dice": "1d6", "type": "Slashing", "traits": ["Agile", "Sweep", "Thrown 10 ft"]},
]

SIMPLE_RANGED = [
    {"name": "Crossbow", "dice": "1d8", "type": "Piercing", "traits": ["Range 120 ft", "Reload 1"]},
    {"name": "Sling", "dice": "1d6", "type": "Bludgeoning", "traits": ["Propulsive", "Range 50 ft", "Reload 1"]},
    {"name": "Dart", "dice": "1d4", "type": "Piercing", "traits": ["Agile", "Thrown 20 ft"]},
    {"name": "Javelin", "dice": "1d6", "type": "Piercing", "traits": ["Thrown 30 ft"]},
]


ONE_HANDED_FIREARMS = [
    {"name": "Dueling Pistol", "dice": "1d6", "type": "Piercing", "traits": ["Concussive", "Fatal d10", "Range 60 ft", "Reload 1"]},
    {"name": "Flintlock Pistol", "dice": "1d4", "type": "Piercing", "traits": ["Concussive", "Fatal d8", "Range 40 ft", "Reload 1"]},
    {"name": "Slide Pistol", "dice": "1d6", "type": "Piercing", "traits": ["Capacity 5", "Concussive", "Fatal d10", "Range 30 ft", "Reload 1"]},
]

TWO_HANDED_SNIPER_FIREARMS = [
    {"name": "Arquebus", "dice": "1d8", "type": "Piercing", "traits": ["Concussive", "Fatal d12", "Kickback", "Range 150 ft", "Reload 1"]},
    {"name": "Flintlock Musket", "dice": "1d6", "type": "Piercing", "traits": ["Concussive", "Fatal d10", "Range 70 ft", "Reload 1", "Two-Hand d10"]},
    {"name": "Heavy Crossbow", "dice": "1d10", "type": "Piercing", "traits": ["Range 120 ft", "Reload 2"]},
]

VANGUARD_FIREARMS = [
    {"name": "Blunderbuss", "dice": "1d8", "type": "Piercing", "traits": ["Concussive", "Scatter 10 ft", "Range 40 ft", "Reload 1"]},
    {"name": "Dwarven Scattergun", "dice": "1d8", "type": "Piercing", "traits": ["Concussive", "Dwarf", "Kickback", "Range 50 ft", "Reload 1", "Scatter 10 ft"]},
]

SECONDARY_BACKUPS = [
    {"name": "Dagger", "dice": "1d4", "type": "Piercing", "traits": ["Agile", "Finesse", "Thrown 10 ft", "Versatile S"]},
    {"name": "Hatchet", "dice": "1d6", "type": "Slashing", "traits": ["Agile", "Sweep", "Thrown 10 ft"]},
    {"name": "Shortsword", "dice": "1d6", "type": "Piercing", "traits": ["Agile", "Finesse", "Versatile S"]},
    {"name": "Light Hammer", "dice": "1d6", "type": "Bludgeoning", "traits": ["Agile", "Thrown 20 ft"]},
    {"name": "Sap", "dice": "1d6", "type": "Bludgeoning", "traits": ["Agile", "Finesse", "Nonlethal"]},
    {"name": "Gauntlet", "dice": "1d4", "type": "Bludgeoning", "traits": ["Agile", "Free-Hand"]},
]


# Ancestral Weapons (Restricted by Ancestry)
ANCESTRAL_WEAPONS: Dict[str, List[Dict[str, Any]]] = {
    "goblin": [
        {"name": "Dogslicer", "dice": "1d6", "type": "Slashing", "traits": ["Agile", "Backstabber", "Finesse", "Goblin"]},
        {"name": "Horsechopper", "dice": "1d8", "type": "Piercing", "traits": ["Goblin", "Reach", "Trip", "Versatile S"]},
    ],
    "dwarf": [
        {"name": "Clan Dagger", "dice": "1d4", "type": "Piercing", "traits": ["Agile", "Dwarf", "Parry", "Versatile B"]},
        {"name": "Dwarven War Axe", "dice": "1d8", "type": "Slashing", "traits": ["Dwarf", "Sweep", "Two-Hand d12"]},
        {"name": "Dwarven Scattergun", "dice": "1d8", "type": "Piercing", "traits": ["Concussive", "Dwarf", "Kickback", "Range 50 ft", "Reload 1", "Scatter 10 ft"]},
    ],
    "elf": [
        {"name": "Elven Curve Blade", "dice": "1d8", "type": "Slashing", "traits": ["Elf", "Finesse", "Forceful"]},
        {"name": "Elven Branched Spear", "dice": "1d6", "type": "Piercing", "traits": ["Agile", "Deadly d8", "Elf", "Finesse", "Reach"]},
    ],
    "gnome": [
        {"name": "Gnome Flickmace", "dice": "1d8", "type": "Bludgeoning", "traits": ["Gnome", "Reach"]},
        {"name": "Gnome Hooked Hammer", "dice": "1d6", "type": "Bludgeoning", "traits": ["Gnome", "Trip", "Two-Hand d10", "Versatile P"]},
    ],
    "orc": [
        {"name": "Orc Knuckle Dagger", "dice": "1d6", "type": "Piercing", "traits": ["Agile", "Finesse", "Orc"]},
        {"name": "Orc Necksplitter", "dice": "1d8", "type": "Slashing", "traits": ["Forceful", "Orc", "Sweep"]},
    ],
    "halfling": [
        {"name": "Halfling Sling Staff", "dice": "1d10", "type": "Bludgeoning", "traits": ["Halfling", "Propulsive", "Range 80 ft", "Reload 1"]},
        {"name": "Filcher's Fork", "dice": "1d4", "type": "Piercing", "traits": ["Agile", "Backstabber", "Deadly d6", "Finesse", "Halfling", "Thrown 20 ft"]},
    ],
    "kobold": [
        {"name": "Fangwire", "dice": "1d4", "type": "Slashing", "traits": ["Agile", "Deadly d8", "Finesse", "Grapple", "Kobold"]},
    ]
}

COMBINATION_FIREARMS = [
    {"name": "Triggerbrand", "dice": "1d6", "type": "Piercing", "traits": ["Combination", "Concussive", "Fatal d8", "Range 30 ft", "Reload 1"]},
    {"name": "Gun Sword", "dice": "1d8", "type": "Piercing", "traits": ["Combination", "Concussive", "Fatal d10", "Range 30 ft", "Reload 1"]},
    {"name": "Dagger Pistol", "dice": "1d4", "type": "Piercing", "traits": ["Agile", "Combination", "Concussive", "Fatal d8", "Finesse", "Range 30 ft", "Reload 1"]},
]

# ============================================================================
# WEAPON PROFICIENCY & CLASS SELECTION GATING
# ============================================================================
ROGUE_MARTIAL_WEAPONS = {"rapier", "sap", "shortbow", "shortsword", "hand crossbow"}
BARD_MARTIAL_WEAPONS = {"rapier", "sap", "shortbow", "shortsword", "whip"}

def select_class_weapons(
    cls_key: str,
    str_mod: int,
    dex_mod: int,
    ancestry_name: str = "",
    subclass_name: str = "",
    archetype_name: str = "",
    feats: Optional[List[Any]] = None,
) -> List[Dict[str, Any]]:
    """Select appropriate primary and backup weapons based on class proficiencies, ancestry, and attributes."""
    
    # 1. Determine Allowed Categories & Base Pools
    is_full_martial = cls_key in {
        "barbarian", "champion", "fighter", "ranger", "inventor",
        "guardian", "commander", "magus", "exemplar", "runesmith"
    }

    simple_pool = list(SIMPLE_MELEE + SIMPLE_RANGED)
    martial_pool = list(MARTIAL_ONE_HANDED + MARTIAL_TWO_HANDED + MARTIAL_FINESSE + MARTIAL_RANGED)

    # 2. Integrate Ancestral Weapons
    anc_key = (ancestry_name or "").strip().lower()
    ancestral_pool = list(ANCESTRAL_WEAPONS.get(anc_key, []))

    feat_str = " ".join(
        (f.get("name") if isinstance(f, dict) else getattr(f, "name", str(f))).lower()
        for f in (feats or [])
    )
    sub_lower = (subclass_name or "").lower()
    arch_lower = (archetype_name or "").lower()

    eligible_primary: List[Dict[str, Any]] = []
    eligible_secondary: List[Dict[str, Any]] = []
    ranged_martial_pool = list(MARTIAL_RANGED + SIMPLE_RANGED)

    # 3. Filter by Class & Subclass Weapon Proficiency / Combat Style
    if cls_key == "magus" and "laughing shadow" in sub_lower:
        # Laughing Shadow requires a free hand and thrives with 1H Finesse weapons
        eligible_primary = list(MARTIAL_FINESSE)
        eligible_secondary = [w for w in SIMPLE_RANGED if w["name"].lower() in ("dart", "javelin", "sling")]
    elif cls_key == "magus" and "starlit span" in sub_lower:
        eligible_primary = list(MARTIAL_RANGED)
        eligible_secondary = list(MARTIAL_FINESSE) if dex_mod >= str_mod else list(MARTIAL_ONE_HANDED)
    elif cls_key == "ranger":
        finesse_melee = [
            w for w in (MARTIAL_FINESSE + SIMPLE_MELEE)
            if any(t in [tr.lower() for tr in w.get("traits", [])] for t in ["finesse", "agile"])
        ]
        if dex_mod > str_mod:
            eligible_primary = list(MARTIAL_RANGED) if MARTIAL_RANGED else ranged_martial_pool
            eligible_secondary = finesse_melee if finesse_melee else list(SIMPLE_MELEE)
        else:
            eligible_primary = [w for w in (martial_pool + simple_pool) if w not in ranged_martial_pool]
            eligible_secondary = list(MARTIAL_RANGED) if MARTIAL_RANGED else ranged_martial_pool
    elif is_full_martial:
        eligible_primary = list(martial_pool)
        if ancestral_pool and ("weapon familiarity" in feat_str or random.random() < 0.35):
            eligible_primary.extend(ancestral_pool)
        eligible_secondary = list(MARTIAL_RANGED + SECONDARY_BACKUPS)
    elif cls_key == "gunslinger":
        firearms = ONE_HANDED_FIREARMS + TWO_HANDED_SNIPER_FIREARMS + VANGUARD_FIREARMS
        eligible_primary = list(firearms) if firearms else martial_pool
        eligible_secondary = list(SECONDARY_BACKUPS + simple_pool)
    elif cls_key == "thaumaturge":
        # 1-handed weapons only to keep a hand free for implements
        thaum_pool = [w for w in (MARTIAL_ONE_HANDED + MARTIAL_FINESSE + SIMPLE_MELEE) if w.get("hands", 1) == 1]
        eligible_primary = thaum_pool if thaum_pool else simple_pool
        eligible_secondary = [w for w in (SIMPLE_RANGED + SECONDARY_BACKUPS) if w.get("hands", 1) == 1]
    elif cls_key == "swashbuckler":
        eligible_primary = [
            w for w in MARTIAL_FINESSE
            if any(t in [tr.lower() for tr in w.get("traits", [])] for t in ["finesse", "agile"])
        ]
        eligible_secondary = [
            w for w in (simple_pool + SECONDARY_BACKUPS)
            if any(t in [tr.lower() for tr in w.get("traits", [])] for t in ["finesse", "agile", "thrown"]) or w.get("hands", 1) == 1
        ]
    elif cls_key == "rogue":
        eligible_primary = [
            w for w in (MARTIAL_FINESSE + SIMPLE_MELEE)
            if w["name"].lower() in ROGUE_MARTIAL_WEAPONS or any(t in [tr.lower() for tr in w.get("traits", [])] for t in ["finesse", "agile"])
        ]
        eligible_secondary = [
            w for w in (MARTIAL_RANGED + simple_pool)
            if w.get("name", "").lower() in ["shortbow", "composite shortbow", "hand crossbow", "dagger", "dart", "sling"]
        ]
    elif cls_key == "monk":
        monk_traits = {"monk", "agile", "finesse"}
        monk_pool = [w for w in (simple_pool + martial_pool) if any(t.lower() in monk_traits for t in w.get("traits", []))]
        eligible_primary = monk_pool if monk_pool else simple_pool
        eligible_secondary = simple_pool
    elif cls_key == "bard":
        eligible_primary = [
            w for w in (simple_pool + martial_pool)
            if w["name"].lower() in BARD_MARTIAL_WEAPONS or w in SIMPLE_MELEE
        ]
        eligible_secondary = [w for w in (MARTIAL_RANGED + simple_pool) if w["name"].lower() in ["shortbow", "sling", "hand crossbow", "whip"]]
    elif cls_key == "cleric":
        eligible_primary = list(SIMPLE_MELEE)
        eligible_secondary = [w for w in simple_pool if w in SIMPLE_RANGED or w.get("hands", 1) == 1]
    elif cls_key == "druid":
        druid_melee = [w for w in SIMPLE_MELEE if w["name"].lower() in ["spear", "sickle", "club", "longspear", "hatchet"]]
        eligible_primary = druid_melee if druid_melee else list(SIMPLE_MELEE)
        eligible_secondary = [w for w in SIMPLE_RANGED if w["name"].lower() in ["sling", "dart", "javelin"]]
    else:
        # Dedicated Casters (Wizard, Witch, Sorcerer, Oracle, Psychic, Necromancer, Summoner, Animist)
        caster_melee = [w for w in SIMPLE_MELEE if w["name"].lower() in ["club", "sickle", "spear"]] + [
            w for w in SECONDARY_BACKUPS if w["name"].lower() == "dagger"
        ]
        caster_ranged = [w for w in SIMPLE_RANGED if w["name"].lower() in ["crossbow", "sling", "dart"]]
        eligible_primary = caster_melee if caster_melee else simple_pool
        eligible_secondary = caster_ranged if caster_ranged else simple_pool

    # 4. Ability Score & Archetype Priority Filtering
    if "archer" in arch_lower and MARTIAL_RANGED:
        eligible_primary = list(MARTIAL_RANGED)
    elif dex_mod > str_mod and cls_key not in ("ranger", "gunslinger"):
        finesse_or_ranged = [
            w for w in eligible_primary
            if w in ranged_martial_pool or any(t in [tr.lower() for tr in w.get("traits", [])] for t in ["finesse", "agile", "ranged"])
        ]
        if finesse_or_ranged:
            eligible_primary = finesse_or_ranged
    elif str_mod >= dex_mod and is_full_martial and cls_key not in ("ranger", "gunslinger"):
        # STR martials favor heavy 2H or sturdy 1H martial melee over light finesse weapons
        str_melee = [
            w for w in eligible_primary
            if w not in ranged_martial_pool and "Finesse" not in w.get("traits", [])
        ]
        if str_melee:
            eligible_primary = str_melee

    if str_mod < 1:
        no_heavy = [w for w in eligible_primary if str(w.get("bulk", "1")) not in ["2", "3"]]
        if no_heavy:
            eligible_primary = no_heavy

    if not eligible_primary:
        eligible_primary = list(SIMPLE_MELEE)
    if not eligible_secondary:
        eligible_secondary = list(SIMPLE_RANGED)

    dual_wield_triggers = (
        "twin takedown", "second sting", "impossible flurry", "twin parry",
        "twin riposte", "double slice", "two-weapon flurry", "twin feint", "dual-weapon"
    )
    is_dual_wielder = any(t in feat_str for t in dual_wield_triggers)

    if is_dual_wielder and cls_key in {
        "ranger", "fighter", "rogue", "barbarian", "swashbuckler", "champion", "guardian", "commander", "exemplar"
    }:
        two_hand_names = {w["name"].lower() for w in MARTIAL_TWO_HANDED} | {"longspear", "elven curve blade", "elven branched spear"}
        one_hand_melee = [
            w for w in (MARTIAL_ONE_HANDED + MARTIAL_FINESSE + SIMPLE_MELEE)
            if w.get("hands", 1) == 1 and w["name"].lower() not in two_hand_names
        ]
        if dex_mod > str_mod:
            finesse_1h = [
                w for w in one_hand_melee
                if any(t in [tr.lower() for tr in w.get("traits", [])] for t in ["finesse", "agile"])
            ]
            if finesse_1h:
                one_hand_melee = finesse_1h
        agile_1h = [
            w for w in one_hand_melee
            if any(t in [tr.lower() for tr in w.get("traits", [])] for t in ["agile", "finesse"])
        ]
        main_hand = random.choice(one_hand_melee) if one_hand_melee else random.choice(SIMPLE_MELEE)
        off_pool = [w for w in (agile_1h or one_hand_melee) if w.get("name") != main_hand.get("name")]
        off_hand = random.choice(off_pool) if off_pool else dict(main_hand)
        ranged_pool = list(MARTIAL_RANGED) if (is_full_martial and MARTIAL_RANGED) else list(SIMPLE_RANGED)
        ranged_backup = random.choice(ranged_pool)
        return [main_hand, off_hand, ranged_backup]

    primary_wep = random.choice(eligible_primary)
    # Keep secondary backup distinct (prefer ranged backup if primary is melee, or 1H melee if primary is ranged)
    primary_is_ranged = "Range" in " ".join(primary_wep.get("traits", []))
    if primary_is_ranged:
        melee_backups = [w for w in eligible_secondary if "Range" not in " ".join(w.get("traits", [])) and w.get("name") != primary_wep.get("name")]
        backup_candidates = melee_backups or [w for w in eligible_secondary if w.get("name") != primary_wep.get("name")]
    else:
        ranged_backups = [w for w in eligible_secondary if "Range" in " ".join(w.get("traits", [])) and w.get("name") != primary_wep.get("name")]
        backup_candidates = ranged_backups or [w for w in eligible_secondary if w.get("name") != primary_wep.get("name")]

    secondary_wep = random.choice(backup_candidates) if backup_candidates else random.choice(eligible_secondary)
    return [primary_wep, secondary_wep]


def _should_equip_shield(
    cls_key: str,
    raw_weps: List[Dict[str, Any]],
    subclass_name: str = "",
    archetype_name: str = "",
    feats: Optional[List[Any]] = None,
) -> bool:
    """Determine if a shield fits the character's hand economy, class, and build."""
    feat_str = " ".join(
        (f.get("name") if isinstance(f, dict) else getattr(f, "name", str(f))).lower()
        for f in (feats or [])
    )
    sub_lower = (subclass_name or "").lower()
    arch_lower = (archetype_name or "").lower()

    # Explicit shield builds always get a shield if hands allow
    explicit_shield_build = (
        "shield block" in feat_str
        or "bastion" in arch_lower
        or "viking" in arch_lower
        or "everstand" in feat_str
        or "reactive shield" in feat_str
    )

    # Free-hand classes/subclasses never equip a shield unless explicitly a shield build
    if cls_key in ("thaumaturge", "monk", "gunslinger"):
        return False
    if cls_key == "magus" and ("laughing shadow" in sub_lower or "starlit span" in sub_lower):
        return False

    # Check if primary weapon occupies both hands or is a bow/crossbow/firearm
    two_hand_names = (
        {w["name"].lower() for w in MARTIAL_TWO_HANDED}
        | {w["name"].lower() for w in TWO_HANDED_SNIPER_FIREARMS}
        | {w["name"].lower() for w in VANGUARD_FIREARMS}
        | {"longspear", "elven curve blade", "elven branched spear", "halfling sling staff", "crossbow"}
    )
    if raw_weps:
        p_wep = raw_weps[0]
        p_name = p_wep.get("name", "").lower()
        p_traits = " ".join(p_wep.get("traits", [])).lower()
        if (
            p_name in two_hand_names
            or "bow" in p_name
            or "crossbow" in p_name
            or "range " in p_traits
            or p_wep.get("hands", 1) == 2
        ):
            return False

    # Dual-wielders (2 melee weapons in raw_weps) have both hands full
    melee_count = sum(1 for w in raw_weps if "Range" not in " ".join(w.get("traits", [])))
    if melee_count >= 2:
        return False

    if explicit_shield_build:
        return True

    # Dedicated shield/frontline classes get a shield ~65% of the time when holding a 1H melee weapon
    if cls_key in ("champion", "guardian", "fighter", "commander", "exemplar"):
        return random.random() < 0.65
    if cls_key == "cleric" and "cloistered" not in sub_lower:
        return random.random() < 0.65
    # Other 1H-capable martials/hybrids (barbarian, runesmith, druid, magus, ranger, swashbuckler) only occasionally (~25%)
    if cls_key in ("barbarian", "runesmith", "druid", "magus", "ranger", "swashbuckler", "inventor"):
        return random.random() < 0.25

    # Pure casters (wizard, witch, sorcerer, oracle, psychic, necromancer, summoner, animist, bard, rogue, alchemist, investigator)
    return False


def get_all_registered_weapons() -> List[Dict[str, Any]]:
    pool = []
    pool_lists = [
        MARTIAL_TWO_HANDED, MARTIAL_ONE_HANDED, MARTIAL_FINESSE, MARTIAL_RANGED,
        SIMPLE_MELEE, SIMPLE_RANGED, ONE_HANDED_FIREARMS, TWO_HANDED_SNIPER_FIREARMS,
        VANGUARD_FIREARMS, SECONDARY_BACKUPS
    ]
    for lst in pool_lists:
        pool.extend(lst)
    for anc_list in ANCESTRAL_WEAPONS.values():
        pool.extend(anc_list)
    return pool

def find_base_weapon(name: str) -> Optional[Dict[str, Any]]:
    clean = re.sub(r"^\+\d+\s+", "", name).strip()
    clean = re.sub(r"\bstriking\b", "", clean, flags=re.IGNORECASE).strip()
    clean = re.sub(r"\s+", " ", clean).strip().lower()
    all_w = get_all_registered_weapons()
    for w in all_w:
        if w["name"].lower() == clean:
            return dict(w)
    for w in all_w:
        if w["name"].lower() in clean or clean in w["name"].lower():
            return dict(w)
    return None


LEVEL2_WEAPON_COSTS_GP = {
    "longbow": 6.0,
    "composite longbow": 20.0,
    "shortbow": 3.0,
    "composite shortbow": 14.0,
    "glaive": 2.0,
    "scimitar": 1.0,
    "longsword": 1.0,
    "greatsword": 2.0,
    "rapier": 2.0,
    "dagger": 0.2,
    "spear": 0.1,
}

def _estimate_weapon_gp(w: Dict[str, Any]) -> float:
    for k in ("cost_gp", "price_gp"):
        if k in w and w[k] is not None:
            try:
                return float(w[k])
            except (TypeError, ValueError):
                pass
    w_low = str(w.get("name", "")).strip().lower()
    if w_low in LEVEL2_WEAPON_COSTS_GP:
        return LEVEL2_WEAPON_COSTS_GP[w_low]
    for k, v in LEVEL2_WEAPON_COSTS_GP.items():
        if k in w_low:
            return v
    return 2.0

def resolve_equipment(
    class_name: str,
    str_mod: int,
    dex_mod: int,
    level: int = 1,
    ancestry_name: str = "",
    heritage_name: str = "",
    subclass_name: str = "",
    archetype_name: str = "",
    existing_weapons: Optional[List[Any]] = None,
    feats: Optional[List[Any]] = None,
    requested_weapons: Optional[List[str]] = None,
    strict_only_weapon: bool = False,
    wants_shield: Optional[bool] = None,
    shield_kind: Optional[str] = None,
    requested_armor: Optional[str] = None,
) -> Tuple[EquipmentLoadout, int, int]:
    cls_key = class_name.lower()
    lvl = max(1, min(20, int(level)))
    wealth_cfg = WEALTH_BY_LEVEL.get(lvl, WEALTH_BY_LEVEL[1])
    tiers = get_fundamental_rune_tiers(lvl)
    attrs_map = {"str": str_mod, "dex": dex_mod}

    martial_capable = {
        "alchemist", "animist", "barbarian", "bard", "champion", "commander",
        "exemplar", "fighter", "gunslinger", "inventor", "investigator",
        "kineticist", "magus", "monk", "ranger", "rogue", "runesmith",
        "summoner", "swashbuckler", "thaumaturge", "vindicator",
    }
    arch_low = (archetype_name or "").lower()
    has_martial_prof = cls_key in martial_capable or any(
        m in arch_low for m in ("fighter", "ranger", "barbarian", "champion", "monk", "rogue", "swashbuckler", "gunslinger", "archer", "mauler")
    )

    raw_weps = []
    if requested_weapons:
        martial_set = {w["name"].lower() for w in (MARTIAL_TWO_HANDED + MARTIAL_ONE_HANDED + MARTIAL_FINESSE + MARTIAL_RANGED)}
        for rw_name in requested_weapons:
            base_w = find_base_weapon(rw_name)
            if not base_w:
                continue
            if base_w["name"].lower() in martial_set and not has_martial_prof:
                continue
            if base_w not in raw_weps:
                raw_weps.append(base_w)
        if raw_weps and not strict_only_weapon and len(raw_weps) == 1:
            p_traits = " ".join(raw_weps[0].get("traits", []))
            if "Range" not in p_traits and "bow" not in raw_weps[0]["name"].lower() and "crossbow" not in raw_weps[0]["name"].lower():
                backup_name = "Shortbow" if has_martial_prof else "Crossbow"
                backup_w = find_base_weapon(backup_name)
                if backup_w and backup_w not in raw_weps:
                    raw_weps.append(backup_w)

    if not raw_weps and existing_weapons:
        for ew in existing_weapons:
            w_name = ew.get("name") if isinstance(ew, dict) else getattr(ew, "name", "")
            base_w = find_base_weapon(w_name)
            if base_w and base_w not in raw_weps:
                raw_weps.append(base_w)
    if not raw_weps:
        raw_weps = select_class_weapons(
            cls_key,
            str_mod,
            dex_mod,
            ancestry_name=ancestry_name,
            subclass_name=subclass_name,
            archetype_name=archetype_name,
            feats=feats,
        )

    # Enforce Level 1-2 weapon wealth budget unless explicit weapons were requested
    if lvl <= 2 and not requested_weapons:
        max_gp = float(wealth_cfg.get("lump_gp", 15 if lvl == 1 else 30))
        spent_gp = 0.0
        affordable_weps = []
        for w in raw_weps:
            w_cost_gp = _estimate_weapon_gp(w)
            if spent_gp + w_cost_gp <= max_gp or not affordable_weps:
                affordable_weps.append(w)
                spent_gp += w_cost_gp
        if len(affordable_weps) > 2:
            affordable_weps = affordable_weps[:2]
        raw_weps = affordable_weps

    weapons: List[Item] = []
    strikes: List[Strike] = []

    for w in raw_weps:
        w_name = format_runed_weapon_name(w["name"], lvl)
        weapons.append(Item(name=w_name, bulk="1", cost_sp=10))
        prop_runes, crit_note = _get_property_runes_and_crit_spec(w["name"], w.get("traits", []), lvl, cls_key)
        enriched_traits = list(w.get("traits", []))
        if prop_runes:
            enriched_traits.append("Runes: " + ", ".join(prop_runes))
        if crit_note:
            enriched_traits.append(crit_note)
        strikes.append(compute_strike(
            name=w["name"],
            base_dice=w["dice"],
            damage_type=w["type"],
            traits=enriched_traits,
            level=lvl,
            class_name=class_name,
            attrs=attrs_map,
            is_unarmed=False,
            weapon_entry=w,
        ))

    # Broad structural rule: inspect ancestry, heritage, and feat names/descriptions for natural/unarmed strike definitions
    feat_entries = []
    for f in (feats or []):
        if isinstance(f, dict):
            f_name = str(f.get("name", "") or "")
            f_desc = str(f.get("description", "") or "")
        else:
            f_name = str(getattr(f, "name", "") or "")
            f_desc = str(getattr(f, "description", "") or "")
        feat_entries.append((f_name, f_desc))

    anc_her_text = f"{ancestry_name or ''} {heritage_name or ''}".lower()
    all_feat_text = " ".join(f"{n} {d}" for n, d in feat_entries).lower()

    attack_grant_snippets = []
    for n, d in feat_entries:
        combined = f"{n} {d}".lower()
        if re.search(
            r"\b(?:unarmed\s+(?:attack|strike)|natural\s+(?:weapon|attack|strike)|gain\s+(?:an?\s+)?[a-z0-9\s\-]{0,35}?(?:unarmed\s+)?(?:attack|strike))\b",
            combined,
        ):
            attack_grant_snippets.append(combined)

    ancestry_search_blob = f"{anc_her_text} {all_feat_text} {' '.join(attack_grant_snippets)}".strip()
    strike_source_text = f"{anc_her_text} {' '.join(attack_grant_snippets)}"
    for tok in ("horn", "hoof", "hooves", "fang", "jaw", "claw", "pincer", "talon", "tail", "venom", "poison", "spine", "quill", "thorn", "fist"):
        if re.search(r"\b" + tok + r"s?\b", strike_source_text) and tok not in ancestry_search_blob:
            ancestry_search_blob += f" {tok}"

    ancestry_strikes_to_add: List[Strike] = []
    if re.search(r"\b(?:automaton|armament|pincer)\b", ancestry_search_blob):
        if re.search(r"\bpincers?\b", ancestry_search_blob):
            ancestry_strikes_to_add.append(compute_strike(
                name="Pincer (Automaton Armament)",
                base_dice="1d6",
                damage_type="Piercing",
                traits=["brawling", "grapple", "unarmed"],
                level=lvl,
                class_name=class_name,
                attrs=attrs_map,
                is_unarmed=True,
            ))
        elif re.search(r"\b(?:automaton|armament|claws?)\b", ancestry_search_blob):
            ancestry_strikes_to_add.append(compute_strike(
                name="Claw (Automaton Armament)",
                base_dice="1d4",
                damage_type="Slashing",
                traits=["agile", "finesse", "unarmed", "brawling"],
                level=lvl,
                class_name=class_name,
                attrs=attrs_map,
                is_unarmed=True,
            ))

    stance_attack_specs = [
        (("gorilla stance", "gorilla slam"), "Gorilla Slam", "1d8", "Bludgeoning", ["backswing", "grappling", "nonlethal", "unarmed"]),
        (("dragon stance", "dragon tail"), "Dragon Tail", "1d10", "Bludgeoning", ["backswing", "nonlethal", "unarmed"]),
        (("tiger stance", "tiger claw"), "Tiger Claw", "1d8", "Slashing", ["agile", "finesse", "nonlethal", "unarmed"]),
        (("wolf stance", "wolf jaws"), "Wolf Jaws", "1d8", "Piercing", ["agile", "backstabber", "finesse", "nonlethal", "unarmed"]),
    ]
    for tokens, st_name, st_dice, st_type, st_traits in stance_attack_specs:
        if any(tok in ancestry_search_blob for tok in tokens) and not any(st_name.lower() in s.name.lower() for s in ancestry_strikes_to_add):
            ancestry_strikes_to_add.append(compute_strike(
                name=st_name,
                base_dice=st_dice,
                damage_type=st_type,
                traits=st_traits,
                level=lvl,
                class_name=class_name,
                attrs=attrs_map,
                is_unarmed=True,
            ))

    natural_attack_specs = [
        (("horn", "horns", "gore"), "Horn", "1d6", "Piercing", ["unarmed"]),
        (("hoof", "hooves"), "Hoof", "1d6", "Bludgeoning", ["unarmed"]),
        (("fang", "fangs", "bite"), "Fangs", "1d6", "Piercing", ["finesse", "unarmed"]),
        (("jaw", "jaws"), "Jaws", "1d6", "Piercing", ["unarmed"]),
        (("claw", "claws"), "Claw", "1d4", "Slashing", ["agile", "finesse", "unarmed"]),
        (("talon", "talons"), "Talons", "1d4", "Slashing", ["agile", "finesse", "unarmed"]),
        (("tail",), "Tail", "1d4", "Bludgeoning", ["agile", "finesse", "unarmed"]),
        (("venom", "poison"), "Venomous Strike", "1d4", "Poison", ["unarmed", "poison"]),
        (("spine", "spines", "quill", "quills"), "Spines", "1d4", "Piercing", ["unarmed"]),
        (("thorn", "thorns"), "Thorn", "1d6", "Piercing", ["finesse", "unarmed"]),
        (("iron fists",), "Fist", "1d4", "Bludgeoning", ["agile", "finesse", "shove", "unarmed"]),
        (("fist", "fists"), "Fist", "1d4", "Bludgeoning", ["agile", "finesse", "nonlethal", "unarmed"]),
    ]
    for tokens, nat_name, nat_dice, nat_type, nat_traits in natural_attack_specs:
        if any(re.search(r"\b" + re.escape(tok) + r"\b", ancestry_search_blob) for tok in tokens):
            n_low = nat_name.lower()
            already_present = any(
                n_low in s.name.lower() or s.name.lower() in n_low
                for s in (strikes + ancestry_strikes_to_add)
            )
            if not already_present:
                ancestry_strikes_to_add.append(compute_strike(
                    name=nat_name,
                    base_dice=nat_dice,
                    damage_type=nat_type,
                    traits=[t.title() for t in nat_traits],
                    level=lvl,
                    class_name=class_name,
                    attrs=attrs_map,
                    is_unarmed=True,
                ))

    for ast in ancestry_strikes_to_add:
        if not any(ast.name.lower() in s.name.lower() for s in strikes):
            strikes.append(ast)

    if cls_key == "alchemist":
        bomb_tier = "greater" if lvl >= 11 else ("moderate" if lvl >= 3 else "lesser")
        tier_list = ALCHEMICAL_BOMBS.get(bomb_tier, ALCHEMICAL_BOMBS["moderate"])
        strikes.insert(0, compute_alchemical_bomb_strike(tier_list[0], lvl, class_name, attrs_map))

    shield_bonus = 0
    shield_item = None
    armor_pot = tiers["armor_potency"]
    is_cloistered = cls_key == "cleric" and "cloistered" in (subclass_name or "").lower()
    if wants_shield is False:
        use_shield = False
    elif wants_shield is True:
        # Still forbid shields if primary weapon is two-handed
        two_hand_names = (
            {w["name"].lower() for w in MARTIAL_TWO_HANDED}
            | {w["name"].lower() for w in TWO_HANDED_SNIPER_FIREARMS}
            | {w["name"].lower() for w in VANGUARD_FIREARMS}
            | {"longspear", "elven curve blade", "elven branched spear", "halfling sling staff", "crossbow"}
        )
        p_name = raw_weps[0].get("name", "").lower() if raw_weps else ""
        use_shield = p_name not in two_hand_names and "bow" not in p_name and "crossbow" not in p_name
    else:
        use_shield = _should_equip_shield(
            cls_key=cls_key,
            raw_weps=raw_weps,
            subclass_name=subclass_name,
            archetype_name=archetype_name,
            feats=feats,
        )

    # Check explicit armor request (within class/archetype armor proficiency rules)
    explicit_armor_spec = None
    if requested_armor:
        armor_catalog = {
            "full plate": ("Full Plate", "heavy", 6, 0, "3"),
            "half plate": ("Half Plate", "heavy", 5, 1, "3"),
            "splint mail": ("Splint Mail", "heavy", 5, 1, "3"),
            "breastplate": ("Breastplate", "medium", 4, 1, "2"),
            "chain mail": ("Chain Mail", "medium", 4, 1, "2"),
            "scale mail": ("Scale Mail", "medium", 3, 2, "2"),
            "hide armor": ("Hide Armor", "medium", 3, 2, "2"),
            "studded leather armor": ("Studded Leather Armor", "light", 2, 3, "1"),
            "leather armor": ("Leather Armor", "light", 1, 4, "1"),
            "padded armor": ("Padded Armor", "light", 1, 3, "1"),
            "explorer's clothing": ("Explorer's Clothing", "unarmored", 0, 5, "L"),
        }
        cand = armor_catalog.get(requested_armor.strip().lower())
        if cand:
            heavy_classes = {"champion", "fighter", "guardian"}
            medium_classes = heavy_classes | {"barbarian", "cleric", "druid", "inventor", "magus", "ranger", "thaumaturge", "vindicator", "commander"}
            light_classes = medium_classes | {"alchemist", "animist", "bard", "gunslinger", "investigator", "kineticist", "oracle", "rogue", "summoner", "swashbuckler"}
            has_heavy = cls_key in heavy_classes or "sentinel" in arch_low
            has_medium = has_heavy or cls_key in medium_classes or any(a in arch_low for a in ("champion", "fighter", "guardian"))
            has_light = has_medium or cls_key in light_classes
            acat = cand[1]
            if (acat == "heavy" and has_heavy) or (acat == "medium" and has_medium) or (acat == "light" and has_light) or acat == "unarmored":
                explicit_armor_spec = cand

    if explicit_armor_spec:
        aname, acat, item_ac, dex_cap, abulk = explicit_armor_spec
        armor_name = format_runed_armor_name(aname, lvl)
        armor_item = Item(name=armor_name, bulk=abulk, cost_sp=50)
        if cls_key == "monk" and acat == "unarmored":
            arm_prof = (8 + lvl) if lvl >= 17 else ((6 + lvl) if lvl >= 13 else (4 + lvl))
        elif cls_key == "thaumaturge" and lvl >= 11:
            arm_prof = 4 + lvl
        else:
            arm_prof = 2 + lvl
        calculated_ac = 10 + item_ac + min(dex_mod, dex_cap) + arm_prof + armor_pot
        if use_shield:
            sh_base = shield_kind or "Steel Shield"
            shield_bonus = 1 if "buckler" in sh_base.lower() else 2
            shield_item = Item(name=format_scaled_shield_name(sh_base, lvl), bulk="L" if shield_bonus == 1 else "1", cost_sp=20)
    elif is_cloistered:
        armor_name = format_runed_armor_name("Explorer's Clothing", lvl)
        armor_item = Item(name=armor_name, bulk="L", cost_sp=1)
        calculated_ac = 10 + 0 + min(dex_mod, 5) + (2 + lvl) + armor_pot
    elif cls_key in ["champion", "fighter", "cleric", "guardian"]:
        armor_name = format_runed_armor_name("Breastplate", lvl)
        armor_item = Item(name=armor_name, bulk="2", cost_sp=80)
        calculated_ac = 10 + 4 + min(dex_mod, 1) + (2 + lvl) + armor_pot
        if use_shield:
            sh_base = shield_kind or "Steel Shield"
            shield_bonus = 1 if "buckler" in sh_base.lower() else 2
            shield_item = Item(name=format_scaled_shield_name(sh_base, lvl), bulk="L" if shield_bonus == 1 else "1", cost_sp=20)
    elif cls_key in ["rogue", "ranger", "bard", "swashbuckler", "investigator", "gunslinger", "alchemist", "animist"]:
        armor_name = format_runed_armor_name("Leather Armor", lvl)
        armor_item = Item(name=armor_name, bulk="1", cost_sp=20)
        calculated_ac = 10 + 1 + min(dex_mod, 4) + (2 + lvl) + armor_pot
        if use_shield:
            sh_base = shield_kind or "Wooden Shield"
            shield_bonus = 1 if "buckler" in sh_base.lower() else 2
            shield_item = Item(name=format_scaled_shield_name(sh_base, lvl), bulk="L" if shield_bonus == 1 else "1", cost_sp=10)
    elif cls_key in ["wizard", "witch", "sorcerer", "oracle", "psychic", "necromancer", "monk"]:
        armor_name = format_runed_armor_name("Explorer's Clothing", lvl)
        armor_item = Item(name=armor_name, bulk="L", cost_sp=1)
        if cls_key == "monk":
            unarm_prof = (8 + lvl) if lvl >= 17 else ((6 + lvl) if lvl >= 13 else (4 + lvl))
        else:
            unarm_prof = (2 + lvl)
        calculated_ac = 10 + 0 + min(dex_mod, 5) + unarm_prof + armor_pot
        if use_shield:
            sh_base = shield_kind or "Wooden Shield"
            shield_bonus = 1 if "buckler" in sh_base.lower() else 2
            shield_item = Item(name=format_scaled_shield_name(sh_base, lvl), bulk="L" if shield_bonus == 1 else "1", cost_sp=10)
    else:
        arm_prof = (4 + lvl) if (cls_key == "thaumaturge" and lvl >= 11) else (2 + lvl)
        if dex_mod >= 4:
            armor_name = format_runed_armor_name("Leather Armor", lvl)
            armor_item = Item(name=armor_name, bulk="1", cost_sp=20)
            calculated_ac = 10 + 1 + min(dex_mod, 4) + arm_prof + armor_pot
        elif dex_mod == 3:
            armor_name = format_runed_armor_name("Studded Leather Armor", lvl)
            armor_item = Item(name=armor_name, bulk="1", cost_sp=30)
            calculated_ac = 10 + 2 + min(dex_mod, 3) + arm_prof + armor_pot
        else:
            armor_name = format_runed_armor_name("Hide Armor", lvl)
            armor_item = Item(name=armor_name, bulk="2", cost_sp=20)
            calculated_ac = 10 + 3 + min(dex_mod, 2) + arm_prof + armor_pot
        if use_shield:
            sh_base = shield_kind or ("Steel Shield" if cls_key in ("commander", "exemplar", "barbarian") else "Wooden Shield")
            shield_bonus = 1 if "buckler" in sh_base.lower() else 2
            shield_item = Item(name=format_scaled_shield_name(sh_base, lvl), bulk="L" if shield_bonus == 1 else "1", cost_sp=10)

    if "hardshell" in (heritage_name or "").lower() and (ancestry_name or "").lower() in ("surki", "sukri"):
        armor_name = format_runed_armor_name("Hardshell Surki Carapace", lvl)
        armor_item = Item(name=armor_name, bulk="0", cost_sp=0)
        calculated_ac = 10 + 4 + min(dex_mod, 1) + (2 + lvl) + armor_pot

    gear: List[str] = ["Adventurer's Pack (Backpack, Bedroll, Rations, Torches, Waterskin, Rope)"]
    num_perm = wealth_cfg.get("permanent_count", 0)
    if num_perm > 0:
        eligible_items = []
        for l in range(1, min(lvl, max(COMPENDIUM_MAGIC_ITEMS.keys())) + 1):
            for item in COMPENDIUM_MAGIC_ITEMS.get(l, []):
                if can_equip_item(item, cls_key, str_mod, dex_mod, lvl):
                    eligible_items.append(item)
        if not eligible_items:
            eligible_items = [i for i in PERMANENT_MAGIC_ITEMS if i["level"] <= lvl and can_equip_item(i, cls_key, str_mod, dex_mod, lvl)]
        chosen_items = random.sample(eligible_items, min(num_perm, len(eligible_items)))
        for item in chosen_items:
            gear.append(f"{item['name']} ({item['description']})")

    consumables: List[ConsumableItem] = []

    # Robust ancestry natural attacks / weapons extraction
    ancestry_search_blob = " ".join([
        ancestry_name or "",
        heritage_name or "",
        " ".join((f.get("name") if isinstance(f, dict) else getattr(f, "name", str(f))) for f in (feats or []))
    ]).lower()

    base_anc_atk = 2 + lvl + max(str_mod, dex_mod)
    ancestry_strikes_to_add = []
    is_automaton_like = "automaton" in ancestry_search_blob or "armament" in ancestry_search_blob
    if is_automaton_like or "pincer" in ancestry_search_blob or "claw" in ancestry_search_blob or "natural attack" in ancestry_search_blob or "lizardfolk" in ancestry_search_blob or "iruxi" in ancestry_search_blob:
        if "pincer" in ancestry_search_blob:
            ancestry_strikes_to_add.append(Strike(
                name="Pincer (Automaton Armament)" if is_automaton_like else "Pincer",
                attack_bonus=base_anc_atk,
                map_second=base_anc_atk - 5,
                map_third=base_anc_atk - 10,
                damage_dice="1d6",
                damage_type="Piercing",
                traits=["brawling", "grapple", "unarmed"]
            ))
        else:
            ancestry_strikes_to_add.append(Strike(
                name="Claw (Automaton Armament)" if is_automaton_like else "Claw",
                attack_bonus=base_anc_atk,
                map_second=base_anc_atk - 4,
                map_third=base_anc_atk - 8,
                damage_dice="1d4",
                damage_type="Slashing",
                traits=["agile", "finesse", "unarmed", "brawling"]
            ))
    if "tengu" in ancestry_search_blob:
        ancestry_strikes_to_add.append(Strike(
            name="Beak",
            attack_bonus=base_anc_atk,
            map_second=base_anc_atk - 5,
            map_third=base_anc_atk - 10,
            damage_dice="1d6",
            damage_type="Piercing",
            traits=["finesse", "unarmed"]
        ))
    if "surki" in ancestry_search_blob or "razortooth" in ancestry_search_blob:
        ancestry_strikes_to_add.append(Strike(
            name="Natural Ancestry Attack",
            attack_bonus=base_anc_atk,
            map_second=base_anc_atk - 4,
            map_third=base_anc_atk - 8,
            damage_dice="1d4",
            damage_type="Slashing",
            traits=["agile", "finesse", "unarmed"]
        ))

    for ast in ancestry_strikes_to_add:
        if not any(ast.name.lower() in s.name.lower() for s in strikes):
            strikes.append(ast)

    if cls_key == "alchemist":
        bomb_tier = "greater" if lvl >= 11 else ("moderate" if lvl >= 3 else "lesser")
        tier_bombs = ALCHEMICAL_BOMBS.get(bomb_tier, ALCHEMICAL_BOMBS["moderate"])
        for idx, b_desc in enumerate([
            f"Deals {tier_bombs[0]['dice']} fire, {tier_bombs[0]['persistent']}, and {tier_bombs[0]['splash']}.",
            f"Deals {tier_bombs[1]['dice']} electricity, {tier_bombs[1]['splash']}, off-guard on hit.",
            f"Deals {tier_bombs[2]['dice']} acid, {tier_bombs[2]['persistent']}, and {tier_bombs[2]['splash']}.",
        ]):
            consumables.append(ConsumableItem(
                name=tier_bombs[idx]["name"],
                quantity=3 if (idx == 0 and lvl >= 4) else 2,
                bulk="L",
                description=b_desc,
            ))

    if lvl == 1:
        consumables.append(ConsumableItem(name="Minor Healing Potion", quantity=2, bulk="L", description="Restores 1d8 HP (1 Action)."))
    elif lvl in (2, 3):
        consumables.append(ConsumableItem(name="Lesser Healing Potion", quantity=2, bulk="L", description="Restores 2d8+5 HP (1 Action)."))
        consumables.append(ConsumableItem(name="Silversheen", quantity=1, bulk="L", description="Grants weapon silver property for 1 hour."))
    elif lvl in (4, 5):
        consumables.append(ConsumableItem(name="Lesser Healing Potion", quantity=3, bulk="L", description="Restores 2d8+5 HP (1 Action)."))
        consumables.append(ConsumableItem(name="Elixir of Life (Lesser)", quantity=1, bulk="L", description="Restores 3d6+6 HP and +1 bonus vs disease/poison."))
    elif lvl in (6, 7, 8, 9, 10, 11):
        consumables.append(ConsumableItem(name="Moderate Healing Potion", quantity=2, bulk="L", description="Restores 3d8+10 HP (1 Action)."))
        consumables.append(ConsumableItem(name="Elixir of Life (Moderate)", quantity=1, bulk="L", description="Restores 5d6+12 HP and +2 item bonus vs disease/poison."))
        consumables.append(ConsumableItem(name="Mistform Elixir (Moderate)", quantity=1, bulk="L", description="Gain concealment (DC 5 flat check) for 1 minute."))
    elif lvl in (12, 13, 14, 15, 16, 17):
        consumables.append(ConsumableItem(name="Greater Healing Potion", quantity=3, bulk="L", description="Restores 6d8+20 HP (1 Action)."))
        consumables.append(ConsumableItem(name="Elixir of Life (Greater)", quantity=2, bulk="L", description="Restores 7d6+18 HP and +3 item bonus vs disease/poison."))
        consumables.append(ConsumableItem(name="Mistform Elixir (Greater)", quantity=1, bulk="L", description="Gain concealment (DC 5 flat check) for 5 minutes."))
    else:
        consumables.append(ConsumableItem(name="Major Healing Potion", quantity=3, bulk="L", description="Restores 8d8+30 HP (1 Action)."))
        consumables.append(ConsumableItem(name="Elixir of Life (True)", quantity=2, bulk="L", description="Restores 10d6+27 HP and +4 item bonus vs disease/poison."))
        consumables.append(ConsumableItem(name="Truesight Potion", quantity=1, bulk="L", description="Grants truesight for 1 hour."))

    remaining_gp = max(5, int(wealth_cfg["lump_gp"] * 0.12))
    sp = random.randint(1, 9)
    cp = random.randint(1, 9)
    formatted_wealth = f"{remaining_gp} GP, {sp} SP, {cp} CP"
    wealth = Wealth(pp=0, gp=remaining_gp, sp=sp, cp=cp, formatted=formatted_wealth)

    loadout = EquipmentLoadout(
        weapons=weapons,
        armor=armor_item,
        shield=shield_item,
        gear=gear,
        consumables=consumables,
        money=wealth,
        strikes=strikes
    )

    return loadout, calculated_ac, shield_bonus
