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
}

PERMANENT_MAGIC_ITEMS: List[Dict[str, Any]] = [
    {"name": "Healer's Gloves", "level": 3, "cost_gp": 50, "bulk": "L", "description": "+1 item bonus to Medicine; 1/day activate to heal 2d6+7 HP."},
    {"name": "Crafter's Eyepiece", "level": 3, "cost_gp": 60, "bulk": "-", "description": "+1 item bonus to Crafting checks and repairing."},
    {"name": "Hat of Disguise", "level": 2, "cost_gp": 30, "bulk": "L", "description": "Cast illusory disguise as an innate arcane spell at will."},
    {"name": "Boots of Elvenkind", "level": 5, "cost_gp": 145, "bulk": "L", "description": "+1 item bonus to Acrobatics; ignore difficult terrain 1/day."},
    {"name": "Cloak of the Bat", "level": 5, "cost_gp": 160, "bulk": "L", "description": "+1 item bonus to Stealth; 1/day fly or turn into a bat."},
    {"name": "Bracers of Missile Deflection", "level": 3, "cost_gp": 52, "bulk": "L", "description": "+1 circumstance bonus to AC against ranged attacks with reaction."}
]

CLASS_WEAPONS: Dict[str, List[Dict[str, Any]]] = {
    "fighter": [
        {"name": "Longsword", "dice": "1d8", "type": "Slashing", "traits": ["Versatile P"]},
        {"name": "Shortbow", "dice": "1d6", "type": "Piercing", "traits": ["Deadly d10", "Range 60 ft"]}
    ],
    "barbarian": [
        {"name": "Greataxe", "dice": "1d12", "type": "Slashing", "traits": ["Sweep"]},
        {"name": "Javelin", "dice": "1d6", "type": "Piercing", "traits": ["Thrown 30 ft"]}
    ],
    "rogue": [
        {"name": "Rapier", "dice": "1d6", "type": "Piercing", "traits": ["Deadly d8", "Disarm", "Finesse"]},
        {"name": "Shortsword", "dice": "1d6", "type": "Piercing", "traits": ["Agile", "Finesse", "Versatile S"]}
    ],
    "wizard": [
        {"name": "Staff", "dice": "1d4", "type": "Bludgeoning", "traits": ["Two-Hand d8"]},
        {"name": "Dagger", "dice": "1d4", "type": "Piercing", "traits": ["Agile", "Finesse", "Thrown 10 ft", "Versatile S"]}
    ],
    "cleric": [
        {"name": "Warhammer", "dice": "1d8", "type": "Bludgeoning", "traits": ["Shove"]},
        {"name": "Light Crossbow", "dice": "1d8", "type": "Piercing", "traits": ["Range 120 ft", "Reload 1"]}
    ],
    "default": [
        {"name": "Dagger", "dice": "1d4", "type": "Piercing", "traits": ["Agile", "Finesse", "Thrown 10 ft", "Versatile S"]},
        {"name": "Staff", "dice": "1d4", "type": "Bludgeoning", "traits": ["Two-Hand d8"]}
    ]
}

def resolve_equipment(
    class_name: str,
    str_mod: int,
    dex_mod: int,
    level: int = 1
) -> Tuple[EquipmentLoadout, int, int]:
    cls_key = class_name.lower()
    lvl = max(1, min(6, level))
    wealth_cfg = WEALTH_BY_LEVEL.get(lvl, WEALTH_BY_LEVEL[1])

    budget_gp = wealth_cfg["lump_gp"]

    # 1. Base Weapon Selection & Rune Progression
    raw_weps = CLASS_WEAPONS.get(cls_key, CLASS_WEAPONS["default"])
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
    else:
        consumables.append(ConsumableItem(name="Moderate Healing Potion", quantity=2, bulk="L", description="Restores 3d8+10 HP (1 Action)."))
        consumables.append(ConsumableItem(name="Elixir of Life (Lesser)", quantity=1, bulk="L", description="Restores 3d6+6 HP and +1 bonus vs disease/poison."))

    # 5. Remaining Coin Purse (GP, SP, CP)
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
