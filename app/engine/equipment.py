from typing import Dict, Any, List, Tuple
from app.engine.models import Item, Strike, EquipmentLoadout

WEAPONS_DB: Dict[str, Dict[str, Any]] = {
    "Longsword": {"damage": "1d8", "type": "slashing", "traits": ["versatile P"], "bulk": "1"},
    "Greatsword": {"damage": "1d12", "type": "slashing", "traits": ["two-hand d12", "versatile P"], "bulk": "2"},
    "Shortsword": {"damage": "1d6", "type": "piercing", "traits": ["agile", "finesse", "versatile S"], "bulk": "L"},
    "Rapier": {"damage": "1d6", "type": "piercing", "traits": ["deadly d8", "disarm", "finesse"], "bulk": "1"},
    "Dagger": {"damage": "1d4", "type": "piercing", "traits": ["agile", "finesse", "thrown 10ft", "versatile S"], "bulk": "L"},
    "Shortbow": {"damage": "1d6", "type": "piercing", "traits": ["deadly d10", "range 60ft", "reload 0"], "bulk": "1"},
    "Heavy Crossbow": {"damage": "1d10", "type": "piercing", "traits": ["range 120ft", "reload 2"], "bulk": "2"},
    "Greataxe": {"damage": "1d12", "type": "slashing", "traits": ["sweep", "two-hand"], "bulk": "2"},
    "Staff": {"damage": "1d4", "type": "bludgeoning", "traits": ["two-hand d8"], "bulk": "1"},
    "Warhammer": {"damage": "1d8", "type": "bludgeoning", "traits": ["shove"], "bulk": "1"},
    "Shield Boss": {"damage": "1d6", "type": "bludgeoning", "traits": ["attached to shield"], "bulk": "-"}
}

ARMOR_DB: Dict[str, Dict[str, Any]] = {
    "Unarmored": {"ac_bonus": 0, "dex_cap": 5, "bulk": "-"},
    "Explorer's Clothing": {"ac_bonus": 0, "dex_cap": 5, "bulk": "L"},
    "Leather Armor": {"ac_bonus": 1, "dex_cap": 4, "bulk": "1"},
    "Studded Leather": {"ac_bonus": 2, "dex_cap": 3, "bulk": "1"},
    "Chain Shirt": {"ac_bonus": 2, "dex_cap": 3, "bulk": "1"},
    "Hide Armor": {"ac_bonus": 3, "dex_cap": 2, "bulk": "2"},
    "Breastplate": {"ac_bonus": 4, "dex_cap": 1, "bulk": "2"},
    "Chain Mail": {"ac_bonus": 4, "dex_cap": 1, "bulk": "2"}
}

ADVENTURER_PACK = [
    "Backpack", "Bedroll", "10x Chalk", "Flint and Steel", "50ft Rope",
    "2 weeks Rations", "Soap", "5x Torches", "Waterskin"
]

def resolve_equipment(
    class_name: str,
    str_mod: int,
    dex_mod: int,
    level: int = 1
) -> Tuple[EquipmentLoadout, int, int]:
    """
    Returns: (EquipmentLoadout, calculated_ac, shield_circumstance_bonus)
    """
    cls = class_name.lower()
    is_finesse_dex = dex_mod > str_mod

    weapons_to_give: List[str] = []
    armor_name = "Leather Armor"
    has_shield = False

    # 1. Determine Class Weapon & Armor Allocation
    if cls in ["fighter", "champion"]:
        has_shield = True
        if is_finesse_dex:
            armor_name = "Studded Leather"
            weapons_to_give = ["Rapier", "Shortbow", "Dagger"]
        else:
            armor_name = "Breastplate"
            weapons_to_give = ["Longsword", "Shortsword"]

    elif cls in ["barbarian"]:
        armor_name = "Hide Armor"
        weapons_to_give = ["Greataxe", "Dagger"]

    elif cls in ["rogue", "swashbuckler"]:
        armor_name = "Leather Armor"
        weapons_to_give = ["Rapier", "Shortbow", "Dagger"]

    elif cls in ["ranger"]:
        armor_name = "Studded Leather"
        if is_finesse_dex:
            weapons_to_give = ["Shortbow", "Shortsword"]
        else:
            weapons_to_give = ["Longsword", "Shortbow"]

    elif cls in ["cleric"]:
        has_shield = True
        armor_name = "Hide Armor" if str_mod >= 2 else "Chain Shirt"
        weapons_to_give = ["Warhammer", "Dagger"]

    elif cls in ["wizard", "sorcerer", "witch"]:
        armor_name = "Explorer's Clothing"
        weapons_to_give = ["Staff", "Dagger", "Heavy Crossbow"]

    elif cls in ["bard", "druid"]:
        armor_name = "Leather Armor"
        weapons_to_give = ["Shortsword", "Staff"]

    elif cls in ["monk"]:
        armor_name = "Explorer's Clothing"
        weapons_to_give = ["Staff", "Dagger"]

    else:
        armor_name = "Leather Armor"
        weapons_to_give = ["Longsword", "Dagger"]

    # 2. Build Item Models
    armor_spec = ARMOR_DB.get(armor_name, ARMOR_DB["Leather Armor"])
    armor_item = Item(name=armor_name, category="armor", bulk=armor_spec["bulk"])
    
    shield_item = Item(name="Steel Shield", category="shield", bulk="1") if has_shield else None
    weapon_items = [
        Item(name=w, category="weapon", bulk=WEAPONS_DB.get(w, {}).get("bulk", "1"))
        for w in weapons_to_give
    ]

    # 3. Calculate AC (10 + Trained Proficiency (2 + Level) + Item Bonus + Min(Dex, Dex Cap))
    prof_bonus = 2 + level  # Standard starting Trained proficiency in armor/unarmored
    ac_dex = min(dex_mod, armor_spec["dex_cap"])
    calculated_ac = 10 + prof_bonus + armor_spec["ac_bonus"] + ac_dex

    # 4. Generate Calculated Strikes
    strikes: List[Strike] = []
    # Most Level 1 martial classes are Trained (Expert for Fighters)
    weapon_prof_rank = 4 if cls == "fighter" else 2
    attack_base = weapon_prof_rank + level

    for w_name in weapons_to_give:
        spec = WEAPONS_DB.get(w_name, {"damage": "1d4", "type": "bludgeoning", "traits": []})
        traits = spec["traits"]

        # Attack modifier calculation (Dex for ranged, Finesse chooses best of Str/Dex, Str for others)
        is_ranged = any("range" in t for t in traits)
        is_finesse = "finesse" in traits

        if is_ranged:
            atk_mod = dex_mod
        elif is_finesse:
            atk_mod = max(str_mod, dex_mod)
        else:
            atk_mod = str_mod

        total_attack = attack_base + atk_mod

        # Damage calculation: Ranged without propulsive adds +0 Str, Melee adds full Str
        dmg_dice = spec["damage"]
        if is_ranged:
            dmg_formula = dmg_dice
        else:
            dmg_formula = f"{dmg_dice}+{str_mod}" if str_mod != 0 else dmg_dice

        strikes.append(Strike(
            name=w_name,
            attack_bonus=total_attack,
            damage_dice=dmg_formula,
            damage_type=spec["type"],
            traits=traits
        ))

    gear_list = list(ADVENTURER_PACK)
    if any("Shortbow" in w or "Crossbow" in w for w in weapons_to_give):
        gear_list.append("Quiver with 20 Arrows/Bolts")

    loadout = EquipmentLoadout(
        armor=armor_item,
        shield=shield_item,
        weapons=weapon_items,
        gear=gear_list,
        strikes=strikes
    )

    shield_bonus = 2 if has_shield else 0
    return loadout, calculated_ac, shield_bonus
