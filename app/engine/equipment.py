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

def select_class_weapons(
    cls_key: str,
    str_mod: int,
    dex_mod: int,
    ancestry_name: str = "",
    subclass_name: str = "",
    archetype_name: str = ""
) -> List[Dict[str, Any]]:
    """Dynamically selects rule-compliant weapons calibrated to class, subclass, and archetype restrictions."""
    is_dex_build = dex_mod > str_mod
    anc_key = (ancestry_name or "").lower().strip()
    sub_key = (subclass_name or "").lower().strip()
    arch_key = (archetype_name or "").lower().strip()
    anc_options = ANCESTRAL_WEAPONS.get(anc_key, [])

    # Archetype Overrides
    if "archer" in arch_key:
        bows = [w for w in MARTIAL_RANGED if "Bow" in w["name"]]
        prim = random.choice(bows if bows else MARTIAL_RANGED)
        sec = random.choice(MARTIAL_FINESSE + SECONDARY_BACKUPS)
        return [prim, sec]

    if "mauler" in arch_key:
        prim = random.choice(MARTIAL_TWO_HANDED)
        sec = random.choice([w for w in MARTIAL_TWO_HANDED if w["name"] != prim["name"]] + SECONDARY_BACKUPS)
        return [prim, sec]

    if "dual-weapon" in arch_key or "dual weapon" in arch_key:
        prim = random.choice(MARTIAL_ONE_HANDED + MARTIAL_FINESSE)
        sec = random.choice([w for w in (MARTIAL_FINESSE + SECONDARY_BACKUPS) if "Agile" in w.get("traits", []) and w["name"] != prim["name"]])
        return [prim, sec]

    # 1. Gunslinger Subclasses (Ways)
    if cls_key == "gunslinger":
        if "pistolero" in sub_key or "pistol" in arch_key:
            prim = random.choice(ONE_HANDED_FIREARMS)
            sec = random.choice(MARTIAL_FINESSE)
            return [prim, sec]
        elif "sniper" in sub_key:
            prim = random.choice(TWO_HANDED_SNIPER_FIREARMS)
            sec = random.choice(SECONDARY_BACKUPS)
            return [prim, sec]
        elif "vanguard" in sub_key:
            prim = random.choice(VANGUARD_FIREARMS)
            sec = random.choice([w for w in (SECONDARY_BACKUPS + MARTIAL_FINESSE) if w["name"] != prim["name"]])
            return [prim, sec]
        elif "drifter" in sub_key:
            prim = random.choice(ONE_HANDED_FIREARMS)
            sec = random.choice(MARTIAL_FINESSE)
            return [prim, sec]
        elif "triggerbrand" in sub_key:
            prim = random.choice(COMBINATION_FIREARMS)
            sec = random.choice(SECONDARY_BACKUPS)
            return [prim, sec]
        else:
            guns = ONE_HANDED_FIREARMS + TWO_HANDED_SNIPER_FIREARMS
            prim = random.choice(guns)
            sec = random.choice(MARTIAL_FINESSE + SECONDARY_BACKUPS)
            return [prim, sec]

    # 2. Rogue & Swashbuckler (Ruffian vs Finesse/Agile)
    if cls_key == "rogue":
        if "ruffian" in sub_key:
            ruffian_pool = [w for w in (SIMPLE_MELEE + MARTIAL_ONE_HANDED) if w.get("dice") in ["1d6", "1d8", "1d4"]]
            prim = random.choice(ruffian_pool if ruffian_pool else SIMPLE_MELEE)
            sec = random.choice(SIMPLE_RANGED + SECONDARY_BACKUPS)
            return [prim, sec]
        else:
            finesse_pool = list(MARTIAL_FINESSE)
            if anc_options:
                finesse_pool += [w for w in anc_options if "Finesse" in w.get("traits", []) or "Agile" in w.get("traits", [])]
            prim = random.choice(finesse_pool)
            sec = random.choice([w for w in (SECONDARY_BACKUPS + SIMPLE_RANGED) if w["name"] != prim["name"]])
            return [prim, sec]

    if cls_key in ["swashbuckler", "investigator"]:
        finesse_pool = list(MARTIAL_FINESSE)
        if anc_options:
            finesse_pool += [w for w in anc_options if "Finesse" in w.get("traits", []) or "Agile" in w.get("traits", [])]
        prim = random.choice(finesse_pool)
        sec = random.choice([w for w in (SECONDARY_BACKUPS + SIMPLE_RANGED) if w["name"] != prim["name"]])
        return [prim, sec]

    # 3. Fighter, Champion, Barbarian
    if cls_key in ["fighter", "barbarian", "champion"]:
        if anc_options and random.random() < 0.35:
            prim = random.choice(anc_options)
        elif is_dex_build:
            dex_pool = MARTIAL_FINESSE + [w for w in MARTIAL_RANGED if "Bow" in w["name"]]
            if anc_options:
                dex_pool += [w for w in anc_options if "Finesse" in w.get("traits", []) or "Ranged" in " ".join(w.get("traits", []))]
            prim = random.choice(dex_pool)
        else:
            style_roll = random.random()
            if style_roll < 0.40 and cls_key != "barbarian":
                prim = random.choice(MARTIAL_ONE_HANDED)
            elif style_roll < 0.75:
                prim = random.choice(MARTIAL_TWO_HANDED)
            else:
                prim = random.choice(MARTIAL_ONE_HANDED + MARTIAL_TWO_HANDED)

        sec_pool = [w for w in (SECONDARY_BACKUPS + MARTIAL_RANGED + SIMPLE_RANGED) if w["name"] != prim["name"]]
        sec = random.choice(sec_pool)
        return [prim, sec]

    # 4. Ranger
    if cls_key == "ranger":
        prim = random.choice(MARTIAL_RANGED if is_dex_build else (MARTIAL_ONE_HANDED + MARTIAL_TWO_HANDED))
        sec_pool = [w for w in (MARTIAL_FINESSE + SECONDARY_BACKUPS) if w["name"] != prim["name"]]
        return [prim, random.choice(sec_pool)]

    # 5. Monk
    if cls_key == "monk":
        monk_options = [
            {"name": "Bo Staff", "dice": "1d8", "type": "Bludgeoning", "traits": ["Monk", "Parry", "Reach", "Trip"]},
            {"name": "Temple Sword", "dice": "1d8", "type": "Slashing", "traits": ["Monk", "Trip"]},
            {"name": "Tiger Fork", "dice": "1d8", "type": "Piercing", "traits": ["Monk", "Two-Hand d10"]},
            {"name": "Kama", "dice": "1d6", "type": "Slashing", "traits": ["Agile", "Monk", "Trip"]},
            {"name": "Nunchaku", "dice": "1d6", "type": "Bludgeoning", "traits": ["Backswing", "Disarm", "Finesse", "Monk"]},
            {"name": "Shuriken", "dice": "1d4", "type": "Piercing", "traits": ["Agile", "Monk", "Reload 0", "Thrown 20 ft"]},
        ]
        prim = random.choice(monk_options)
        sec = random.choice([w for w in monk_options if w["name"] != prim["name"]])
        return [prim, sec]

    # 6. Cleric, Druid, Kineticist, Thaumaturge
    if cls_key in ["cleric", "druid", "kineticist", "thaumaturge"]:
        prim = random.choice(SIMPLE_MELEE + (MARTIAL_ONE_HANDED if cls_key in ["thaumaturge", "cleric"] else []))
        sec = random.choice(SIMPLE_RANGED + SECONDARY_BACKUPS)
        return [prim, sec]

    # 7. Bard, Alchemist
    if cls_key in ["bard", "alchemist"]:
        prim = random.choice(MARTIAL_FINESSE + SIMPLE_MELEE)
        sec = random.choice(SIMPLE_RANGED + SECONDARY_BACKUPS)
        return [prim, sec]

    # 8. Casters (Wizard, Witch, Sorcerer, Oracle, Psychic)
    caster_primary = [
        {"name": "Staff", "dice": "1d4", "type": "Bludgeoning", "traits": ["Two-Hand d8"]},
        {"name": "Spear", "dice": "1d6", "type": "Piercing", "traits": ["Thrown 20 ft"]},
        {"name": "Morningstar", "dice": "1d6", "type": "Bludgeoning", "traits": ["Versatile P"]},
        {"name": "Sickle", "dice": "1d4", "type": "Slashing", "traits": ["Agile", "Finesse", "Trip"]},
        {"name": "Club", "dice": "1d6", "type": "Bludgeoning", "traits": ["Thrown 10 ft"]},
    ]
    caster_ranged = [
        {"name": "Crossbow", "dice": "1d8", "type": "Piercing", "traits": ["Range 120 ft", "Reload 1"]},
        {"name": "Sling", "dice": "1d6", "type": "Bludgeoning", "traits": ["Propulsive", "Range 50 ft", "Reload 1"]},
        {"name": "Dart", "dice": "1d4", "type": "Piercing", "traits": ["Agile", "Thrown 20 ft"]},
        {"name": "Dagger", "dice": "1d4", "type": "Piercing", "traits": ["Agile", "Finesse", "Thrown 10 ft", "Versatile S"]},
    ]
    prim = random.choice(caster_primary)
    sec = random.choice([w for w in caster_ranged if w["name"] != prim["name"]])
    return [prim, sec]


def resolve_equipment(
    class_name: str,
    str_mod: int,
    dex_mod: int,
    level: int = 1,
    ancestry_name: str = "",
    subclass_name: str = "",
    archetype_name: str = ""
) -> Tuple[EquipmentLoadout, int, int]:
    cls_key = class_name.lower()
    lvl = max(1, min(7, level))
    wealth_cfg = WEALTH_BY_LEVEL.get(lvl, WEALTH_BY_LEVEL[1])

    budget_gp = wealth_cfg["lump_gp"]

    # 1. Base Weapon Selection & Rune Progression
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
        eligible_items = [i for i in PERMANENT_MAGIC_ITEMS if i["level"] <= lvl]
        chosen_items = random.sample(eligible_items, min(num_perm, len(eligible_items)))
        for item in chosen_items:
            gear.append(f"{item['name']} ({item['description']})")
            budget_gp -= min(item["cost_gp"], budget_gp // 2)

    # 4. Consumables Scaling by Level
    consumables: List[ConsumableItem] = []
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