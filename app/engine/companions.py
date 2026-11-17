import random
import re
from typing import Dict, Any, List, Optional
from app.engine.models import AnimalCompanionData, Strike, FeatSummary

COMPANION_NAMES = [
    "Fang", "Shadow", "Ghost", "Bruno", "Copper", "Grizz",
    "Storm", "Zephyr", "Rowan", "Onyx", "Talon", "Bramble",
    "Pip", "Squeak", "Barnaby", "Cinder", "Feather", "Pebble"
]

COMPANION_SPECIES: Dict[str, Dict[str, Any]] = {
    # --- SMALL / FAMILIAR & BIRDS ---
    "mouse": {
        "species": "Mouse / Rodent",
        "young_size": "Tiny",
        "mature_size": "Small",
        "speed": "25 ft, burrow 10 ft",
        "base_hp": 4,
        "con_mod": 1,
        "str_mod": 0,
        "dex_mod": 3,
        "wis_mod": 2,
        "strikes": [
            {"name": "Jaws", "dice": "1d4", "type": "Piercing", "traits": ["Finesse", "Agile", "Unarmed"], "finesse": True}
        ],
        "support_benefit": "Your mouse scurries through distractions. Enemies adjacent to your mouse are flat-footed against your attacks.",
        "advanced_maneuver": "Squeeze By: The mouse can move through enemy spaces effortlessly."
    },
    "bat": {
        "species": "Giant Bat",
        "young_size": "Small",
        "mature_size": "Medium",
        "speed": "20 ft, fly 40 ft",
        "base_hp": 4,
        "con_mod": 1,
        "str_mod": 1,
        "dex_mod": 3,
        "wis_mod": 2,
        "strikes": [
            {"name": "Jaws", "dice": "1d6", "type": "Piercing", "traits": ["Finesse", "Unarmed"], "finesse": True}
        ],
        "support_benefit": "Your bat emits disorienting screeches. Targets you hit within your bat's reach are dazzled until the start of your next turn.",
        "advanced_maneuver": "Echolocating Swoop: The bat ignores concealment against targets it targets."
    },
    "owl": {
        "species": "Owl",
        "young_size": "Tiny",
        "mature_size": "Small",
        "speed": "10 ft, fly 50 ft",
        "base_hp": 4,
        "con_mod": 1,
        "str_mod": 1,
        "dex_mod": 3,
        "wis_mod": 3,
        "strikes": [
            {"name": "Talons", "dice": "1d6", "type": "Slashing", "traits": ["Finesse", "Unarmed", "Silent"], "finesse": True}
        ],
        "support_benefit": "Your owl spots weak points from above. Your ranged or melee strikes against targets illuminated or observed by your owl ignore circumstance bonuses to AC from cover.",
        "advanced_maneuver": "Silent Strike: The owl Strikes from stealth without revealing its position."
    },
    "dog": {
        "species": "Hound / Dog",
        "young_size": "Small",
        "mature_size": "Medium",
        "speed": "40 ft",
        "base_hp": 6,
        "con_mod": 2,
        "str_mod": 2,
        "dex_mod": 2,
        "wis_mod": 2,
        "strikes": [
            {"name": "Jaws", "dice": "1d8", "type": "Piercing", "traits": ["Trip", "Unarmed"], "finesse": False}
        ],
        "support_benefit": "Your hound corners your quarry. Whenever you hit a creature in your dog's reach, the target cannot take reactions until the start of your next turn.",
        "advanced_maneuver": "Guard Dog: Intercepts attacks directed at adjacent allies."
    },
    "flamingo": {
        "species": "Flamingo",
        "young_size": "Small",
        "mature_size": "Medium",
        "speed": "30 ft, fly 30 ft, swim 20 ft",
        "base_hp": 4,
        "con_mod": 1,
        "str_mod": 1,
        "dex_mod": 3,
        "wis_mod": 2,
        "strikes": [
            {"name": "Beak", "dice": "1d6", "type": "Piercing", "traits": ["Finesse", "Reach 10 ft", "Unarmed"], "finesse": True}
        ],
        "support_benefit": "Your flamingo disorients foes with elegant defensive wading. Enemies within your flamingo's reach take a -1 circumstance penalty to Reflex saves.",
        "advanced_maneuver": "Wading Kick: A sweeping kick that pushes an enemy 5 feet."
    },

    # --- CORE CLASSICS ---
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
            {"name": "Jaws", "dice": "1d8", "type": "Piercing", "traits": ["Trip", "Unarmed"], "finesse": False}
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
            {"name": "Jaws", "dice": "1d8", "type": "Piercing", "traits": ["Unarmed"], "finesse": False},
            {"name": "Claw", "dice": "1d6", "type": "Slashing", "traits": ["Agile", "Unarmed"], "finesse": False}
        ],
        "support_benefit": "Your bear mauls your enemies. Whenever you hit a creature in your bear's reach, the bear deals 1d8 slashing damage to that creature.",
        "advanced_maneuver": "Bear Hug: If the bear hits with two consecutive claw strikes, it grabs the target automatically."
    },
    "cat": {
        "species": "Big Cat (Leopard / Tiger)",
        "young_size": "Small",
        "mature_size": "Medium",
        "speed": "40 ft",
        "base_hp": 4,
        "con_mod": 1,
        "str_mod": 2,
        "dex_mod": 3,
        "wis_mod": 1,
        "strikes": [
            {"name": "Jaws", "dice": "1d6", "type": "Piercing", "traits": ["Finesse", "Unarmed"], "finesse": True},
            {"name": "Claw", "dice": "1d4", "type": "Slashing", "traits": ["Agile", "Finesse", "Unarmed"], "finesse": True}
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
            {"name": "Bite", "dice": "1d8", "type": "Piercing", "traits": ["Unarmed"], "finesse": False},
            {"name": "Claw", "dice": "1d6", "type": "Slashing", "traits": ["Agile", "Unarmed"], "finesse": False}
        ],
        "support_benefit": "Your badger snarls viciously. Enemies within the badger's reach take a -1 circumstance penalty to attack rolls.",
        "advanced_maneuver": "Badger Rage: The badger gains temporary HP and a status bonus to melee damage rolls."
    },
    "horse": {
        "species": "Horse (Mount)",
        "young_size": "Large",
        "mature_size": "Large",
        "speed": "50 ft",
        "base_hp": 8,
        "con_mod": 2,
        "str_mod": 3,
        "dex_mod": 2,
        "wis_mod": 1,
        "strikes": [
            {"name": "Hoof", "dice": "1d8", "type": "Bludgeoning", "traits": ["Unarmed"], "finesse": False}
        ],
        "support_benefit": "Your horse carries you swiftly into battle. You gain a +5-foot status bonus to your Speed when you Stride closer to an enemy your horse is adjacent to.",
        "advanced_maneuver": "Gallop: The horse Strides twice."
    },
    
    # --- DINOSAURS & REPTILES ---
    "deinonychus": {
        "species": "Deinonychus",
        "young_size": "Medium",
        "mature_size": "Medium",
        "speed": "40 ft",
        "base_hp": 6,
        "con_mod": 2,
        "str_mod": 3,
        "dex_mod": 3,
        "wis_mod": 1,
        "strikes": [
            {"name": "Talon", "dice": "1d8", "type": "Slashing", "traits": ["Finesse", "Unarmed"], "finesse": True},
            {"name": "Jaws", "dice": "1d6", "type": "Piercing", "traits": ["Unarmed"], "finesse": False}
        ],
        "support_benefit": "Your deinonychus leaps on foes. Your Strikes against a creature flanked by you and your deinonychus deal 2 additional precision damage.",
        "advanced_maneuver": "Dino Leap: The deinonychus Leaps up to twice its normal distance."
    },
    "crocodile": {
        "species": "Crocodile",
        "young_size": "Small",
        "mature_size": "Medium",
        "speed": "25 ft, swim 25 ft",
        "base_hp": 8,
        "con_mod": 3,
        "str_mod": 3,
        "dex_mod": 2,
        "wis_mod": 1,
        "strikes": [
            {"name": "Jaws", "dice": "1d8", "type": "Piercing", "traits": ["Grab", "Unarmed"], "finesse": False},
            {"name": "Tail", "dice": "1d6", "type": "Bludgeoning", "traits": ["Agile", "Unarmed"], "finesse": False}
        ],
        "support_benefit": "Your crocodile clamps down. If the crocodile has a creature grabbed, your attacks against that creature ignore circumstance bonuses to AC from shields or cover.",
        "advanced_maneuver": "Death Roll: The crocodile rolls with a grabbed target, dealing automatic bite damage and knocking it prone."
    },

    # --- INSECTS & ARTHROPODS ---
    "beetle": {
        "species": "Stag Beetle",
        "young_size": "Medium",
        "mature_size": "Large",
        "speed": "25 ft, burrow 10 ft",
        "base_hp": 10,
        "con_mod": 3,
        "str_mod": 4,
        "dex_mod": 1,
        "wis_mod": 1,
        "strikes": [
            {"name": "Mandible", "dice": "1d10", "type": "Piercing", "traits": ["Unarmed"], "finesse": False}
        ],
        "support_benefit": "Your beetle locks its mandibles as a bulwark. Your attacks gain the Grapple trait when targeting creatures adjacent to your beetle.",
        "advanced_maneuver": "Carapace Wall: The beetle tucks in, granting cover to adjacent allies."
    },
    "spider": {
        "species": "Giant Spider",
        "young_size": "Small",
        "mature_size": "Medium",
        "speed": "30 ft, climb 30 ft",
        "base_hp": 6,
        "con_mod": 2,
        "str_mod": 2,
        "dex_mod": 3,
        "wis_mod": 2,
        "strikes": [
            {"name": "Fangs", "dice": "1d6", "type": "Piercing", "traits": ["Unarmed"], "finesse": False}
        ],
        "support_benefit": "Your spider webs the area. Enemies damaged by your strikes take a -10-foot status penalty to Speed until they break free.",
        "advanced_maneuver": "Web Trap: The spider spins a web wall across a 10-foot square."
    },

    # --- AQUATIC ---
    "shark": {
        "species": "Shark",
        "young_size": "Medium",
        "mature_size": "Large",
        "speed": "swim 45 ft",
        "base_hp": 8,
        "con_mod": 2,
        "str_mod": 3,
        "dex_mod": 3,
        "wis_mod": 1,
        "strikes": [
            {"name": "Jaws", "dice": "1d10", "type": "Piercing", "traits": ["Unarmed"], "finesse": False}
        ],
        "support_benefit": "Your shark senses blood in the water. Your attacks against bleeding or flat-footed targets in water deal 2 additional damage.",
        "advanced_maneuver": "Feeding Frenzy: The shark makes consecutive attacks against targets in water with reduced multiple attack penalties."
    },
    "octopus": {
        "species": "Octopus",
        "young_size": "Small",
        "mature_size": "Medium",
        "speed": "swim 40 ft",
        "base_hp": 6,
        "con_mod": 2,
        "str_mod": 2,
        "dex_mod": 3,
        "wis_mod": 2,
        "strikes": [
            {"name": "Tentacle", "dice": "1d6", "type": "Bludgeoning", "traits": ["Agile", "Grab", "Unarmed"], "finesse": True}
        ],
        "support_benefit": "Your octopus releases a cloud of ink. Adjacent enemies are concealed from your attacks, but you can see through the ink.",
        "advanced_maneuver": "Ink Jet: The octopus squirts ink and rushes away safely."
    }
}

def resolve_companion(
    class_name: str,
    feats: List[FeatSummary],
    archetype: Optional[str],
    level: int = 1,
    force_qualify: bool = False,
    concept_text: Optional[str] = None
) -> Optional[AnimalCompanionData]:
    cls_lower = class_name.lower()
    feat_names = [f.name.lower() for f in feats]
    has_companion_feat = any("animal companion" in fn or "beastmaster" in fn for fn in feat_names)
    is_beastmaster = archetype and "beastmaster" in archetype.lower()
    
    # Auto-force qualification if the user's concept text explicitly asks for a companion/pet
    has_concept_companion = bool(concept_text and any(w in concept_text.lower() for w in ("companion", "pet", "mouse", "moose", "wolf", "bear")))
    should_qualify = force_qualify or has_companion_feat or is_beastmaster or has_concept_companion or cls_lower in ("ranger", "champion") or (cls_lower == "druid" and ("order: animal" in " ".join(feat_names) or has_concept_companion))

    if not should_qualify:
        return None

 matched_species_key = None
    search_corpus = f"{concept_text or ''}".lower()  # Search only the concept text, not the entire feat string
    
    sorted_keys = sorted(COMPANION_SPECIES.keys(), key=len, reverse=True)
    for key in sorted_keys:
        if re.search(rf"\b{key}\b", search_corpus):
            matched_species_key = key
            break

    if matched_species_key and matched_species_key in COMPANION_SPECIES:
        cfg = COMPANION_SPECIES[matched_species_key]
    else:
        # Intelligent Dynamic Fallback Generator for ANY unlisted animal
        custom_animal_name = "Beast"
        if concept_text:
            words = concept_text.split()
            for i, w in enumerate(words):
                if w.lower() in ("with", "companion", "pet", "familiar") and i + 1 < len(words):
                    next_idx = i + 1
                    while next_idx < len(words) and words[next_idx].lower() in ("a", "an", "the"):
                        next_idx += 1
                    if next_idx < len(words):
                        custom_animal_name = words[next_idx].strip(".,!?:;")
                    break

        name_lower = custom_animal_name.lower()
        
        # Categorize dynamic stats based on animal type keywords
        if any(b in name_lower for b in ("elephant", "mammoth", "rhino", "hippo", "whale", "dinosaur")):
            young_size, mature_size, speed, base_hp, str_m, con_m, dex_m, wis_m = "Large", "Large", "30 ft", 10, 4, 3, 1, 1
            strike_name, dice, dtype, traits = "Gore / Slam", "1d10", "Bludgeoning", ["Reach 10 ft", "Unarmed"]
        elif any(bird in name_lower for bird in ("toucan", "hawk", "raven", "eagle", "parrot", "falcon")):
            young_size, mature_size, speed, base_hp, str_m, con_m, dex_m, wis_m = "Small", "Medium", "10 ft, fly 50 ft", 4, 1, 1, 3, 2
            strike_name, dice, dtype, traits = "Beak / Talons", "1d6", "Piercing", ["Finesse", "Agile", "Unarmed"]
        elif any(farm in name_lower for farm in ("goat", "sheep", "ram", "alpaca", "llama")):
            young_size, mature_size, speed, base_hp, str_m, con_m, dex_m, wis_m = "Small", "Medium", "35 ft", 6, 2, 2, 2, 1
            strike_name, dice, dtype, traits = "Horns / Hooves", "1d8", "Bludgeoning", ["Trip", "Unarmed"]
        else:
            # General default beast
            young_size, mature_size, speed, base_hp, str_m, con_m, dex_m, wis_m = "Small", "Medium", "30 ft", 6, 2, 2, 2, 1
            strike_name, dice, dtype, traits = "Natural Attack", "1d6", "Piercing", ["Unarmed"]

        cfg = {
            "species": custom_animal_name.capitalize(),
            "young_size": young_size,
            "mature_size": mature_size,
            "speed": speed,
            "base_hp": base_hp,
            "con_mod": con_m,
            "str_mod": str_m,
            "dex_mod": dex_m,
            "wis_mod": wis_m,
            "strikes": [
                {"name": strike_name, "dice": dice, "type": dtype, "traits": traits, "finesse": "Finesse" in traits}
            ],
            "support_benefit": f"Your {custom_animal_name.lower()} coordinates seamlessly with your attacks. Enemies adjacent to it are off-guard.",
            "advanced_maneuver": f"Feral Surge: The {custom_animal_name.lower()} unleashes a coordinated assault."
        }

    is_mature = level >= 4 or any("mature" in fn for fn in feat_names)
    stage = "Mature" if is_mature else "Young"
    size = cfg["mature_size"] if is_mature else cfg["young_size"]

    prof_bonus = 2 + level
    con_mod = cfg["con_mod"] + (1 if is_mature else 0)
    str_mod = cfg["str_mod"] + (1 if is_mature else 0)
    dex_mod = cfg["dex_mod"] + (1 if is_mature else 0)
    wis_mod = cfg["wis_mod"] + (1 if is_mature else 0)

    hp = cfg["base_hp"] + (level * (6 + con_mod)) + (10 if is_mature else 0)
    ac = 10 + dex_mod + prof_bonus + (1 if is_mature else 0)

    fort_save = prof_bonus + con_mod + (1 if is_mature else 0)
    ref_save = prof_bonus + dex_mod + (1 if is_mature else 0)
    will_save = prof_bonus + wis_mod + (1 if is_mature else 0)
    perception = prof_bonus + wis_mod

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

    companion_attrs = {
        "STR": str_mod,
        "DEX": dex_mod,
        "CON": con_mod,
        "INT": -4,
        "WIS": wis_mod,
        "CHA": -4
    }
    companion_skills = {
        "Athletics": prof_bonus + str_mod,
        "Acrobatics": prof_bonus + dex_mod,
        "Stealth": prof_bonus + dex_mod,
        "Survival": prof_bonus + wis_mod
    }

    comp_traits = ["Animal", "Minion"]
    if is_mature:
        comp_traits.append("Mature")

    return AnimalCompanionData(
        name=f"{c_name} the {cfg['species']}",
        creature_type="Animal Companion",
        sub_type=cfg.get("species", "Beast"),
        primary_ability=cfg.get("support_benefit", ""),
        secondary_ability=cfg.get("advanced_maneuver") if is_mature else None,
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
        traits=comp_traits,
        senses="Low-Light Vision, Scent (Imprecise) 30 ft",
        attributes=companion_attrs,
        skills=companion_skills,
        support_benefit=cfg["support_benefit"],
        advanced_maneuver=cfg.get("advanced_maneuver") if is_mature else None
    )
