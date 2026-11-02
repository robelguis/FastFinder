import random
from typing import Dict, Any, Tuple, List, Optional
from app.engine.models import EquipmentLoadout, Item, Strike, Wealth, ConsumableItem

# Class-specific weapon packages and strikes
CLASS_WEAPON_CONFIGS: Dict[str, Dict[str, Any]] = {
    "monk": {
        "armor": None,
        "shield": None,
        "weapons": [
            {"name": "Bo Staff", "bulk": 2}
        ],
        "strikes": [
            {
                "name": "Powerful Fist (Unarmed)",
                "dice": "1d6",
                "type": "Bludgeoning",
                "traits": ["Agile", "Finesse", "Nonlethal", "Unarmed"],
                "finesse": True
            },
            {
                "name": "Tiger Claw (Stance)",
                "dice": "1d8",
                "type": "Slashing",
                "traits": ["Agile", "Finesse", "Unarmed"],
                "finesse": True
            }
        ],
        "gear": ["Monk's Robes", "Bandolier", "Bedroll", "Rations (1 week)", "Waterskin"]
    },
    "gunslinger": {
        "armor": {"name": "Leather Armor", "bulk": 1, "ac_bonus": 1, "dex_cap": 4},
        "shield": None,
        "weapons": [
            {"name": "Dueling Pistol", "bulk": 1},
            {"name": "Dagger", "bulk": "L"}
        ],
        "strikes": [
            {
                "name": "Dueling Pistol",
                "dice": "1d6",
                "type": "Piercing",
                "traits": ["Concussive", "Fatal d10", "Range 60 ft", "Reload 1"],
                "finesse": False,
                "is_ranged": True
            },
            {
                "name": "Dagger",
                "dice": "1d4",
                "type": "Piercing",
                "traits": ["Agile", "Finesse", "Thrown 10 ft", "Versatile S"],
                "finesse": True
            }
        ],
        "gear": ["Firearm Ammunition (30 rounds)", "Cleaning Kit", "Powder Horn", "Backpack", "Waterskin"]
    },
    "thaumaturge": {
        "armor": {"name": "Studded Leather", "bulk": 1, "ac_bonus": 2, "dex_cap": 3},
        "shield": None,
        "weapons": [
            {"name": "Warhammer", "bulk": 1},
            {"name": "Esoteric Implement (Amulet/Chalice)", "bulk": "L"}
        ],
        "strikes": [
            {
                "name": "Warhammer",
                "dice": "1d8",
                "type": "Bludgeoning",
                "traits": ["Shove"],
                "finesse": False
            }
        ],
        "gear": ["Esoteric Lore Components Pouch", "Grimoire", "Backpack", "Rations (1 week)", "Waterskin"]
    },
    "swashbuckler": {
        "armor": {"name": "Leather Armor", "bulk": 1, "ac_bonus": 1, "dex_cap": 4},
        "shield": {"name": "Buckler", "bulk": "L", "ac_bonus": 1},
        "weapons": [
            {"name": "Rapier", "bulk": 1},
            {"name": "Main-Gauche", "bulk": "L"}
        ],
        "strikes": [
            {
                "name": "Rapier",
                "dice": "1d6",
                "type": "Piercing",
                "traits": ["Deadly d8", "Disarm", "Finesse"],
                "finesse": True
            },
            {
                "name": "Main-Gauche",
                "dice": "1d4",
                "type": "Piercing",
                "traits": ["Agile", "Disarm", "Finesse", "Parry", "Versatile S"],
                "finesse": True
            }
        ],
        "gear": ["Fine Clothes", "Disguise Kit", "Backpack", "Bedroll", "Waterskin"]
    },
    "rogue": {
        "armor": {"name": "Leather Armor", "bulk": 1, "ac_bonus": 1, "dex_cap": 4},
        "shield": None,
        "weapons": [
            {"name": "Shortsword", "bulk": "L"},
            {"name": "Dagger", "bulk": "L"}
        ],
        "strikes": [
            {
                "name": "Shortsword",
                "dice": "1d6",
                "type": "Piercing",
                "traits": ["Agile", "Finesse", "Versatile S"],
                "finesse": True
            },
            {
                "name": "Dagger",
                "dice": "1d4",
                "type": "Piercing",
                "traits": ["Agile", "Finesse", "Thrown 10 ft", "Versatile S"],
                "finesse": True
            }
        ],
        "gear": ["Thieves' Tools", "Backpack", "Bedroll", "Rations (1 week)", "50ft Silk Rope"]
    },
    "fighter": {
        "armor": {"name": "Scale Mail", "bulk": 2, "ac_bonus": 3, "dex_cap": 2},
        "shield": {"name": "Steel Shield", "bulk": 1, "ac_bonus": 2},
        "weapons": [
            {"name": "Longsword", "bulk": 1},
            {"name": "Shortbow", "bulk": 1}
        ],
        "strikes": [
            {
                "name": "Longsword",
                "dice": "1d8",
                "type": "Slashing",
                "traits": ["Versatile P"],
                "finesse": False
            },
            {
                "name": "Shortbow",
                "dice": "1d6",
                "type": "Piercing",
                "traits": ["Deadly d10", "Range 60 ft", "Reload 0"],
                "finesse": False,
                "is_ranged": True
            }
        ],
        "gear": ["Arrows (20)", "Backpack", "Bedroll", "Rations (1 week)", "Waterskin"]
    },
    "champion": {
        "armor": {"name": "Splint Mail", "bulk": 3, "ac_bonus": 4, "dex_cap": 1},
        "shield": {"name": "Steel Shield", "bulk": 1, "ac_bonus": 2},
        "weapons": [
            {"name": "Warhammer", "bulk": 1}
        ],
        "strikes": [
            {
                "name": "Warhammer",
                "dice": "1d8",
                "type": "Bludgeoning",
                "traits": ["Shove"],
                "finesse": False
            }
        ],
        "gear": ["Religious Symbol (Silver)", "Backpack", "Bedroll", "Rations (1 week)", "Waterskin"]
    },
    "kineticist": {
        "armor": {"name": "Leather Armor", "bulk": 1, "ac_bonus": 1, "dex_cap": 4},
        "shield": None,
        "weapons": [
            {"name": "Kinetic Gate Focus", "bulk": "L"}
        ],
        "strikes": [
            {
                "name": "Elemental Blast (Melee)",
                "dice": "1d8",
                "type": "Elemental",
                "traits": ["Impulse", "Kinetic", "Primal"],
                "finesse": False,
                "add_con_damage": True
            },
            {
                "name": "Elemental Blast (Ranged)",
                "dice": "1d8",
                "type": "Elemental",
                "traits": ["Impulse", "Kinetic", "Primal", "Range 60 ft"],
                "finesse": False,
                "is_ranged": True
            }
        ],
        "gear": ["Adventurer's Pack", "Bedroll", "Rations (1 week)", "Waterskin"]
    },
    "alchemist": {
        "armor": {"name": "Studded Leather", "bulk": 1, "ac_bonus": 2, "dex_cap": 3},
        "shield": None,
        "weapons": [
            {"name": "Dagger", "bulk": "L"},
            {"name": "Sling", "bulk": "L"}
        ],
        "strikes": [
            {
                "name": "Dagger",
                "dice": "1d4",
                "type": "Piercing",
                "traits": ["Agile", "Finesse", "Thrown 10 ft"],
                "finesse": True
            },
            {
                "name": "Alchemical Bomb (Lesser)",
                "dice": "1d8",
                "type": "Fire / Acid",
                "traits": ["Bomb", "Consumable", "Splash 1", "Range 20 ft"],
                "finesse": False,
                "is_ranged": True
            }
        ],
        "gear": ["Alchemist's Toolkit", "Formula Book", "Sling Bullets (20)", "Backpack", "Waterskin"]
    }
}

DEFAULT_CASTER_CONFIG = {
    "armor": {"name": "Explorer's Clothing", "bulk": "L", "ac_bonus": 0, "dex_cap": 5},
    "shield": None,
    "weapons": [
        {"name": "Staff", "bulk": 1},
        {"name": "Dagger", "bulk": "L"}
    ],
    "strikes": [
        {
            "name": "Staff",
            "dice": "1d4",
            "type": "Bludgeoning",
            "traits": ["Two-Hand d8"],
            "finesse": False
        },
        {
            "name": "Dagger",
            "dice": "1d4",
            "type": "Piercing",
            "traits": ["Agile", "Finesse", "Thrown 10 ft", "Versatile S"],
            "finesse": True
        }
    ],
    "gear": ["Backpack", "Bedroll", "Rations (1 week)", "Waterskin", "Torch (5)", "Flint and Steel", "50ft Rope"]
}

DEFAULT_MARTIAL_CONFIG = {
    "armor": {"name": "Hide Armor", "bulk": 2, "ac_bonus": 3, "dex_cap": 2},
    "shield": {"name": "Wooden Shield", "bulk": 1, "ac_bonus": 2},
    "weapons": [
        {"name": "Longsword", "bulk": 1}
    ],
    "strikes": [
        {
            "name": "Longsword",
            "dice": "1d8",
            "type": "Slashing",
            "traits": ["Versatile P"],
            "finesse": False
        }
    ],
    "gear": ["Backpack", "Bedroll", "Rations (1 week)", "Waterskin", "50ft Rope"]
}

def resolve_equipment(
    class_name: str,
    str_mod: int,
    dex_mod: int,
    level: int = 1
) -> Tuple[EquipmentLoadout, int, int]:
    cls_key = class_name.lower()
    
    # 1. Resolve equipment config
    if cls_key in CLASS_WEAPON_CONFIGS:
        cfg = CLASS_WEAPON_CONFIGS[cls_key]
    elif cls_key in ["wizard", "witch", "sorcerer", "oracle", "psychic", "animist", "cleric", "bard", "druid"]:
        cfg = DEFAULT_CASTER_CONFIG
    else:
        cfg = DEFAULT_MARTIAL_CONFIG

    # 2. Calculate AC
    armor_data = cfg.get("armor")
    shield_data = cfg.get("shield")
    
    shield_bonus = shield_data.get("ac_bonus", 0) if shield_data else 0

    if armor_data:
        ac_bonus = armor_data.get("ac_bonus", 0)
        dex_cap = armor_data.get("dex_cap", 5)
        applied_dex = min(dex_mod, dex_cap)
        # Standard trained proficiency bonus: 2 + level
        prof_bonus = 2 + level
        calc_ac = 10 + ac_bonus + applied_dex + prof_bonus
        armor_item = Item(name=armor_data["name"], bulk=armor_data.get("bulk", 1))
    else:
        # Unarmored (e.g. Monk) - full DEX, standard unarmored trained/expert
        prof_rank = 4 if cls_key == "monk" else 2  # Monks start Expert in unarmored
        calc_ac = 10 + dex_mod + (prof_rank + level)
        armor_item = Item(name="Unarmored Defense", bulk="0")

    shield_item = Item(name=shield_data["name"], bulk=shield_data.get("bulk", 1)) if shield_data else None

    # 3. Resolve Strikes
    strikes: List[Strike] = []
    # Fighter and Gunslinger start Expert (+4) with weapons
    attack_prof_rank = 4 if cls_key in ["fighter", "gunslinger"] else 2
    base_prof_bonus = attack_prof_rank + level

    for st in cfg.get("strikes", []):
        is_finesse = st.get("finesse", False)
        is_ranged = st.get("is_ranged", False)

        if is_ranged:
            atk_bonus = base_prof_bonus + dex_mod
            dmg_mod = str_mod if "Propulsive" in st.get("traits", []) else 0
        elif is_finesse:
            chosen_mod = max(str_mod, dex_mod)
            atk_bonus = base_prof_bonus + chosen_mod
            dmg_mod = str_mod
        else:
            atk_bonus = base_prof_bonus + str_mod
            dmg_mod = str_mod

        # Kineticist adds CON to blast damage
        if st.get("add_con_damage", False):
            dmg_mod = str_mod

        # Level 4 Potency Rune bonus (+1 to attack)
        if level >= 4 and not is_ranged:
            atk_bonus += 1

        is_agile = "Agile" in st.get("traits", [])
        map_second = atk_bonus - (4 if is_agile else 5)
        map_third = atk_bonus - (8 if is_agile else 10)

        dmg_str = f"{st['dice']}+{dmg_mod}" if dmg_mod > 0 else (f"{st['dice']}{dmg_mod}" if dmg_mod < 0 else st['dice'])

        strikes.append(Strike(
            name=st["name"],
            attack_bonus=atk_bonus,
            map_second=map_second,
            map_third=map_third,
            damage_dice=dmg_str,
            damage_type=st["type"],
            traits=st.get("traits", [])
        ))

    # 4. Consumables scaling with level
    potion_count = 2 if level >= 3 else 1
    potion_name = "Lesser Healing Potion" if level >= 3 else "Minor Healing Potion"
    potion_desc = "Drink to restore 2d8+5 Hit Points (1 Action)." if level >= 3 else "Drink to restore 1d8 Hit Points (1 Action)."

    consumables = [
        ConsumableItem(
            name=potion_name,
            quantity=potion_count,
            item_type="potion",
            bulk="L",
            description=potion_desc
        )
    ]

    weapons_items = [Item(name=w["name"], bulk=w.get("bulk", 1)) for w in cfg.get("weapons", [])]

    loadout = EquipmentLoadout(
        weapons=weapons_items,
        armor=armor_item,
        shield=shield_item,
        gear=cfg.get("gear", []),
        consumables=consumables,
        money=Wealth(gp=10 + level * 5, sp=4, cp=8),
        strikes=strikes
    )

    return loadout, calc_ac, shield_bonus
