import random
from typing import Dict, Any, List, Optional
from app.engine.models import PartnerCreatureData

FAMILIAR_SPECIES: Dict[str, Dict[str, Any]] = {
    "raven": {
        "species": "Raven",
        "speed": "10 ft, fly 25 ft",
        "innate_abilities": ["Flier", "Speech"],
        "aquatic": False,
        "description": "An intelligent corvid with glossy black feathers capable of mimicking common words."
    },
    "cat": {
        "species": "Black Cat",
        "speed": "25 ft, climb 15 ft",
        "innate_abilities": ["Darkvision", "Fast Movement"],
        "aquatic": False,
        "description": "An aloof, stealthy feline that glides between shadows undetected."
    },
    "toad": {
        "species": "Warted Toad",
        "speed": "15 ft, swim 25 ft",
        "innate_abilities": ["Amphibious", "Tough"],
        "aquatic": True,
        "description": "A calm, earthy amphibian attuned to natural spirits and damp environments."
    },
    "sea_lizard": {
        "species": "Reef Lizard",
        "speed": "20 ft, swim 25 ft",
        "innate_abilities": ["Amphibious", "Darkvision"],
        "aquatic": True,
        "description": "A crested coastal reptile with webbed toes and shimmering tidal scales."
    },
    "tidepool_octopus": {
        "species": "Tidepool Octopus",
        "speed": "10 ft, swim 30 ft",
        "innate_abilities": ["Amphibious", "Manual Dexterity"],
        "aquatic": True,
        "description": "A clever cephalopod capable of shifting color and manipulating small tools."
    },
    "reef_crab": {
        "species": "Coral Crab",
        "speed": "20 ft, swim 20 ft",
        "innate_abilities": ["Amphibious", "Tough"],
        "aquatic": True,
        "description": "An armored crustacean draped in living sea anemones and barnacles."
    },
    "serpent": {
        "species": "Viper",
        "speed": "20 ft, climb 20 ft",
        "innate_abilities": ["Scent", "Poison Resistance"],
        "aquatic": False,
        "description": "A slender snake that coils unobtrusively around your wrist or staff."
    },
    "owl": {
        "species": "Screech Owl",
        "speed": "10 ft, fly 30 ft",
        "innate_abilities": ["Flier", "Darkvision"],
        "aquatic": False,
        "description": "A nocturnal raptor with wide, perceptive eyes and silent wingbeats."
    },
    "leshy": {
        "species": "Leaf Leshy",
        "speed": "25 ft",
        "innate_abilities": ["Plant Form", "Restorative Familiar"],
        "aquatic": False,
        "description": "A diminutive nature spirit formed from pressed autumn leaves and twigs."
    },
    "elemental_wisp": {
        "species": "Elemental Wisp",
        "speed": "15 ft, fly 25 ft",
        "innate_abilities": ["Elemental", "Flier", "Darkvision"],
        "aquatic": False,
        "elemental": True,
        "description": "A tiny, swirling mote of raw elemental essence bound to your kinetic gate."
    },
    "elemental_mote": {
        "species": "Crystalline Mote",
        "speed": "20 ft, burrow 10 ft",
        "innate_abilities": ["Elemental", "Darkvision", "Tough"],
        "aquatic": False,
        "elemental": True,
        "description": "A hovering shard of living stone and forged metal resonating with planar energy."
    },
    "elemental_spirit": {
        "species": "Tidal & Ember Sprite",
        "speed": "20 ft, swim 25 ft",
        "innate_abilities": ["Elemental", "Amphibious", "Resistance"],
        "aquatic": True,
        "elemental": True,
        "description": "A flickering planar spirit formed of dancing sparks, mist, and living timber."
    }
}

FAMILIAR_ABILITIES_POOL = [
    {"name": "Cantrip Connection", "desc": "You can prepare or cast one additional cantrip from your familiar's mystical connection."},
    {"name": "Spell Delivery", "desc": "If your familiar is in your space, you can have it deliver a touch spell to a target within its movement range."},
    {"name": "Share Senses", "desc": "Once every 10 minutes, you can spend 1 action to project your senses through your familiar up to 1 mile away."},
    {"name": "Speech", "desc": "Your familiar can speak in a clear voice using one common language you know."},
    {"name": "Independent", "desc": "In combat encounters, if you do not Command your familiar on your turn, it still gains 1 action to Stride or Step."},
    {"name": "Lab Assistant", "desc": "Your familiar can use Quick Alchemy or retrieve materials if you are an alchemist."}
]

FAMILIAR_NAMES = ["Corvus", "Pippin", "Hecate", "Mallow", "Barnaby", "Nyx", "Bramble", "Zephyr", "Grimm", "Soot", "Riptide", "Brine"]


import re

KNOWN_SPECIES_WORDS = [
    "hawk", "falcon", "eagle", "owl", "raven", "crow", "viper", "snake", "serpent",
    "cat", "toad", "frog", "lizard", "octopus", "crab", "leshy", "fox", "wolf",
    "badger", "weasel", "ferret", "rat", "bat", "spider", "beetle", "stag", "horse"
]


def _extract_species_from_text(desc: Optional[str]) -> Optional[str]:
    if not desc or not isinstance(desc, str):
        return None
    low = desc.lower()
    for word in KNOWN_SPECIES_WORDS:
        if re.search(rf"\b{re.escape(word)}\b", low):
            return word.title()
    return None


def resolve_familiar(
    master_ac: int,
    master_fort: int,
    master_ref: int,
    master_will: int,
    master_perception: int,
    class_name: str,
    level: int = 1,
    aquatic_only: bool = False,
    is_pet: bool = False,
    forced_species: Optional[str] = None,
    description_text: Optional[str] = None,
    archetype_name: Optional[str] = None,
    is_undead_familiar: bool = False,
) -> PartnerCreatureData:
    if forced_species == "elemental":
        pool = [k for k, v in FAMILIAR_SPECIES.items() if v.get("elemental")]
    elif forced_species and forced_species in FAMILIAR_SPECIES:
        pool = [forced_species]
    elif aquatic_only:
        pool = [k for k, v in FAMILIAR_SPECIES.items() if v.get("aquatic") and not v.get("elemental")]
    else:
        pool = [k for k, v in FAMILIAR_SPECIES.items() if not v.get("elemental")]

    key = random.choice(pool)
    cfg = FAMILIAR_SPECIES[key]
    name = random.choice(FAMILIAR_NAMES)
    extracted_species = _extract_species_from_text(description_text)
    if extracted_species:
        species_label = extracted_species
        sub_label = f"{species_label} Pet" if is_pet else f"{species_label} Familiar"
    else:
        species_label = cfg["species"]


    FLYING_BIRDS = {"hawk", "falcon", "eagle", "owl", "raven", "crow"}
    if extracted_species:
        ext_low = extracted_species.lower()
        if ext_low in FLYING_BIRDS:
            cfg = dict(cfg)
            cfg["speed"] = "10 ft, fly 60 ft" if ext_low in ("hawk", "falcon", "eagle") else "10 ft, fly 30 ft"
            cfg["innate_abilities"] = ["Flier", "Keen Eyes"]
            cfg["aquatic"] = False

    # Remaster rules: HP = 5 * Master Level
    hp = 5 * level

    if is_pet:
        ability_tags = list(cfg.get("innate_abilities") or [])[:2]
        if aquatic_only:
            for req_ab in ("Darkvision", "Tough"):
                if req_ab not in ability_tags:
                    ability_tags.append(req_ab)
        ability_summary = ", ".join(ability_tags) if ability_tags else "Amphibious, Tough"
        primary_text = (
            f"Pet Abilities: {ability_summary}. Tiny minion (Perception +{3 + level}, other skills +{level}, "
            f"HP {hp}). Can be retrained if you have a familiar; choose which minion to use in play."
        )
        secondary_text = cfg["description"]
        stage_label = "Bonded Pet"
        sub_label = f"{species_label} Pet"
    else:
        is_undead_mode = bool(is_undead_familiar or (description_text and "undead familiar" in description_text.lower()))
        filtered_pool = [
            a for a in FAMILIAR_ABILITIES_POOL
            if not (
                is_undead_mode
                and (class_name.lower() != "alchemist" and "lab assistant" in str(a.get("name", "")).lower())
            )
        ] or list(FAMILIAR_ABILITIES_POOL)
        ability_count = 1 if is_undead_mode else min(2, len(filtered_pool))
        chosen_pool_abilities = random.sample(filtered_pool, ability_count)
        base_innate = list(cfg["innate_abilities"])[:1] if is_undead_mode else list(cfg["innate_abilities"])
        ability_tags = base_innate + [a["name"] for a in chosen_pool_abilities]
        ability_summary = ", ".join(ability_tags)
        if is_undead_mode:
            primary_text = f"Undead Familiar Ability (1/day): {ability_summary}. {chosen_pool_abilities[0]['name']}: {chosen_pool_abilities[0]['desc']}"
            secondary_text = "Undead trait instead of Animal; immune to bleed, death effects, disease, mental, and poison. Cannot take trait-changing abilities."
            stage_label = "Undead Familiar"
        else:
            primary_text = f"Familiar Abilities: {ability_summary}. {chosen_pool_abilities[0]['name']}: {chosen_pool_abilities[0]['desc']}"
            secondary_text = f"{chosen_pool_abilities[1]['name']}: {chosen_pool_abilities[1]['desc']}" if len(chosen_pool_abilities) > 1 else ""
            is_witch_partner = class_name.lower() == "witch" or "witch" in str(archetype_name or "").lower()
            stage_label = "Patron Conduit" if is_witch_partner else ("Marine Bond" if aquatic_only else "Mystical Bond")
        sub_label = f"{species_label} Familiar"

    eff_perception = (3 + level) if is_pet else master_perception
    return PartnerCreatureData(
        name=f"{name} ({species_label})",
        creature_type="Pet" if is_pet else "Familiar",
        sub_type=sub_label,
        stage=stage_label,
        size="Tiny",
        speed=cfg["speed"],
        ac=master_ac,
        hp=hp,
        fortitude=master_fort,
        reflex=master_ref,
        will=master_will,
        perception=eff_perception,
        strikes=[],
        primary_ability=primary_text,
        secondary_ability=secondary_text,
        traits=(["Undead", "Familiar", "Magical", "Minion"] if (not is_pet and (is_undead_familiar or (description_text and "undead familiar" in description_text.lower()))) else (["Familiar", "Magical", "Minion"] if not is_pet else ["Pet", "Animal", "Minion"])),
    )
