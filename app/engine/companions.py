import random
from typing import Dict, Any, List, Optional
from app.engine.models import AnimalCompanionData, Strike, FeatSummary

COMPANION_NAMES = [
    "Fang", "Shadow", "Ghost", "Bruno", "Copper", "Grizz",
    "Storm", "Zephyr", "Rowan", "Onyx", "Talon", "Bramble"
]

COMPANION_SPECIES: Dict[str, Dict[str, Any]] = {
    "wolf": {
        "species": "Wolf",
        "young_size": "Small",
        "mature_size": "Medium",
        "speed": "40 ft",
        "base_hp": 6,
        "con_mod": 2,
        "str_mod": 2,
        "dex_mod": 3,
        "wis_mod": 1,
        "strikes": [
            {
                "name": "Jaws",
                "dice": "1d8",
                "type": "Piercing",
                "traits": ["Trip", "Unarmed"],
                "finesse": False
            }
        ],
        "support_benefit": "Your wolf tears at your foe's tendons. If you hit a creature in the wolf's reach, that creature is flat-footed against your attacks until the start of your next turn.",
        "advanced_maneuver": "Knockdown: When the wolf hits with a Jaws strike, it attempts an Athletics check to Trip the target without triggering reactions."
    },
    "bear": {
        "species": "Bear",
        "young_size": "Small",
        "mature_size": "Medium",
        "speed": "35 ft",
        "base_hp": 8,
        "con_mod": 3,
        "str_mod": 3,
        "dex_mod": 2,
        "wis_mod": 1,
        "strikes": [
            {
                "name": "Jaws",
                "dice": "1d8",
                "type": "Piercing",
                "traits": ["Unarmed"],
                "finesse": False
            },
            {
                "name": "Claw",
                "dice": "1d6",
                "type": "Slashing",
                "traits": ["Agile", "Unarmed"],
                "finesse": False
            }
        ],
        "support_benefit": "Your bear mauls your enemies. Whenever you hit a creature in your bear's reach, the bear deals 1d8 slashing damage to that creature.",
        "advanced_maneuver": "Bear Hug: If the bear hits with two consecutive claw strikes, it grabs the target automatically."
    },
    "bird": {
        "species": "Bird (Raptor)",
        "young_size": "Small",
        "mature_size": "Medium",
        "speed": "10 ft, fly 60 ft",
        "base_hp": 4,
        "con_mod": 1,
        "str_mod": 1,
        "dex_mod": 3,
        "wis_mod": 2,
        "strikes": [
            {
                "name": "Jaws (Beak)",
                "dice": "1d6",
                "type": "Piercing",
                "traits": ["Finesse", "Unarmed"],
                "finesse": True
            },
            {
                "name": "Talon",
                "dice": "1d4",
                "type": "Slashing",
                "traits": ["Agile", "Finesse", "Unarmed"],
                "finesse": True
            }
        ],
        "support_benefit": "Your bird swoops at eyes and vitals. Targets you hit within the bird's reach become clumsy 1 and take 1d4 bleed damage.",
        "advanced_maneuver": "Flyby Attack: The bird Strides or Flies, makes one Strike at any point during movement, and continues moving."
    },
    "cat": {
        "species": "Cat (Leopard)",
        "young_size": "Small",
        "mature_size": "Medium",
        "speed": "35 ft",
        "base_hp": 4,
        "con_mod": 1,
        "str_mod": 2,
        "dex_mod": 3,
        "wis_mod": 1,
        "strikes": [
            {
                "name": "Jaws",
                "dice": "1d6",
                "type": "Piercing",
                "traits": ["Finesse", "Unarmed"],
                "finesse": True
            },
            {
                "name": "Claw",
                "dice": "1d4",
                "type": "Slashing",
                "traits": ["Agile", "Finesse", "Unarmed"],
                "finesse": True
            }
        ],
        "support_benefit": "Your cat stalks with lethal focus. If you hit a creature within the cat's reach, that target is flat-footed against your companion's attacks.",
        "advanced_maneuver": "Pounce: The cat Strides and then makes a Strike; if it was hidden, it deals an extra 1d6 precision damage."
    },
    "badger": {
        "species": "Badger",
        "young_size": "Small",
        "mature_size": "Medium",
        "speed": "25 ft, burrow 10 ft",
        "base_hp": 8,
        "con_mod": 2,
        "str_mod": 2,
        "dex_mod": 2,
        "wis_mod": 2,
        "strikes": [
            {
                "name": "Bite",
                "dice": "1d8",
                "type": "Piercing",
                "traits": ["Unarmed"],
                "finesse": False
            },
            {
                "name": "Claw",
                "dice": "1d6",
                "type": "Slashing",
                "traits": ["Agile", "Unarmed"],
                "finesse": False
            }
        ],
        "support_benefit": "Your badger snarls viciously. Enemies within the badger's reach take a -1 circumstance penalty to attack rolls.",
        "advanced_maneuver": "Badger Rage: The badger gains temporary HP and a status bonus to melee damage rolls."
    }
}

def resolve_companion(
    class_name: str,
    feats: List[FeatSummary],
    archetype: Optional[str],
    level: int = 1
) -> Optional[AnimalCompanionData]:
    # Determine if character qualifies for a companion
    cls_lower = class_name.lower()
    feat_names = [f.name.lower() for f in feats]
    has_companion_feat = any("animal companion" in fn or "beastmaster" in fn for fn in feat_names)
    is_beastmaster = archetype and "beastmaster" in archetype.lower()

    if not (has_companion_feat or is_beastmaster or (cls_lower == "druid" and "order: animal" in " ".join(feat_names))):
        return None

    # Pick a companion species
    species_key = random.choice(list(COMPANION_SPECIES.keys()))
    cfg = COMPANION_SPECIES[species_key]

    is_mature = level >= 4 or any("mature" in fn for fn in feat_names)
    stage = "Mature" if is_mature else "Young"
    size = cfg["mature_size"] if is_mature else cfg["young_size"]

    # Proficiency bonus: Trained = 2 + master's level
    prof_bonus = 2 + level
    con_mod = cfg["con_mod"] + (1 if is_mature else 0)
    str_mod = cfg["str_mod"] + (1 if is_mature else 0)
    dex_mod = cfg["dex_mod"] + (1 if is_mature else 0)
    wis_mod = cfg["wis_mod"] + (1 if is_mature else 0)

    # HP calculation: base_hp + level * (6 + con) + (+10 if mature)
    hp = cfg["base_hp"] + (level * (6 + con_mod)) + (10 if is_mature else 0)
    ac = 10 + dex_mod + prof_bonus + (1 if is_mature else 0)

    fort_save = prof_bonus + con_mod + (1 if is_mature else 0)
    ref_save = prof_bonus + dex_mod + (1 if is_mature else 0)
    will_save = prof_bonus + wis_mod + (1 if is_mature else 0)
    perception = prof_bonus + wis_mod

    # Build Companion Strikes
    companion_strikes: List[Strike] = []
    for st in cfg["strikes"]:
        is_fin = st.get("finesse", False)
        atk_mod = max(str_mod, dex_mod) if is_fin else str_mod
        atk_bonus = prof_bonus + atk_mod

        dmg_bonus = str_mod + (2 if is_mature else 0)
        dmg_str = f"{st['dice']}+{dmg_bonus}" if dmg_bonus > 0 else st['dice']

        is_agile = "Agile" in st.get("traits", [])
        map_second = atk_bonus - (4 if is_agile else 5)
        map_third = atk_bonus - (8 if is_agile else 10)

        companion_strikes.append(Strike(
            name=st["name"],
            attack_bonus=atk_bonus,
            map_second=map_second,
            map_third=map_third,
            damage_dice=dmg_str,
            damage_type=st["type"],
            traits=st.get("traits", [])
        ))

    c_name = random.choice(COMPANION_NAMES)

    return AnimalCompanionData(
        name=f"{c_name} the {cfg['species']}",
        species=cfg["species"],
        stage=stage,
        size=size,
        speed=cfg["speed"],
        ac=ac,
        hp=hp,
        fortitude=fort_save,
        reflex=ref_save,
        will=will_save,
        perception=perception,
        strikes=companion_strikes,
        support_benefit=cfg["support_benefit"],
        advanced_maneuver=cfg.get("advanced_maneuver") if is_mature else None
    )
