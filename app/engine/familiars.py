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
    forced_species: Optional[str] = None
) -> PartnerCreatureData:
    if forced_species and forced_species in FAMILIAR_SPECIES:
        pool = [forced_species]
    elif aquatic_only:
        pool = [k for k, v in FAMILIAR_SPECIES.items() if v.get("aquatic")]
    else:
        pool = list(FAMILIAR_SPECIES.keys())

    key = random.choice(pool)
    cfg = FAMILIAR_SPECIES[key]
    name = random.choice(FAMILIAR_NAMES)

    # Remaster rules: HP = 5 * Master Level
    hp = 5 * level

    if is_pet:
        ability_tags = list(cfg["innate_abilities"])[:1]
        ability_summary = ", ".join(ability_tags)
        primary_text = f"Pet Abilities: {ability_summary}. Tiny animal companion with non-combat utility."
        secondary_text = cfg["description"]
        stage_label = "Bonded Pet"
        sub_label = f"{cfg['species']} Pet"
    else:
        chosen_pool_abilities = random.sample(FAMILIAR_ABILITIES_POOL, 2)
        ability_tags = list(cfg["innate_abilities"]) + [a["name"] for a in chosen_pool_abilities]
        ability_summary = ", ".join(ability_tags)
        primary_text = f"Familiar Abilities: {ability_summary}. {chosen_pool_abilities[0]['name']}: {chosen_pool_abilities[0]['desc']}"
        secondary_text = f"{chosen_pool_abilities[1]['name']}: {chosen_pool_abilities[1]['desc']}"
        stage_label = "Patron Conduit" if class_name.lower() == "witch" else ("Marine Bond" if aquatic_only else "Mystical Bond")
        sub_label = f"{cfg['species']} Familiar"

    return PartnerCreatureData(
        name=f"{name} ({cfg['species']})",
        creature_type="Familiar",
        sub_type=sub_label,
        stage=stage_label,
        size="Tiny",
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
        traits=["Familiar", "Magical", "Minion"] if not is_pet else ["Pet", "Animal", "Minion"]
    )
