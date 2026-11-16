# app/engine/heritages.py
<<<<<<< HEAD
# Comprehensive Official Pathfinder 2e Ancestry Heritages Matrix

import random
from typing import Dict, Any, List, Optional
=======
import random
from typing import Dict, List
>>>>>>> 187a873 (Successfully modularize heritages and subclasses, fix all engine import paths)

AWAKENED_ANIMAL_SPECIES = [
    {"species": "Wolf", "heritage": "Running Animal", "unarmed": "Jaws (1d6 P)", "size": "Medium"},
    {"species": "Red Fox", "heritage": "Running Animal", "unarmed": "Jaws (1d6 P, Finesse)", "size": "Small"},
    {"species": "Grizzly Bear", "heritage": "Running Animal", "unarmed": "Jaws (1d8 P) or Claws (1d6 S, Agile)", "size": "Medium"},
    {"species": "Cheetah", "heritage": "Running Animal", "unarmed": "Jaws (1d6 P, Finesse)", "size": "Medium"},
    {"species": "Deer", "heritage": "Running Animal", "unarmed": "Antlers (1d6 P)", "size": "Medium"},
    {"species": "Badger", "heritage": "Burrowing Animal", "unarmed": "Jaws (1d6 P) or Claws (1d6 S, Agile)", "size": "Small"},
    {"species": "Mole", "heritage": "Burrowing Animal", "unarmed": "Claws (1d6 S, Agile)", "size": "Small"},
    {"species": "Wombat", "heritage": "Burrowing Animal", "unarmed": "Jaws (1d6 P)", "size": "Small"},
    {"species": "Raccoon", "heritage": "Climbing Animal", "unarmed": "Claws (1d6 S, Agile, Finesse)", "size": "Small"},
    {"species": "Leopard", "heritage": "Climbing Animal", "unarmed": "Jaws (1d6 P) or Claws (1d6 S, Agile)", "size": "Medium"},
    {"species": "Squirrel", "heritage": "Climbing Animal", "unarmed": "Jaws (1d6 P, Finesse)", "size": "Small"},
    {"species": "Tree Frog", "heritage": "Climbing Animal", "unarmed": "Tongue (1d6 B)", "size": "Small"},
    {"species": "Raven", "heritage": "Flying Animal", "unarmed": "Beak (1d6 P, Finesse) or Talons (1d6 S, Agile)", "size": "Small"},
    {"species": "Barn Owl", "heritage": "Flying Animal", "unarmed": "Talons (1d6 S, Agile, Finesse)", "size": "Small"},
    {"species": "Hawk", "heritage": "Flying Animal", "unarmed": "Talons (1d6 S, Agile, Finesse)", "size": "Small"},
    {"species": "Fruit Bat", "heritage": "Flying Animal", "unarmed": "Fangs (1d6 P, Finesse)", "size": "Small"},
    {"species": "River Otter", "heritage": "Swimming Animal", "unarmed": "Jaws (1d6 P, Finesse)", "size": "Small"},
    {"species": "Beaver", "heritage": "Swimming Animal", "unarmed": "Teeth (1d6 P)", "size": "Small"},
    {"species": "Seal", "heritage": "Swimming Animal", "unarmed": "Jaws (1d6 P)", "size": "Medium"},
    {"species": "Crocodile", "heritage": "Swimming Animal", "unarmed": "Jaws (1d8 P)", "size": "Medium"}
]

ANCESTRY_HERITAGES: Dict[str, List[Dict[str, str]]] = {
    "human": [
        {"name": "Versatile Human", "description": "You gain a general feat of your choice at 1st level."},
        {"name": "Skilled Human", "description": "You become trained in one additional skill of your choice."},
        {"name": "Half-Elf (Aiuvarin)", "description": "You gain low-light vision and the elf trait."},
<<<<<<< HEAD
        {"name": "Half-Orc (Dromaar)", "description": "You gain low-light vision and the orc trait."},
        {"name": "Wintertouched Human", "description": "You adapt to frigid climes and gain cold resistance equal to half your level."},
        {"name": "Defined Human", "description": "You gain a specialized heritage background reflecting your distinct cultural upbringing."}
=======
        {"name": "Half-Orc (Dromaar)", "description": "You gain low-light vision and the orc trait."}
>>>>>>> 187a873 (Successfully modularize heritages and subclasses, fix all engine import paths)
    ],
    "dwarf": [
        {"name": "Strong-Blooded Dwarf", "description": "You gain poison resistance and a +2 bonus to poison saving throws."},
        {"name": "Rock Dwarf", "description": "You gain a +2 circumstance bonus to your Fortitude or Reflex DC against Shove or Trip."},
        {"name": "Forge Dwarf", "description": "You gain fire resistance equal to half your level (minimum 1)."},
<<<<<<< HEAD
        {"name": "Death Warden Dwarf", "description": "You gain a +2 circumstance bonus to saving throws against necromancy effects."},
        {"name": "Anvil Dwarf", "description": "You are preternaturally steady on your feet, gaining bonuses against effects that knock you prone."}
=======
        {"name": "Death Warden Dwarf", "description": "You gain a +2 circumstance bonus to saving throws against necromancy effects."}
>>>>>>> 187a873 (Successfully modularize heritages and subclasses, fix all engine import paths)
    ],
    "elf": [
        {"name": "Ancient Elf", "description": "You gain a multiclass dedication feat at 1st level."},
        {"name": "Cavern Elf", "description": "You gain darkvision, allowing you to see in the dark without light."},
        {"name": "Woodland Elf", "description": "You can always use the Take Cover action in natural terrain."},
<<<<<<< HEAD
        {"name": "Whisper Elf", "description": "You gain a +2 circumstance bonus to Seek creatures using hearing."},
        {"name": "Arctic Elf", "description": "You shrug off blinding snowstorms and gain cold resistance equal to half your level."},
        {"name": "Seer Elf", "description": "Your senses pierce illusions, granting a +1 circumstance bonus to perception checks against illusions."}
=======
        {"name": "Whisper Elf", "description": "You gain a +2 circumstance bonus to Seek creatures using hearing."}
>>>>>>> 187a873 (Successfully modularize heritages and subclasses, fix all engine import paths)
    ],
    "goblin": [
        {"name": "Unbreakable Goblin", "description": "You gain 10 Hit Points from your ancestry instead of 6."},
        {"name": "Razortooth Goblin", "description": "You gain a jaws unarmed attack that deals 1d6 piercing damage."},
        {"name": "Charhide Goblin", "description": "You gain fire resistance equal to half your level (minimum 1)."},
<<<<<<< HEAD
        {"name": "Snow Goblin", "description": "You gain cold resistance equal to half your level (minimum 1)."},
        {"name": "Treedweller Goblin", "description": "You gain a climb Speed of 15 feet in forested environments."}
    ],
    "halfling": [
        {"name": "Gutsy Halfling", "description": "Your success against an emotion effect becomes a critical success."},
        {"name": "Nomadic Halfling", "description": "You speak two additional languages."},
        {"name": "Wildwood Halfling", "description": "You ignore difficult terrain caused by bushes and thick foliage."},
        {"name": "Twilight Halfling", "description": "You possess dim-light vision and naturally blend into shadowy environments."}
=======
        {"name": "Snow Goblin", "description": "You gain cold resistance equal to half your level (minimum 1)."}
    ],
    "halfling": [
        {"name": "Gutsy Halfling", "description": "You gain a bonus against emotion effects."},
        {"name": "Nomadic Halfling", "description": "You speak two additional languages."},
        {"name": "Wildwood Halfling", "description": "You ignore difficult terrain caused by bushes and thick foliage."}
>>>>>>> 187a873 (Successfully modularize heritages and subclasses, fix all engine import paths)
    ],
    "gnome": [
        {"name": "Fey-Touched Gnome", "description": "You gain a primal cantrip of your choice."},
        {"name": "Sensate Gnome", "description": "You gain imprecise scent out to 30 feet."},
<<<<<<< HEAD
        {"name": "Umbral Gnome", "description": "You gain darkvision."},
        {"name": "Vivacious Gnome", "description": "You gain 10 Hit Points from your ancestry instead of 8 and recover faster from drained conditions."}
=======
        {"name": "Umbral Gnome", "description": "You gain darkvision."}
>>>>>>> 187a873 (Successfully modularize heritages and subclasses, fix all engine import paths)
    ],
    "orc": [
        {"name": "Badlands Orc", "description": "You gain cold and heat resistance equal to half your level."},
        {"name": "Hold-Scarred Orc", "description": "You gain 12 Hit Points from your ancestry instead of 10, and Diehard feat."},
<<<<<<< HEAD
        {"name": "Rainfall Orc", "description": "You gain a +2 circumstance bonus to Athletics checks to Swim."},
        {"name": "Gladiator Orc", "description": "You gain training in intimidation and specialized combat bravado."}
    ],
    "surki": [
        {"name": "Breaker Surki", "description": "You gain a 1d4 slashing claw unarmed attack (agile, finesse, versatile B). At 9th level, Grand Metamorphosis unlocks Digging Wedge or Grounding Spikes."},
        {"name": "Elytron Surki", "description": "You take no damage from falling regardless of distance. At 9th level, Grand Metamorphosis unlocks Glowing Wings or Stridulating Song."},
        {"name": "Hardshell Surki", "description": "You can etch armor runes directly onto your natural carapace (+4 item AC medium armor). At 9th level, Grand Metamorphosis unlocks Reinforcing Network or Dampening Harmonics."},
        {"name": "Lantern Surki", "description": "You can Interact (1A) to shed 20-ft bright / 20-ft dim magical light from your abdomen. At 9th level, Grand Metamorphosis unlocks Lantern Beam or Lantern Strobe."}
    ],
    "conrasu": [
        {"name": "Rite of Passage", "description": "You ignore difficult terrain from undergrowth and upgrade balancing successes in forests to critical successes."},
        {"name": "Rite of Light", "description": "You can channel your Sunlight Healing to restore Hit Points directly to an adjacent ally."},
        {"name": "Rite of Invocation", "description": "You gain an innate cantrip of your choice from the arcane or occult spell lists."},
        {"name": "Rite of Knowing", "description": "You possess heightened esoteric geometric awareness, granting bonuses to Recall Knowledge checks."}
=======
        {"name": "Rainfall Orc", "description": "You gain a +2 circumstance bonus to Athletics checks to Swim."}
    ],
    "surki": [
        {"name": "Breaker Surki", "description": "You gain a 1d4 slashing claw unarmed attack."},
        {"name": "Elytron Surki", "description": "You take no damage from falling regardless of distance."},
        {"name": "Hardshell Surki", "description": "You can etch armor runes directly onto your natural carapace."},
        {"name": "Lantern Surki", "description": "You can shed magical light from your abdomen."}
    ],
    "conrasu": [
        {"name": "Rite of Passage", "description": "You ignore difficult terrain from undergrowth."},
        {"name": "Rite of Light", "description": "You channel Sunlight Healing to restore Hit Points to an adjacent ally."},
        {"name": "Rite of Invocation", "description": "You gain an innate cantrip from arcane or occult lists."},
        {"name": "Rite of Knowing", "description": "You possess heightened esoteric geometric awareness."}
>>>>>>> 187a873 (Successfully modularize heritages and subclasses, fix all engine import paths)
    ],
    "leshy": [
        {"name": "Leaf Leshy", "description": "You take no damage from falling no matter the distance."},
        {"name": "Gourd Leshy", "description": "You can store up to 1 Bulk of objects inside your hollow head."},
<<<<<<< HEAD
        {"name": "Vine Leshy", "description": "You gain a +2 circumstance bonus to Athletics checks to Climb."},
        {"name": "Root Leshy", "description": "You gain tremorsense as an imprecise sense out to 30 feet on the ground."}
=======
        {"name": "Vine Leshy", "description": "You gain a +2 circumstance bonus to Athletics checks to Climb."}
>>>>>>> 187a873 (Successfully modularize heritages and subclasses, fix all engine import paths)
    ]
}

GENERIC_HERITAGES = [
    {"name": "Versatile Heritage", "description": "You gain a general feat of your choice at 1st level."},
    {"name": "Skilled Heritage", "description": "You become trained in one additional skill."}
]

def resolve_heritage(ancestry_name: str) -> Dict[str, str]:
    anc_key = ancestry_name.lower().replace("sukri", "surki")
    if "awakened animal" in anc_key:
        spec = random.choice(AWAKENED_ANIMAL_SPECIES)
        return {
            "name": f"{spec['species']} ({spec['heritage']})",
<<<<<<< HEAD
            "description": f"You were awakened as a {spec['species']} ({spec['size']}). Heritage: {spec['heritage']}. Natural Attack: {spec['unarmed']}."
=======
            "description": f"Awakened {spec['species']} ({spec['size']}). Natural Attack: {spec['unarmed']}."
>>>>>>> 187a873 (Successfully modularize heritages and subclasses, fix all engine import paths)
        }
    pool = ANCESTRY_HERITAGES.get(anc_key, GENERIC_HERITAGES)
    return random.choice(pool)
