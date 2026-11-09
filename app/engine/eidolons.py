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
    
    # Eidolons start Expert (+4) in unarmored defense
    ac_prof = 4 + level
    ac = 10 + cfg["dex_mod"] + ac_prof

    # Saves: Expert in Fortitude and Will, Trained in Reflex
    fort = (4 + level) + cfg["con_mod"]
    ref = (2 + level) + cfg["dex_mod"]
    will = (4 + level) + cfg["wis_mod"]
    perception = (2 + level) + cfg["wis_mod"]

    # Attack bonus: Trained in unarmed strikes (+2 + level)
    atk_prof = 2 + level
    strikes: List[Strike] = []

    for st in cfg["strikes"]:
        is_fin = st.get("finesse", False)
        atk_mod = max(cfg["str_mod"], cfg["dex_mod"]) if is_fin else cfg["str_mod"]
        atk_bonus = atk_prof + atk_mod
        
        # Level 4 Handwraps / Potency bonus
        if level >= 4:
            atk_bonus += 1

        dmg_bonus = cfg["str_mod"]
        dmg_str = f"{st['dice']}+{dmg_bonus}" if dmg_bonus > 0 else st["dice"]

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
