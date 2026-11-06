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

# PF2e Remaster Character Wealth by Level (Lump sum alternative)
# Level: (lump_sum_gp, min_consumables, typical_permanent_items)
WEALTH_BY_LEVEL: Dict[int, Dict[str, Any]] = {
    1: {"lump_gp": 15, "consumable_tier": "minor", "permanent_count": 0},
    2: {"lump_gp": 30, "consumable_tier": "minor", "permanent_count": 0},
    3: {"lump_gp": 75, "consumable_tier": "lesser", "permanent_count": 1},
    4: {"lump_gp": 140, "consumable_tier": "lesser", "permanent_count": 2},
    5: {"lump_gp": 270, "consumable_tier": "moderate", "permanent_count": 3},
    6: {"lump_gp": 450, "consumable_tier": "moderate", "permanent_count": 4},
    7: {"lump_gp": 720, "consumable_tier": "moderate_plus", "permanent_count": 5},
}

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
    archetype_name: str = ""
) -> List[Dict[str, Any]]:
    """Select appropriate primary and backup weapons based on class proficiencies, ancestry, and attributes."""
    
    # 1. Determine Allowed Categories & Base Pools
    is_full_martial = cls_key in {
        "barbarian", "champion", "fighter", "ranger", "inventor", 
        "guardian", "commander", "magus"
    }
    
    simple_pool = list(SIMPLE_MELEE + SIMPLE_RANGED)
    martial_pool = list(MARTIAL_ONE_HANDED + MARTIAL_TWO_HANDED + MARTIAL_FINESSE + MARTIAL_RANGED)

    # 2. Integrate Ancestral Weapons
    anc_key = (ancestry_name or "").strip().title()
    anc_weapons = list(ANCESTRAL_WEAPONS.get(anc_key, []))

    eligible_primary: List[Dict[str, Any]] = []
    eligible_secondary: List[Dict[str, Any]] = []

    # 3. Filter by Class Weapon Proficiency
    if is_full_martial:
        eligible_primary = martial_pool + simple_pool + anc_weapons
        eligible_secondary = martial_pool + simple_pool + anc_weapons
    elif cls_key == "gunslinger":
        firearms = ONE_HANDED_FIREARMS + TWO_HANDED_SNIPER_FIREARMS + VANGUARD_FIREARMS
        eligible_primary = list(firearms) if firearms else martial_pool
        eligible_secondary = list(SECONDARY_BACKUPS + simple_pool)
    elif cls_key == "thaumaturge":
        # 1-handed weapons only to keep a hand free for implements
        thaum_pool = [w for w in (MARTIAL_ONE_HANDED + MARTIAL_FINESSE + SIMPLE_MELEE + anc_weapons) if w.get("hands", 1) == 1]
        eligible_primary = thaum_pool if thaum_pool else simple_pool
        eligible_secondary = [w for w in (SIMPLE_RANGED + SECONDARY_BACKUPS) if w.get("hands", 1) == 1]
    elif cls_key == "swashbuckler":
        eligible_primary = [
            w for w in (MARTIAL_FINESSE + anc_weapons) 
            if any(t in [tr.lower() for tr in w.get("traits", [])] for t in ["finesse", "agile"])
        ]
        eligible_secondary = [
            w for w in (simple_pool + SECONDARY_BACKUPS) 
            if any(t in [tr.lower() for tr in w.get("traits", [])] for t in ["finesse", "agile", "thrown"]) or w.get("hands", 1) == 1
        ]
    elif cls_key == "rogue":
        eligible_primary = [
            w for w in (martial_pool + simple_pool + anc_weapons)
            if w["name"].lower() in ROGUE_MARTIAL_WEAPONS or w in simple_pool or any(t in [tr.lower() for tr in w.get("traits", [])] for t in ["finesse", "agile"])
        ]
        eligible_secondary = [
            w for w in simple_pool 
            if w.get("name", "").lower() in ["shortbow", "hand crossbow", "dagger", "dart", "sling"]
        ]
    elif cls_key == "monk":
        monk_traits = {"monk", "agile", "finesse"}
        monk_pool = [w for w in (simple_pool + martial_pool + anc_weapons) if any(t.lower() in monk_traits for t in w.get("traits", []))]
        eligible_primary = monk_pool if monk_pool else simple_pool
        eligible_secondary = simple_pool
    elif cls_key == "bard":
        eligible_primary = [
            w for w in (simple_pool + martial_pool)
            if w["name"].lower() in BARD_MARTIAL_WEAPONS or w in simple_pool
        ]
        eligible_secondary = [w for w in simple_pool if w["name"].lower() in ["shortbow", "sling", "hand crossbow", "whip"]]
    elif cls_key == "cleric":
        eligible_primary = simple_pool
        eligible_secondary = [w for w in simple_pool if "ranged" in w.get("type", "").lower() or w.get("hands", 1) == 1]
    else:
        # Full Casters (Wizard, Witch, Sorcerer, Druid, Oracle, Psychic, Summoner, Animist)
        caster_melee = [w for w in SIMPLE_MELEE if w["name"].lower() in ["staff", "dagger", "club", "sickle"]]
        caster_ranged = [w for w in SIMPLE_RANGED if w["name"].lower() in ["light crossbow", "sling", "dart"]]
        eligible_primary = caster_melee if caster_melee else simple_pool
        eligible_secondary = caster_ranged if caster_ranged else simple_pool

    # 4. Ability Score Priority Filtering
    if dex_mod > str_mod and dex_mod >= 2:
        finesse_primary = [
            w for w in eligible_primary 
            if any(t in [tr.lower() for tr in w.get("traits", [])] for t in ["finesse", "agile", "ranged"])
        ]
        if finesse_primary:
            eligible_primary = finesse_primary

    if str_mod < 1:
        no_heavy = [w for w in eligible_primary if str(w.get("bulk", "1")) not in ["2", "3"]]
        if no_heavy:
            eligible_primary = no_heavy

    if not eligible_primary:
        eligible_primary = list(SIMPLE_MELEE)
    if not eligible_secondary:
        eligible_secondary = list(SIMPLE_RANGED)

    primary_wep = random.choice(eligible_primary)
    backup_candidates = [w for w in eligible_secondary if w.get("name") != primary_wep.get("name")]
    secondary_wep = random.choice(backup_candidates) if backup_candidates else random.choice(eligible_secondary)

    return [primary_wep, secondary_wep]
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

def resolve_equipment(
    class_name: str,
    str_mod: int,
    dex_mod: int,
    level: int = 1,
    ancestry_name: str = "",
    subclass_name: str = "",
    archetype_name: str = "",
    existing_weapons: Optional[List[Any]] = None
) -> Tuple[EquipmentLoadout, int, int]:
    cls_key = class_name.lower()
    lvl = max(1, min(7, level))
    wealth_cfg = WEALTH_BY_LEVEL.get(lvl, WEALTH_BY_LEVEL[1])

    budget_gp = wealth_cfg["lump_gp"]

    # 1. Base Weapon Selection & Rune Progression
    raw_weps = []
    if existing_weapons:
        for ew in existing_weapons:
            w_name = ew.get("name") if isinstance(ew, dict) else getattr(ew, "name", "")
            base_w = find_base_weapon(w_name)
            if base_w and base_w not in raw_weps:
                raw_weps.append(base_w)
    if not raw_weps:
        raw_weps = select_class_weapons(cls_key, str_mod, dex_mod, ancestry_name=ancestry_name, subclass_name=subclass_name, archetype_name=archetype_name)
    weapons: List[Item] = []
    strikes: List[Strike] = []

    has_potency = lvl >= 2
    has_striking = lvl >= 4
    has_armor_potency = lvl >= 5

    # Runes cost tracking
    if has_potency:
        budget_gp -= 35
    if has_striking:
        budget_gp -= 65
    if has_armor_potency:
        budget_gp -= 160

    potency_bonus = 1 if has_potency else 0
    dice_count = 2 if has_striking else 1

    for w in raw_weps:
        w_name = w["name"]
        if has_striking:
            w_name = f"+1 Striking {w['name']}"
        elif has_potency:
            w_name = f"+1 {w['name']}"

        weapons.append(Item(name=w_name, bulk="1", cost_sp=10))

        # Strike calculations
        is_finesse = "Finesse" in w.get("traits", [])
        is_ranged = "Range" in " ".join(w.get("traits", []))
        atk_stat = dex_mod if (is_finesse or is_ranged) else max(str_mod, dex_mod if is_finesse else -99)

        base_prof = 4 if cls_key == "fighter" else 2
        total_atk = base_prof + lvl + atk_stat + potency_bonus

        dice_str = f"{dice_count}{w['dice'][1:]}"
        dmg_str = f"{dice_str}+{str_mod}" if not is_ranged else dice_str

        is_agile = "Agile" in w.get("traits", [])
        strikes.append(Strike(
            name=w_name,
            attack_bonus=total_atk,
            map_second=total_atk - (4 if is_agile else 5),
            map_third=total_atk - (8 if is_agile else 10),
            damage_dice=dmg_str,
            damage_type=w["type"],
            traits=w.get("traits", [])
        ))

    # Add Signature Alchemist Bomb Strike
    if cls_key == "alchemist":
        bomb_tier = "moderate" if lvl >= 3 else "lesser"
        # Default to Alchemist's Fire
        chosen_bomb = ALCHEMICAL_BOMBS[bomb_tier][0]
        bomb_prof = 2  # Trained in simple weapons / alchemical bombs
        bomb_atk = bomb_prof + lvl + dex_mod + chosen_bomb["item_bonus"]
        dmg_desc = f"{chosen_bomb['dice']} + {chosen_bomb['persistent']} + {chosen_bomb['splash']}"
        strikes.insert(0, Strike(
            name=chosen_bomb["name"],
            attack_bonus=bomb_atk,
            map_second=bomb_atk - 5,
            map_third=bomb_atk - 10,
            damage_dice=dmg_desc,
            damage_type=chosen_bomb["type"],
            traits=chosen_bomb["traits"]
        ))

    # 2. Armor and Shield Selection
    shield_bonus = 0
    if cls_key in ["champion", "fighter", "cleric"]:
        armor_name = "+1 Breastplate" if has_armor_potency else "Breastplate"
        armor_item = Item(name=armor_name, bulk="2", cost_sp=80)
        calculated_ac = 10 + 4 + min(dex_mod, 1) + (2 + lvl) + (1 if has_armor_potency else 0)
        shield_item = Item(name="Steel Shield", bulk="1", cost_sp=20)
        shield_bonus = 2
    elif cls_key in ["rogue", "ranger", "bard"]:
        armor_name = "+1 Leather Armor" if has_armor_potency else "Leather Armor"
        armor_item = Item(name=armor_name, bulk="1", cost_sp=20)
        calculated_ac = 10 + 1 + min(dex_mod, 4) + (2 + lvl) + (1 if has_armor_potency else 0)
        shield_item = None
    elif cls_key in ["wizard", "witch", "sorcerer", "oracle", "psychic"]:
        armor_name = "+1 Explorer's Clothing" if has_armor_potency else "Explorer's Clothing"
        armor_item = Item(name=armor_name, bulk="L", cost_sp=1)
        calculated_ac = 10 + 0 + min(dex_mod, 5) + (2 + lvl) + (1 if has_armor_potency else 0)
        shield_item = None
    else:
        armor_name = "+1 Hide Armor" if has_armor_potency else "Hide Armor"
        armor_item = Item(name=armor_name, bulk="2", cost_sp=20)
        calculated_ac = 10 + 2 + min(dex_mod, 2) + (2 + lvl) + (1 if has_armor_potency else 0)
        shield_item = Item(name="Wooden Shield", bulk="1", cost_sp=10)
        shield_bonus = 2

    # 3. Permanent Magic Item Purchases
    gear: List[str] = ["Adventurer's Pack (Backpack, Bedroll, Rations, Torches, Waterskin, Rope)"]
    num_perm = wealth_cfg.get("permanent_count", 0)
    if num_perm > 0:
        eligible_items = []
        for l in range(1, lvl + 1):
            for item in COMPENDIUM_MAGIC_ITEMS.get(l, []):
                if can_equip_item(item, cls_key, str_mod, dex_mod, lvl):
                    eligible_items.append(item)
        if not eligible_items:
            eligible_items = [i for i in PERMANENT_MAGIC_ITEMS if i['level'] <= lvl and can_equip_item(i, cls_key, str_mod, dex_mod, lvl)]
        chosen_items = random.sample(eligible_items, min(num_perm, len(eligible_items)))
        for item in chosen_items:
            gear.append(f"{item['name']} ({item['description']})")
            budget_gp -= min(item["cost_gp"], budget_gp // 2)

    # 4. Consumables Scaling by Level
    consumables: List[ConsumableItem] = []

    if cls_key == "alchemist":
        bomb_tier = "moderate" if lvl >= 3 else "lesser"
        tier_bombs = ALCHEMICAL_BOMBS[bomb_tier]
        # Alchemist daily prepared bombs (Alchemist's Fire, Bottled Lightning, Acid Flask)
        consumables.append(ConsumableItem(
            name=tier_bombs[0]["name"],
            quantity=3 if lvl >= 4 else 2,
            bulk="L",
            description=f"Deals {tier_bombs[0]['dice']} fire, {tier_bombs[0]['persistent']}, and {tier_bombs[0]['splash']}."
        ))
        consumables.append(ConsumableItem(
            name=tier_bombs[1]["name"],
            quantity=2,
            bulk="L",
            description=f"Deals {tier_bombs[1]['dice']} electricity, {tier_bombs[1]['splash']}, flat-footed on hit."
        ))
        consumables.append(ConsumableItem(
            name=tier_bombs[2]["name"],
            quantity=2,
            bulk="L",
            description=f"Deals {tier_bombs[2]['dice']} acid, {tier_bombs[2]['persistent']}, and {tier_bombs[2]['splash']}."
        ))
        # Add signature elixir
        elixir_name = "Elixir of Life (Moderate)" if lvl >= 5 else ("Elixir of Life (Lesser)" if lvl >= 3 else "Minor Healing Potion")
        elixir_desc = "Restores 3d6+6 HP and +1 bonus vs disease/poison." if "Lesser" in elixir_name else "Restores 1d8 HP."
        consumables.append(ConsumableItem(name=elixir_name, quantity=2, bulk="L", description=elixir_desc))
    if lvl == 1:
        consumables.append(ConsumableItem(name="Minor Healing Potion", quantity=2, bulk="L", description="Restores 1d8 HP (1 Action)."))
    elif lvl in [2, 3]:
        consumables.append(ConsumableItem(name="Lesser Healing Potion", quantity=2, bulk="L", description="Restores 2d8+5 HP (1 Action)."))
        consumables.append(ConsumableItem(name="Silversheen", quantity=1, bulk="L", description="Grants weapon silver property for 1 hour."))
    elif lvl == 6:
        consumables.append(ConsumableItem(name="Moderate Healing Potion", quantity=2, bulk="L", description="Restores 3d8+10 HP (1 Action)."))
        consumables.append(ConsumableItem(name="Elixir of Life (Lesser)", quantity=1, bulk="L", description="Restores 3d6+6 HP and +1 bonus vs disease/poison."))
    else:
        # Level 7 Loadout
        consumables.append(ConsumableItem(name="Moderate Healing Potion", quantity=2, bulk="L", description="Restores 3d8+10 HP (1 Action)."))
        consumables.append(ConsumableItem(name="Elixir of Life (Moderate)", quantity=1, bulk="L", description="Restores 3d6+6 HP and +1 bonus vs disease/poison."))
        consumables.append(ConsumableItem(name="Mistform Elixir (Lesser)", quantity=1, bulk="L", description="Gain concealment (DC 5 flat check) for 3 rounds."))

    # 5. Remaining Coin Purse (GP, SP, CP)
    if lvl == 7:
        remaining_gp = 45
    elif lvl == 6:
        remaining_gp = 25
    else:
        remaining_gp = max(3, budget_gp)
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
