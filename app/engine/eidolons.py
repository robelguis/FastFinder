import random
from typing import Dict, Any, List, Optional
from app.engine.models import PartnerCreatureData, Strike

EIDOLON_CATALOG: Dict[str, Dict[str, Any]] = {
    "fey": {
        "name_options": ["Puck", "Titania's Thorn", "Bramble", "Gossamer", "Briar"],
        "sub_type": "Fey Eidolon",
        "tradition": "Primal",
        "size": "Small or Medium",
        "speed": "25 ft",
        "str_mod": 1,
        "dex_mod": 4,
        "con_mod": 2,
        "int_mod": 1,
        "wis_mod": 0,
        "cha_mod": 2,
        "strikes": [
            {"name": "Fey Claws", "dice": "1d6", "type": "Slashing", "traits": ["Agile", "Finesse", "Primal", "Unarmed"], "finesse": True},
            {"name": "Sprite Lash", "dice": "1d6", "type": "Piercing", "traits": ["Finesse", "Primal", "Unarmed"], "finesse": True}
        ],
        "primary_ability": "Act Together: You and your eidolon share a tactical bond. Either you or your eidolon takes an action, and the other simultaneously takes a 1-to-3 action activity.",
        "secondary_ability": "Fey Glamour: The eidolon can manipulate primal illusions and trickery to baffle foes.",
        "traits": ["Fey", "Primal"]
    },
    "plant": {
        "name_options": ["Oakheart", "Verdant Reach", "Rootstrider", "Briarhorn", "Thornweaver"],
        "sub_type": "Plant Eidolon",
        "tradition": "Primal",
        "size": "Medium or Large",
        "speed": "25 ft",
        "str_mod": 4,
        "dex_mod": 1,
        "con_mod": 3,
        "int_mod": -1,
        "wis_mod": 2,
        "cha_mod": 0,
        "strikes": [
            {"name": "Tendril", "dice": "1d8", "type": "Bludgeoning", "traits": ["Reach", "Unarmed"], "finesse": False},
            {"name": "Branch", "dice": "1d6", "type": "Bludgeoning", "traits": ["Agile", "Unarmed"], "finesse": False}
        ],
        "primary_ability": "Act Together: Either you or your eidolon takes an action, and the other simultaneously takes an activity.",
        "secondary_ability": "Verdant Reach: Your plant eidolon extends its tendrils, increasing reach with all Strikes by 5 feet.",
        "traits": ["Plant", "Primal"]
    },
    "construct": {
        "name_options": ["Aegis-01", "Ironclad", "Clockwork Vanguard", "Gilded Sentinel", "Cogheart"],
        "sub_type": "Construct Eidolon",
        "tradition": "Arcane",
        "size": "Medium",
        "speed": "25 ft",
        "str_mod": 4,
        "dex_mod": 2,
        "con_mod": 3,
        "int_mod": -1,
        "wis_mod": 1,
        "cha_mod": -1,
        "strikes": [
            {"name": "Iron Fist", "dice": "1d8", "type": "Bludgeoning", "traits": ["Unarmed"], "finesse": False},
            {"name": "Piston Strike", "dice": "1d6", "type": "Bludgeoning", "traits": ["Agile", "Unarmed"], "finesse": False}
        ],
        "primary_ability": "Act Together: Either you or your eidolon takes an action, and the other simultaneously takes an activity.",
        "secondary_ability": "Reconfigure: The construct can adapt its physical form to gain resistances or alternative damage types.",
        "traits": ["Construct", "Arcane"]
    },
    "elemental": {
        "name_options": ["Cinder", "Torrent", "Gale", "Quake", "Vortex"],
        "sub_type": "Elemental Eidolon",
        "tradition": "Primal",
        "size": "Medium",
        "speed": "25 ft",
        "str_mod": 3,
        "dex_mod": 3,
        "con_mod": 3,
        "int_mod": 0,
        "wis_mod": 0,
        "cha_mod": 0,
        "strikes": [
            {"name": "Elemental Blast", "dice": "1d8", "type": "Bludgeoning, Piercing, or Slashing (plus 1 Energy)", "traits": ["Unarmed"], "finesse": False},
            {"name": "Lashing Core", "dice": "1d6", "type": "Energy", "traits": ["Agile", "Finesse", "Unarmed"], "finesse": True}
        ],
        "primary_ability": "Act Together: Either you or your eidolon takes an action, and the other simultaneously takes an activity.",
        "secondary_ability": "Elemental Burst: The eidolon releases a wave of primal kinetic force damaging adjacent targets.",
        "traits": ["Elemental", "Primal"]
    },
    "demon": {
        "name_options": ["Gorefeast", "Abyssal Maw", "Krag'gath", "Blightfang", "Ravage"],
        "sub_type": "Demon Eidolon",
        "tradition": "Divine",
        "size": "Medium",
        "speed": "25 ft",
        "str_mod": 4,
        "dex_mod": 1,
        "con_mod": 3,
        "int_mod": -1,
        "wis_mod": 0,
        "cha_mod": 2,
        "strikes": [
            {"name": "Jaws", "dice": "1d8", "type": "Piercing (plus 1 Evil)", "traits": ["Unholy", "Unarmed"], "finesse": False},
            {"name": "Claw", "dice": "1d6", "type": "Slashing", "traits": ["Agile", "Unholy", "Unarmed"], "finesse": True}
        ],
        "primary_ability": "Act Together: Either you or your eidolon takes an action, and the other simultaneously takes an activity.",
        "secondary_ability": "Abyssal Incursion: The demon inflicts weakness to unholy damage on strikes.",
        "traits": ["Fiend", "Demon", "Divine", "Unholy"]
    },
    "undead": {
        "name_options": ["Gravechill", "Ossuary", "Marrowthief", "Duskling", "Wraithwalker"],
        "sub_type": "Undead Eidolon",
        "tradition": "Divine",
        "size": "Medium",
        "speed": "25 ft",
        "str_mod": 4,
        "dex_mod": 2,
        "con_mod": 3,
        "int_mod": -1,
        "wis_mod": 1,
        "cha_mod": 0,
        "strikes": [
            {"name": "Grave Fist", "dice": "1d8", "type": "Bludgeoning (plus 1 Void)", "traits": ["Void", "Unarmed"], "finesse": False},
            {"name": "Bone Claw", "dice": "1d6", "type": "Slashing", "traits": ["Agile", "Finesse", "Unarmed"], "finesse": True}
        ],
        "primary_ability": "Act Together: Either you or your eidolon takes an action, and the other simultaneously takes an activity.",
        "secondary_ability": "Negative Healing: The undead eidolon is healed by void energy and harmed by vitality energy.",
        "traits": ["Undead", "Divine"]
    },
    "psychopomp": {
        "name_options": ["Duskwarden", "Graveguide", "Morrigna's Beak", "Threshold", "Anubis-Marked"],
        "sub_type": "Psychopomp Eidolon",
        "tradition": "Divine",
        "size": "Medium",
        "speed": "25 ft",
        "str_mod": 3,
        "dex_mod": 2,
        "con_mod": 3,
        "int_mod": 0,
        "wis_mod": 2,
        "cha_mod": 0,
        "strikes": [
            {"name": "Staff Strike", "dice": "1d8", "type": "Bludgeoning (Spirit)", "traits": ["Spirit", "Unarmed"], "finesse": False},
            {"name": "Mask Claw", "dice": "1d6", "type": "Slashing", "traits": ["Agile", "Finesse", "Unarmed"], "finesse": True}
        ],
        "primary_ability": "Act Together: Either you or your eidolon takes an action, and the other simultaneously takes an activity.",
        "secondary_ability": "Spirit Touch: The psychopomp's strikes ghost-touch ethereal targets and deal spirit damage.",
        "traits": ["Monitor", "Psychopomp", "Divine"]
    },

    "dragon": {
        "name_options": ["Ignis", "Vermithrax", "Glintwing", "Pyroth", "Azurewing"],
        "sub_type": "Dragon Eidolon",
        "tradition": "Arcane",
        "size": "Medium",
        "speed": "25 ft",
        "str_mod": 4,
        "dex_mod": 1,
        "con_mod": 3,
        "int_mod": 0,
        "wis_mod": 1,
        "cha_mod": 0,
        "strikes": [
            {
                "name": "Jaws",
                "dice": "1d8",
                "type": "Piercing (plus 1 Energy)",
                "traits": ["Unarmed", "Arcane"],
                "finesse": False
            },
            {
                "name": "Claw",
                "dice": "1d6",
                "type": "Slashing",
                "traits": ["Agile", "Finesse", "Unarmed"],
                "finesse": True
            }
        ],
        "primary_ability": "Act Together: You and your eidolon share a tactical bond. Either you or your eidolon takes an action, and the other simultaneously takes a 1-to-3 action activity, using 1 fewer action from your shared pool.",
        "secondary_ability": "Draconic Breath: The dragon exhales a 30-foot cone or 60-foot line of elemental energy dealing 1d6 damage per level (basic Reflex save).",
        "traits": ["Dragon", "Eidolon", "Magical"]
    },
    "anger phantom": {
        "name_options": ["Wrath", "Vengeance", "Malice", "Scourge", "Torment"],
        "sub_type": "Anger Phantom Eidolon",
        "tradition": "Occult",
        "size": "Medium",
        "speed": "25 ft",
        "str_mod": 4,
        "dex_mod": 2,
        "con_mod": 2,
        "int_mod": -1,
        "wis_mod": 1,
        "cha_mod": 1,
        "strikes": [
            {
                "name": "Fist of Fury",
                "dice": "1d8",
                "type": "Bludgeoning",
                "traits": ["Forceful", "Unarmed"],
                "finesse": False
            },
            {
                "name": "Spiteful Tendril",
                "dice": "1d6",
                "type": "Slashing",
                "traits": ["Agile", "Reach 10 ft", "Unarmed"],
                "finesse": False
            }
        ],
        "primary_ability": "Act Together: Either you or your eidolon takes an action, and the other simultaneously takes an activity, operating in seamless emotional synergy.",
        "secondary_ability": "Furious Strike: The anger phantom channels pure rage into an attack, adding status bonus damage equal to its Constitution modifier.",
        "traits": ["Eidolon", "Emotion", "Mental", "Phantom"]
    },
    "beast": {
        "name_options": ["Apex", "Primal Roar", "Ursoc", "Savage", "Gorefang"],
        "sub_type": "Beast Eidolon",
        "tradition": "Primal",
        "size": "Medium",
        "speed": "35 ft",
        "str_mod": 4,
        "dex_mod": 2,
        "con_mod": 2,
        "int_mod": -2,
        "wis_mod": 1,
        "cha_mod": 0,
        "strikes": [
            {
                "name": "Predator Jaws",
                "dice": "1d8",
                "type": "Piercing",
                "traits": ["Trip", "Unarmed"],
                "finesse": False
            },
            {
                "name": "Rending Claw",
                "dice": "1d6",
                "type": "Slashing",
                "traits": ["Agile", "Finesse", "Unarmed"],
                "finesse": True
            }
        ],
        "primary_ability": "Act Together: Either you or your eidolon takes an action, and the other simultaneously takes an activity.",
        "secondary_ability": "Beast's Charge: The beast Strides twice and makes a Strike at the end of the movement with a +1 circumstance bonus to the attack roll.",
        "traits": ["Beast", "Eidolon", "Primal"]
    },
    "devotion phantom": {
        "name_options": ["Guardian", "Aegis", "Valor", "Watcher", "Seraph"],
        "sub_type": "Devotion Phantom Eidolon",
        "tradition": "Divine",
        "size": "Medium",
        "speed": "25 ft",
        "str_mod": 3,
        "dex_mod": 3,
        "con_mod": 2,
        "int_mod": 0,
        "wis_mod": 1,
        "cha_mod": 0,
        "strikes": [
            {
                "name": "Holy Glaive",
                "dice": "1d8",
                "type": "Slashing",
                "traits": ["Forceful", "Reach 10 ft", "Unarmed"],
                "finesse": False
            },
            {
                "name": "Shield Bash",
                "dice": "1d6",
                "type": "Bludgeoning",
                "traits": ["Agile", "Unarmed"],
                "finesse": False
            }
        ],
        "primary_ability": "Act Together: Either you or your eidolon takes an action, and the other simultaneously takes an activity.",
        "secondary_ability": "Dutiful Retaliation: Trigger: An enemy adjacent to the eidolon hits you. Reaction: The devotion phantom makes a melee Strike against the triggering enemy.",
        "traits": ["Divine", "Eidolon", "Holy", "Phantom"]
    }
}

def resolve_eidolon(master_hp: int = 20, level: int = 1, eidolon_type: Optional[str] = None) -> PartnerCreatureData:
    chosen_key = None
    if eidolon_type:
        clean = eidolon_type.lower()
        for k, v in EIDOLON_CATALOG.items():
            if k in clean or clean in k or v.get("sub_type", "").lower() in clean or clean in v.get("sub_type", "").lower():
                chosen_key = k
                break
    if not chosen_key:
        chosen_key = random.choice(list(EIDOLON_CATALOG.keys()))
    cfg = EIDOLON_CATALOG[chosen_key]

    name = random.choice(cfg["name_options"])
    
    # PF2e Remaster Eidolon progression (ability boosts at 5, 10, 15, 20)
    boost_tiers = sum(1 for thr in (5, 10, 15, 20) if level >= thr)
    str_mod = cfg["str_mod"] + (boost_tiers if cfg["str_mod"] >= cfg["dex_mod"] else max(0, boost_tiers - 1))
    dex_mod = cfg["dex_mod"] + (boost_tiers if cfg["dex_mod"] > cfg["str_mod"] else max(0, boost_tiers - 1))
    con_mod = cfg["con_mod"] + boost_tiers
    wis_mod = cfg["wis_mod"] + max(0, boost_tiers - 1)

    # Armor proficiency: Expert (+4) at 1, Master (+6) at 11, Legendary (+8) at 19
    armor_rank = 8 if level >= 19 else (6 if level >= 11 else 4)
    armor_item = 3 if level >= 18 else (2 if level >= 11 else (1 if level >= 5 else 0))
    ac = 10 + dex_mod + armor_rank + level + armor_item

    # Saves & Perception: Expert (+4) Fort/Will at 1, Master (+6) at 13; Reflex Expert (+4) at 9
    fort_rank = 6 if level >= 13 else 4
    will_rank = 6 if level >= 13 else 4
    ref_rank = 4 if level >= 9 else 2
    perc_rank = 4 if level >= 9 else 2
    save_item = 3 if level >= 17 else (2 if level >= 11 else (1 if level >= 5 else 0))

    fort = fort_rank + level + con_mod + save_item
    ref = ref_rank + level + dex_mod + save_item
    will = will_rank + level + wis_mod + save_item
    perception = perc_rank + level + wis_mod + save_item

    # Unarmed Strikes: Trained (+2) at 1, Expert (+4) at 5, Master (+6) at 13 + Handwraps potency/striking
    atk_rank = 6 if level >= 13 else (4 if level >= 5 else 2)
    potency_bonus = 3 if level >= 16 else (2 if level >= 10 else (1 if level >= 2 else 0))
    striking_dice = 4 if level >= 19 else (3 if level >= 12 else (2 if level >= 4 else 1))
    spec_dmg = 6 if level >= 15 else (3 if level >= 7 else 0)
    strikes: List[Strike] = []

    for st in cfg["strikes"]:
        is_fin = st.get("finesse", False)
        atk_mod = max(str_mod, dex_mod) if is_fin else str_mod
        atk_bonus = atk_rank + level + atk_mod + potency_bonus

        die_face = st["dice"].split("d", 1)[1] if "d" in st["dice"] else "6"
        dmg_bonus = str_mod + spec_dmg
        dmg_str = f"{striking_dice}d{die_face}+{dmg_bonus}" if dmg_bonus > 0 else f"{striking_dice}d{die_face}"

        is_agile = "Agile" in st.get("traits", [])
        map_second = atk_bonus - (4 if is_agile else 5)
        map_third = atk_bonus - (8 if is_agile else 10)

        strikes.append(Strike(
            name=st["name"],
            attack_bonus=atk_bonus,
            map_second=map_second,
            map_third=map_third,
            damage_dice=dmg_str,
            damage_type=st["type"],
            traits=st.get("traits", [])
        ))

    return PartnerCreatureData(
        name=f"{name} ({cfg['sub_type']})",
        creature_type=cfg.get("sub_type", "Eidolon"),
        sub_type=cfg["sub_type"],
        stage=f"{cfg['tradition']} Bond",
        size=cfg["size"],
        speed=cfg["speed"],
        ac=ac,
        hp=master_hp,
        fortitude=fort,
        reflex=ref,
        will=will,
        perception=perception,
        strikes=strikes,
        primary_ability=cfg["primary_ability"],
        secondary_ability=cfg.get("secondary_ability"),
        traits=cfg.get("traits", [])
    )
