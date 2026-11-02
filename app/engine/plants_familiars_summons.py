import random
from typing import Dict, Any, List, Optional
from app.engine.models import PartnerCreatureData, Strike

# =====================================================================
# 1. PLANT COMPANIONS
# =====================================================================
PLANT_SPECIES: Dict[str, Dict[str, Any]] = {
    "arboreal": {
        "name": "Arboreal Sapling",
        "speed": "25 ft",
        "base_hp": 8,
        "con_mod": 3,
        "str_mod": 3,
        "dex_mod": 0,
        "wis_mod": 2,
        "strikes": [
            {
                "name": "Branch Slam",
                "dice": "1d8",
                "type": "Bludgeoning",
                "traits": ["Reach 10 ft", "Unarmed"],
                "finesse": False
            }
        ],
        "support": "Roots burst from the ground around your target. Foes hit by your attacks within reach treat the area around the sapling as difficult terrain.",
        "maneuver": "Root Grab: On a critical hit with Branch Slam, the sapling immobilizes the target with tangled roots (DC = Fortitude DC)."
    },
    "carnivorous": {
        "name": "Carnivorous Flytrap",
        "speed": "20 ft",
        "base_hp": 6,
        "con_mod": 2,
        "str_mod": 2,
        "dex_mod": 3,
        "wis_mod": 1,
        "strikes": [
            {
                "name": "Snapping Maw",
                "dice": "1d8",
                "type": "Piercing",
                "traits": ["Grab", "Reach 10 ft", "Unarmed"],
                "finesse": True
            },
            {
                "name": "Acid Thorn",
                "dice": "1d4",
                "type": "Acid",
                "traits": ["Agile", "Range 30 ft", "Unarmed"],
                "finesse": True
            }
        ],
        "support": "Your flytrap leaks digestive bile. Targets hit within reach take 1d4 persistent acid damage.",
        "maneuver": "Engulfing Snap: The flytrap makes a Snapping Maw Strike. If it hits an off-guard foe, it automatically initiates a Grab without spending an extra action."
    }
}

PLANT_NAMES = ["Brambleheart", "Verdant", "Thornbark", "Spore", "Gloomweed", "Mossback"]

def resolve_plant_companion(level: int = 1) -> PartnerCreatureData:
    prof_bonus = 2 + level
    key = random.choice(list(PLANT_SPECIES.keys()))
    cfg = PLANT_SPECIES[key]
    name = random.choice(PLANT_NAMES)

    str_mod = cfg["str_mod"]
    dex_mod = cfg["dex_mod"]
    con_mod = cfg["con_mod"]
    wis_mod = cfg["wis_mod"]

    is_mature = level >= 4
    stage = "Mature Plant Companion" if is_mature else "Young Plant Companion"
    size = "Large" if (is_mature and key == "arboreal") else "Medium"

    hp = cfg["base_hp"] + (level * (6 + con_mod)) + (10 if is_mature else 0)
    ac = 10 + dex_mod + prof_bonus + 2 + (1 if is_mature else 0)

    fort = prof_bonus + con_mod + (1 if is_mature else 0)
    ref = prof_bonus + dex_mod + (1 if is_mature else 0)
    will = prof_bonus + wis_mod + (1 if is_mature else 0)
    perception = prof_bonus + wis_mod

    strikes: List[Strike] = []
    for st in cfg["strikes"]:
        is_fin = st.get("finesse", False)
        atk_mod = max(str_mod, dex_mod) if is_fin else str_mod
        atk_bonus = prof_bonus + atk_mod + (1 if is_mature else 0)
        dmg_bonus = str_mod + (2 if is_mature else 0)

        is_agile = "Agile" in st.get("traits", [])
        strikes.append(Strike(
            name=st["name"],
            attack_bonus=atk_bonus,
            map_second=atk_bonus - (4 if is_agile else 5),
            map_third=atk_bonus - (8 if is_agile else 10),
            damage_dice=f"{st['dice']}+{dmg_bonus}",
            damage_type=st["type"],
            traits=st.get("traits", [])
        ))

    primary_text = f"Plant Traits: Immune to bleed and sleep. Weakness to fire & slashing (3), Resistance to acid & piercing (3). Natural Camouflage in foliage."
    secondary_text = f"Support Benefit: {cfg['support']} | Special Maneuver: {cfg['maneuver']}"

    return PartnerCreatureData(
        name=f"{name} ({cfg['name']})",
        creature_type="Plant Companion",
        sub_type=cfg["name"],
        stage=stage,
        size=size,
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
        traits=["Plant", "Minion"]
    )


# =====================================================================
# 2. SPECIFIC FAMILIARS (LEVEL 4+)
# =====================================================================
SPECIFIC_FAMILIARS: Dict[str, Dict[str, Any]] = {
    "imp": {
        "name": "Imp Familiar",
        "size": "Tiny",
        "speed": "20 ft, fly 30 ft",
        "innate_spells": "Innate Spells: At-will Detect Magic; 1/day Invisibility (self only).",
        "resistances": "Resistance 5 to fire; immune to poison.",
        "granted_abilities": ["Flier", "Speech", "Darkvision", "Cantrip Connection"],
        "flavor": "A barbed fiendish advisor constantly whispering deceitful shortcuts."
    },
    "faerie dragon": {
        "name": "Faerie Dragon",
        "size": "Tiny",
        "speed": "15 ft, fly 40 ft",
        "innate_spells": "Innate Spells: Euphoric Breath (1/day 10-ft cone, stupefied 2 on failed Fortitude save); 1/day Ghost Sound.",
        "resistances": "Darkvision, immune to sleep and paralyzed effects.",
        "granted_abilities": ["Flier", "Speech", "Touch Telepathy", "Spell Delivery"],
        "flavor": "An iridescent butterfly-winged dragon fond of subtle mischief and sweet nectar."
    },
    "nosoi": {
        "name": "Nosoi Psychopomp",
        "size": "Tiny",
        "speed": "15 ft, fly 35 ft",
        "innate_spells": "Innate Spells: Haunting Melody (1 action, fascinates or calms spirits); at-will Read Aura.",
        "resistances": "Immune to death effects and disease; resistance 3 to void damage.",
        "granted_abilities": ["Flier", "Speech", "Spirit Sight", "Restorative Familiar"],
        "flavor": "A masked raven-like psychopomp that scribes records of wandering souls."
    },
    "dweomercat cub": {
        "name": "Dweomercat Cub",
        "size": "Tiny",
        "speed": "30 ft, climb 20 ft",
        "innate_spells": "Innate Reaction: Dweomer Leap (Trigger: Master casts a spell; Reaction: Teleport 10 ft into master space).",
        "resistances": "+1 status bonus to saving throws against magical effects.",
        "granted_abilities": ["Darkvision", "Fast Movement", "Share Senses", "Cantrip Connection"],
        "flavor": "A kitten with shifting indigo fur that crackles with ambient arcane static."
    }
}

SPECIFIC_FAMILIAR_NAMES = ["Malakor", "Titania", "Quill", "Whisper", "Vesper", "Singe", "Zephyr"]

def resolve_specific_familiar(
    master_ac: int,
    master_fort: int,
    master_ref: int,
    master_will: int,
    master_perception: int,
    level: int = 4
) -> PartnerCreatureData:
    key = random.choice(list(SPECIFIC_FAMILIARS.keys()))
    cfg = SPECIFIC_FAMILIARS[key]
    name = random.choice(SPECIFIC_FAMILIAR_NAMES)

    hp = 5 * level
    abilities_str = ", ".join(cfg["granted_abilities"])

    primary_text = f"Specific Familiar Traits: {abilities_str}. {cfg['resistances']} {cfg['flavor']}"
    secondary_text = f"{cfg['innate_spells']}"

    return PartnerCreatureData(
        name=f"{name} ({cfg['name']})",
        creature_type="Specific Familiar",
        sub_type=cfg["name"],
        stage=f"Rank {max(1, level // 2)} Conduit",
        size=cfg["size"],
        speed=cfg["speed"],
        ac=master_ac,
        hp=hp,
        fortitude=master_fort,
        reflex=master_ref,
        will=master_will,
        perception=master_perception,
        strikes=[],
        primary_ability=primary_text,
        secondary_ability=secondary_text,
        traits=["Familiar", "Magical", "Specific Familiar", "Minion"]
    )


# =====================================================================
# 3. SUMMON SNAPSHOTS (SPELL-BASED MINIONS)
# =====================================================================
SUMMON_SNAPSHOTS: Dict[str, Dict[int, Dict[str, Any]]] = {
    "animate dead": {
        1: {
            "name": "Skeleton Guard",
            "size": "Medium",
            "speed": "25 ft",
            "ac": 16,
            "hp": 9,
            "fort": 4,
            "ref": 7,
            "will": 4,
            "perception": 2,
            "strike_name": "Scimitar",
            "strike_dice": "1d6+2",
            "strike_type": "Slashing",
            "traits": ["Undead", "Mindless"],
            "features": "Void healing; immune to bleed, death effects, disease, paralyzed, poison, unconscious. Cold resistance 3."
        },
        2: {
            "name": "Zombie Brute",
            "size": "Large",
            "speed": "25 ft",
            "ac": 15,
            "hp": 40,
            "fort": 8,
            "ref": 3,
            "will": 5,
            "perception": 3,
            "strike_name": "Fist (Grab)",
            "strike_dice": "1d12+4",
            "strike_type": "Bludgeoning",
            "traits": ["Undead", "Mindless"],
            "features": "Void healing; immune to death effects, disease, poison. Slashing weakness 5. Permanently Slowed 1."
        }
    },
    "summon animal": {
        1: {
            "name": "Hunting Wolf",
            "size": "Medium",
            "speed": "35 ft",
            "ac": 15,
            "hp": 20,
            "fort": 7,
            "ref": 7,
            "will": 4,
            "perception": 7,
            "strike_name": "Jaws (Trip)",
            "strike_dice": "1d6+2",
            "strike_type": "Piercing",
            "traits": ["Animal"],
            "features": "Scent (imprecise 30 ft), Pack Attack (deals extra 1d4 damage to targets in reach of 2 allies)."
        },
        2: {
            "name": "Grizzly Mauler",
            "size": "Large",
            "speed": "35 ft",
            "ac": 18,
            "hp": 45,
            "fort": 11,
            "ref": 8,
            "will": 6,
            "perception": 8,
            "strike_name": "Claw (Agile)",
            "strike_dice": "1d8+5",
            "strike_type": "Slashing",
            "traits": ["Animal"],
            "features": "Maul: If the bear hits with a Strike, it can spend 1 action to automatically Grab the target."
        }
    },
    "summon elemental": {
        1: {
            "name": "Cinder Wisp (Fire)",
            "size": "Small",
            "speed": "fly 40 ft",
            "ac": 16,
            "hp": 15,
            "fort": 5,
            "ref": 8,
            "will": 4,
            "perception": 5,
            "strike_name": "Flame Tendril",
            "strike_dice": "1d4+1 plus 1d4 fire",
            "strike_type": "Fire",
            "traits": ["Elemental", "Fire"],
            "features": "Fire immunity; cold weakness 5. Heated Body: Creatures touching the wisp take 1d4 fire damage."
        },
        2: {
            "name": "Living Geode (Earth)",
            "size": "Medium",
            "speed": "20 ft, burrow 20 ft",
            "ac": 19,
            "hp": 38,
            "fort": 10,
            "ref": 5,
            "will": 6,
            "perception": 6,
            "strike_name": "Stone Fist",
            "strike_dice": "1d10+4",
            "strike_type": "Bludgeoning",
            "traits": ["Earth", "Elemental"],
            "features": "Tremorsense 30 ft (imprecise). Earth Glide: Can burrow through stone without disturbing material."
        }
    }
}

def resolve_summon_snapshot(spell_name: str, spell_rank: int = 1) -> PartnerCreatureData:
    sn_key = "summon animal"
    s_lower = spell_name.lower()
    if "animate dead" in s_lower or "undead" in s_lower:
        sn_key = "animate dead"
    elif "elemental" in s_lower:
        sn_key = "summon elemental"

    tier = min(2, max(1, spell_rank))
    cfg = SUMMON_SNAPSHOTS[sn_key][tier]

    strikes = [
        Strike(
            name=cfg["strike_name"],
            attack_bonus=cfg["ac"] - 7,
            map_second=cfg["ac"] - 12,
            map_third=cfg["ac"] - 17,
            damage_dice=cfg["strike_dice"],
            damage_type=cfg["strike_type"],
            traits=["Magical", "Summoned"]
        )
    ]

    primary_text = f"Summoned Minion: Duration Sustained up to 1 minute. Requires 1 Action from master each round to Command (grants minion 2 actions)."
    secondary_text = f"Features & Immunities: {cfg['features']}"

    return PartnerCreatureData(
        name=f"{cfg['name']} (Rank {tier} Summon)",
        creature_type="Summon Snapshot",
        sub_type=cfg["name"],
        stage=f"Rank {tier} Spell Minion",
        size=cfg["size"],
        speed=cfg["speed"],
        ac=cfg["ac"],
        hp=cfg["hp"],
        fortitude=cfg["fort"],
        reflex=cfg["ref"],
        will=cfg["will"],
        perception=cfg["perception"],
        strikes=strikes,
        primary_ability=primary_text,
        secondary_ability=secondary_text,
        traits=cfg["traits"] + ["Minion", "Summoned"]
    )
