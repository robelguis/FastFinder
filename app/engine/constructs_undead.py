import random
from typing import Dict, Any, List, Optional
from app.engine.models import PartnerCreatureData, Strike

# ==========================================
# 1. CONSTRUCT INNOVATION (INVENTOR)
# ==========================================
CONSTRUCT_MODIFICATIONS = [
    {
        "name": "Accelerated Mobility",
        "effect": "Its Speed increases to 40 feet and it gains the Quick Step action."
    },
    {
        "name": "Hardened Plating",
        "effect": "Its AC increases by +1 and it gains physical damage resistance equal to half master level."
    },
    {
        "name": "Retractable Claws & Spikes",
        "effect": "Its primary strikes gain the Agile and Versatile P/S traits."
    },
    {
        "name": "Subtle Chassis",
        "effect": "Construct is built with stealth dampers. It gains trained proficiency in Stealth and light frame agility."
    }
]

def resolve_construct_companion(master_int_mod: int, level: int = 1) -> PartnerCreatureData:
    prof_bonus = 2 + level
    mod = random.choice(CONSTRUCT_MODIFICATIONS)
    
    # Base stats for construct innovation
    str_mod = 3
    dex_mod = 1
    con_mod = 2
    wis_mod = 1

    extra_ac = 1 if mod["name"] == "Hardened Plating" else 0
    extra_speed = "40 ft" if mod["name"] == "Accelerated Mobility" else "30 ft"

    ac = 10 + dex_mod + prof_bonus + 2 + extra_ac # Starts with trained unarmored + frame bonus
    hp = 10 + (level * (8 + con_mod))

    fort = prof_bonus + con_mod
    ref = prof_bonus + dex_mod
    will = prof_bonus + wis_mod
    perception = prof_bonus + wis_mod

    atk_bonus = prof_bonus + str_mod
    if level >= 4:
        atk_bonus += 1

    strikes = [
        Strike(
            name="Pounding Slam",
            attack_bonus=atk_bonus,
            map_second=atk_bonus - 5,
            map_third=atk_bonus - 10,
            damage_dice=f"1d8+{str_mod}",
            damage_type="Bludgeoning",
            traits=["Construct", "Unarmed", "Overdrive Compatible"]
        ),
        Strike(
            name="Gear Cleaver",
            attack_bonus=atk_bonus,
            map_second=atk_bonus - 4,
            map_third=atk_bonus - 8,
            damage_dice=f"1d6+{str_mod}",
            damage_type="Slashing",
            traits=["Agile", "Construct", "Unarmed"]
        )
    ]

    primary_text = f"Construct Immunities: Bleed, Death effects, Paralyzed, Poison, Sleep. Initial Modification: {mod['name']} ({mod['effect']})"
    secondary_text = "Overdrive Synergy: When you successfully roll Overdrive, your construct adds your Overdrive bonus damage to all its melee Strikes."

    return PartnerCreatureData(
        name=f"Clockwork Chassis Mk-{level}",
        creature_type="Construct Innovation",
        sub_type="Construct Partner",
        stage="Custom Chassis",
        size="Medium",
        speed=extra_speed,
        ac=ac,
        hp=hp,
        fortitude=fort,
        reflex=ref,
        will=will,
        perception=perception,
        strikes=strikes,
        primary_ability=primary_text,
        secondary_ability=secondary_text,
        traits=["Construct", "Innovation", "Mindless"]
    )


# ==========================================
# 2. UNDEAD COMPANIONS (UNDEAD MASTER)
# ==========================================
UNDEAD_SPECIES: Dict[str, Dict[str, Any]] = {
    "skeleton": {
        "name": "Skeleton Sentinel",
        "speed": "30 ft",
        "base_hp": 6,
        "con_mod": 2,
        "str_mod": 2,
        "dex_mod": 3,
        "wis_mod": 1,
        "strikes": [
            {
                "name": "Bone Claw",
                "dice": "1d6",
                "type": "Slashing",
                "traits": ["Agile", "Finesse", "Unarmed"],
                "finesse": True
            },
            {
                "name": "Bone Scythe",
                "dice": "1d8",
                "type": "Slashing",
                "traits": ["Deadly d8", "Unarmed"],
                "finesse": False
            }
        ],
        "support": "Your skeleton rattles intimidatingly. Foes hit by your attacks within its reach become frightened 1."
    },
    "ghost": {
        "name": "Phantom Shade",
        "speed": "fly 30 ft",
        "base_hp": 4,
        "con_mod": 1,
        "str_mod": 1,
        "dex_mod": 3,
        "wis_mod": 2,
        "strikes": [
            {
                "name": "Grave Touch",
                "dice": "1d6",
                "type": "Void",
                "traits": ["Agile", "Finesse", "Magical", "Unarmed"],
                "finesse": True
            }
        ],
        "support": "Your phantom chills the enemy's heart. Foes hit within reach take 1d4 void damage and take -1 to saving throws for 1 round."
    },
    "zombie": {
        "name": "Hulking Zombie",
        "speed": "20 ft",
        "base_hp": 10,
        "con_mod": 3,
        "str_mod": 3,
        "dex_mod": 0,
        "wis_mod": 0,
        "strikes": [
            {
                "name": "Rotting Slam",
                "dice": "1d8",
                "type": "Bludgeoning",
                "traits": ["Grab", "Unarmed"],
                "finesse": False
            }
        ],
        "support": "Your zombie drags foes down. Targets hit within its reach become off-guard and take -10 ft penalty to Speeds."
    }
}

UNDEAD_NAMES = ["Grimjaw", "Rattle", "Sepulcher", "Dusk", "Harrow", "Marrow", "Vesper"]

def resolve_undead_companion(level: int = 1) -> PartnerCreatureData:
    prof_bonus = 2 + level
    key = random.choice(list(UNDEAD_SPECIES.keys()))
    cfg = UNDEAD_SPECIES[key]
    name = random.choice(UNDEAD_NAMES)

    con_mod = cfg["con_mod"]
    str_mod = cfg["str_mod"]
    dex_mod = cfg["dex_mod"]
    wis_mod = cfg["wis_mod"]

    ac = 10 + dex_mod + prof_bonus + 2
    hp = cfg["base_hp"] + (level * (6 + con_mod))

    fort = prof_bonus + con_mod
    ref = prof_bonus + dex_mod
    will = prof_bonus + wis_mod
    perception = prof_bonus + wis_mod

    strikes: List[Strike] = []
    for st in cfg["strikes"]:
        is_fin = st.get("finesse", False)
        atk_mod = max(str_mod, dex_mod) if is_fin else str_mod
        atk_bonus = prof_bonus + atk_mod
        if level >= 4:
            atk_bonus += 1

        is_agile = "Agile" in st.get("traits", [])
        strikes.append(Strike(
            name=st["name"],
            attack_bonus=atk_bonus,
            map_second=atk_bonus - (4 if is_agile else 5),
            map_third=atk_bonus - (8 if is_agile else 10),
            damage_dice=f"{st['dice']}+{str_mod}",
            damage_type=st["type"],
            traits=st.get("traits", [])
        ))

    primary_text = f"Undead Trait & Void Healing: Harmed by vitality, healed by void effects. Immune to death effects, disease, paralyzed, poison, and unconscious."
    secondary_text = f"Support Benefit: {cfg['support']}"

    return PartnerCreatureData(
        name=f"{name} ({cfg['name']})",
        creature_type="Undead Companion",
        sub_type=cfg["name"],
        stage="Thrall of Bone & Void",
        size="Medium",
        speed=cfg["speed"],
        ac=ac,
        hp=hp,
        fortitude=fort,
        reflex=ref,
        will=will,
        perception=perception,
        strikes=strikes,
        primary_ability=primary_text,
        secondary_ability=secondary_text,
        traits=["Undead", "Void Healing", "Minion"]
    )
