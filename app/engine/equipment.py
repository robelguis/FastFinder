from typing import Dict, Any, List, Tuple
from app.engine.models import Item, Strike, EquipmentLoadout, Wealth

WEAPONS_DB: Dict[str, Dict[str, Any]] = {
    "Longsword": {"damage": "1d8", "type": "slashing", "traits": ["versatile P"], "bulk": "1", "cost_sp": 10},
    "Greatsword": {"damage": "1d12", "type": "slashing", "traits": ["two-hand d12", "versatile P"], "bulk": "2", "cost_sp": 20},
    "Shortsword": {"damage": "1d6", "type": "piercing", "traits": ["agile", "finesse", "versatile S"], "bulk": "L", "cost_sp": 9},
    "Rapier": {"damage": "1d6", "type": "piercing", "traits": ["deadly d8", "disarm", "finesse"], "bulk": "1", "cost_sp": 20},
    "Dagger": {"damage": "1d4", "type": "piercing", "traits": ["agile", "finesse", "thrown 10ft", "versatile S"], "bulk": "L", "cost_sp": 2},
    "Shortbow": {"damage": "1d6", "type": "piercing", "traits": ["deadly d10", "range 60ft", "reload 0"], "bulk": "1", "cost_sp": 30},
    "Heavy Crossbow": {"damage": "1d10", "type": "piercing", "traits": ["range 120ft", "reload 2"], "bulk": "2", "cost_sp": 40},
    "Greataxe": {"damage": "1d12", "type": "slashing", "traits": ["sweep", "two-hand"], "bulk": "2", "cost_sp": 20},
    "Staff": {"damage": "1d4", "type": "bludgeoning", "traits": ["two-hand d8"], "bulk": "1", "cost_sp": 0},
    "Warhammer": {"damage": "1d8", "type": "bludgeoning", "traits": ["shove"], "bulk": "1", "cost_sp": 10},
    "Shield Boss": {"damage": "1d6", "type": "bludgeoning", "traits": ["attached to shield"], "bulk": "-", "cost_sp": 5}
}

ARMOR_DB: Dict[str, Dict[str, Any]] = {
    "Unarmored": {"ac_bonus": 0, "dex_cap": 5, "bulk": "-", "cost_sp": 0},
    "Explorer's Clothing": {"ac_bonus": 0, "dex_cap": 5, "bulk": "L", "cost_sp": 1},
    "Leather Armor": {"ac_bonus": 1, "dex_cap": 4, "bulk": "1", "cost_sp": 20},
    "Studded Leather": {"ac_bonus": 2, "dex_cap": 3, "bulk": "1", "cost_sp": 30},
    "Chain Shirt": {"ac_bonus": 2, "dex_cap": 3, "bulk": "1", "cost_sp": 50},
    "Hide Armor": {"ac_bonus": 3, "dex_cap": 2, "bulk": "2", "cost_sp": 20},
    "Breastplate": {"ac_bonus": 4, "dex_cap": 1, "bulk": "2", "cost_sp": 80},
    "Chain Mail": {"ac_bonus": 4, "dex_cap": 1, "bulk": "2", "cost_sp": 60}
}

ADVENTURER_PACK_COST_SP = 15
ADVENTURER_PACK = [
    "Backpack", "Bedroll", "10x Chalk", "Flint and Steel", "50ft Rope",
    "2 weeks Rations", "Soap", "5x Torches", "Waterskin"
]

def format_wealth(total_sp: int) -> Wealth:
    if total_sp < 0:
        total_sp = 0
    gp = total_sp // 10
    sp = total_sp % 10
    parts = []
    if gp > 0:
        parts.append(f"{gp} gp")
    if sp > 0 or not parts:
        parts.append(f"{sp} sp")
    return Wealth(gp=gp, sp=sp, cp=0, formatted=", ".join(parts))

def resolve_equipment(
    class_name: str,
    str_mod: int,
    dex_mod: int,
    level: int = 1
) -> Tuple[EquipmentLoadout, int, int]:
    cls = class_name.lower()
    is_finesse_dex = dex_mod > str_mod

    weapons_to_give: List[str] = []
    armor_name = "Leather Armor"
    has_shield = False

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

    starting_allowance_sp = 150
    spent_sp = ADVENTURER_PACK_COST_SP

    armor_spec = ARMOR_DB.get(armor_name, ARMOR_DB["Leather Armor"])
    spent_sp += armor_spec.get("cost_sp", 0)
    armor_item = Item(
        name=armor_name,
        category="armor",
        bulk=armor_spec["bulk"],
        cost_sp=armor_spec.get("cost_sp", 0)
    )

    shield_item = None
    if has_shield:
        shield_cost_sp = 20
        spent_sp += shield_cost_sp
        shield_item = Item(name="Steel Shield", category="shield", bulk="1", cost_sp=shield_cost_sp)

    weapon_items = []
    for w in weapons_to_give:
        spec = WEAPONS_DB.get(w, {})
        w_cost = spec.get("cost_sp", 0)
        spent_sp += w_cost
        weapon_items.append(Item(
            name=w,
            category="weapon",
            bulk=spec.get("bulk", "1"),
            cost_sp=w_cost
        ))

    gear_list = list(ADVENTURER_PACK)
    if any("Shortbow" in w or "Crossbow" in w for w in weapons_to_give):
        quiver_cost_sp = 2
        spent_sp += quiver_cost_sp
        gear_list.append("Quiver with 20 Arrows/Bolts")

    remaining_wealth = format_wealth(starting_allowance_sp - spent_sp)

    prof_bonus = 2 + level
    ac_dex = min(dex_mod, armor_spec["dex_cap"])
    calculated_ac = 10 + prof_bonus + armor_spec["ac_bonus"] + ac_dex

    # Strikes and Multi-Attack Penalty (MAP)
    strikes: List[Strike] = []
    weapon_prof_rank = 4 if cls == "fighter" else 2
    attack_base = weapon_prof_rank + level

    for w_name in weapons_to_give:
        spec = WEAPONS_DB.get(w_name, {"damage": "1d4", "type": "bludgeoning", "traits": []})
        traits = spec["traits"]

        is_ranged = any("range" in t for t in traits)
        is_finesse = "finesse" in traits
        is_agile = "agile" in traits

        if is_ranged:
            atk_mod = dex_mod
        elif is_finesse:
            atk_mod = max(str_mod, dex_mod)
        else:
            atk_mod = str_mod

        total_attack = attack_base + atk_mod
        
        # Agile MAP is -4 / -8; Non-agile MAP is -5 / -10
        second_strike = total_attack - 4 if is_agile else total_attack - 5
        third_strike = total_attack - 8 if is_agile else total_attack - 10

        dmg_dice = spec["damage"]
        dmg_formula = dmg_dice if is_ranged else (f"{dmg_dice}+{str_mod}" if str_mod != 0 else dmg_dice)

        strikes.append(Strike(
            name=w_name,
            attack_bonus=total_attack,
            map_second=second_strike,
            map_third=third_strike,
            damage_dice=dmg_formula,
            damage_type=spec["type"],
            traits=traits
        ))

    loadout = EquipmentLoadout(
        armor=armor_item,
        shield=shield_item,
        weapons=weapon_items,
        gear=gear_list,
        money=remaining_wealth,
        strikes=strikes
    )

    shield_bonus = 2 if has_shield else 0
    return loadout, calculated_ac, shield_bonus
