# app/engine/heritages.py
# Comprehensive Official Pathfinder 2e Ancestry Heritages Matrix

import random
from typing import Dict, Any, List, Optional

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
        {"name": "Half-Orc (Dromaar)", "description": "You gain low-light vision and the orc trait."},
        {"name": "Wintertouched Human", "description": "You adapt to frigid climes and gain cold resistance equal to half your level."}
    ],
    "dwarf": [
        {"name": "Strong-Blooded Dwarf", "description": "You gain poison resistance and a +2 bonus to poison saving throws."},
        {"name": "Rock Dwarf", "description": "You gain a +2 circumstance bonus to your Fortitude or Reflex DC against Shove or Trip."},
        {"name": "Forge Dwarf", "description": "You gain fire resistance equal to half your level (minimum 1)."},
        {"name": "Death Warden Dwarf", "description": "You gain a +2 circumstance bonus to saving throws against necromancy effects."}
    ],
    "elf": [
        {"name": "Ancient Elf", "description": "You gain a multiclass dedication feat at 1st level."},
        {"name": "Cavern Elf", "description": "You gain darkvision, allowing you to see in the dark without light."},
        {"name": "Woodland Elf", "description": "You can always use the Take Cover action in natural terrain."},
        {"name": "Whisper Elf", "description": "You gain a +2 circumstance bonus to Seek creatures using hearing."}
    ],
    "goblin": [
        {"name": "Unbreakable Goblin", "description": "You gain 10 Hit Points from your ancestry instead of 6."},
        {"name": "Razortooth Goblin", "description": "You gain a jaws unarmed attack that deals 1d6 piercing damage."},
        {"name": "Charhide Goblin", "description": "You gain fire resistance equal to half your level (minimum 1)."},
        {"name": "Snow Goblin", "description": "You gain cold resistance equal to half your level (minimum 1)."}
    ],
    "halfling": [
        {"name": "Gutsy Halfling", "description": "Your success against an emotion effect becomes a critical success."},
        {"name": "Nomadic Halfling", "description": "You speak two additional languages."},
        {"name": "Wildwood Halfling", "description": "You ignore difficult terrain caused by bushes and thick foliage."}
    ],
    "gnome": [
        {"name": "Fey-Touched Gnome", "description": "You gain a primal cantrip of your choice."},
        {"name": "Sensate Gnome", "description": "You gain imprecise scent out to 30 feet."},
        {"name": "Umbral Gnome", "description": "You gain darkvision."}
    ],
    "orc": [
        {"name": "Badlands Orc", "description": "You gain cold and heat resistance equal to half your level."},
        {"name": "Hold-Scarred Orc", "description": "You gain 12 Hit Points from your ancestry instead of 10, and Diehard feat."},
        {"name": "Rainfall Orc", "description": "You gain a +2 circumstance bonus to Athletics checks to Swim."}
    ],
    "poppet": [
        {"name": "Broom Poppet", "description": "You are fashioned from household cleaning tools, granting sweeping agile balance."},
        {"name": "Conscious Poppet", "description": "You possess an active soul awakened within your stuffed or wooden vessel."},
        {"name": "Ragamuffin Poppet", "description": "You are cobbled together from discarded scraps, granting stealth and flexibility."},
        {"name": "Stitch-Fleshed Poppet", "description": "Your body incorporates organic leather and twine, granting minor positive energy affinity."}
    ],
    "automaton": [
        {"name": "Aethelman", "description": "Your core is infused with raw astral magic, granting mystical resistance."},
        {"name": "Sharpshooter Automaton", "description": "Your chassis is calibrated for ranged target acquisition and ballistic accuracy."},
        {"name": "Bound Soul Automaton", "description": "A mortal soul is permanently anchored inside your clockwork frame."}
    ],
    "anadi": [
        {"name": "Spell-Reft Anadi", "description": "You can seamlessly transition between human and spider forms with innate magic."},
        {"name": "Climbing Anadi", "description": "Your arachnid physiology grants superior vertical movement and web-slinging tricks."}
    ],
    "kobold": [
        {"name": "Cavernborn Kobold", "description": "Accustomed to subterranean depths, you gain darkvision and stonecunning."},
        {"name": "Dragonscaled Kobold", "description": "Your scales shimmer with draconic heritage, granting elemental resistance corresponding to your patron dragon."},
        {"name": "Tunneler Kobold", "description": "You excel at digging and navigating tight subterranean corridors."}
    ],
    "lizardfolk": [
        {"name": "Cliffscale Lizardfolk", "description": "Your toes and claws possess adhesive pads, granting a climb speed."},
        {"name": "Ridgeback Lizardfolk", "description": "Spiny dermal ridges protect your back and grant a tail slap unarmed attack."},
        {"name": "_${Wading Lizardfolk}_", "description": "You possess webbed feet, granting a swim speed and aquatic proficiency."},
        {"name": "Wading Lizardfolk", "description": "You possess webbed feet, granting a swim speed and aquatic proficiency."}
    ],
    "ratfolk": [
        {"name": "Desert Ysoki", "description": "Adapted to arid wasteland survival with heat endurance."},
        {"name": "Longsnout Ysoki", "description": "Your heightened sense of smell grants a +2 circumstance bonus to scent-based Perception checks."},
        {"name": "Tunnel Rat Ysoki", "description": "You can squeeze through tight spaces with extreme ease."}
    ],
    "tengu": [
        {"name": "Jalmeri Tengu", "description": "Trained in coastal trade and urban hustle with extra language versatility."},
        {"name": "Taloned Tengu", "description": "Your feet bear razor-sharp talons granting a deadly unarmed slash attack."}
    ],
    "kitsune": [
        {"name": "Celestial Envoy Kitsune", "description": "Connected to heavenly courts, granting divine spellcasting flair."},
        {"name": "Winter Kitsune", "description": "Adapted to northern snowscapes with cold resistance and frost resilience."}
    ],
    "strix": [
        {"name": "Nocturnal Strix", "description": "Your eyes excel in pitch darkness, granting superior darkvision."},
        {"name": "Wingclipped Strix", "description": "Though your flight is restrained, your ground agility and athletic prowess are heightened."}
    ],
    "surki": [
        {"name": "Breaker Surki", "description": "You gain a 1d4 slashing claw unarmed attack (agile, finesse, versatile B)."},
        {"name": "Elytron Surki", "description": "You take no damage from falling regardless of distance."},
        {"name": "Hardshell Surki", "description": "You can etch armor runes directly onto your natural carapace."},
        {"name": "Lantern Surki", "description": "You can shed magical light from your abdomen."}
    ],
    "conrasu": [
        {"name": "Rite of Passage", "description": "You ignore difficult terrain from undergrowth."},
        {"name": "Rite of Light", "description": "You channel Sunlight Healing to restore Hit Points to an adjacent ally."},
        {"name": "Rite of Invocation", "description": "You gain an innate cantrip from arcane or occult lists."},
        {"name": "Rite of Knowing", "description": "You possess heightened esoteric geometric awareness."}
    ],
    "leshy": [
        {"name": "Leaf Leshy", "description": "You take no damage from falling no matter the distance."},
        {"name": "Gourd Leshy", "description": "You can store up to 1 Bulk of objects inside your hollow head."},
        {"name": "Vine Leshy", "description": "You gain a +2 circumstance bonus to Athletics checks to Climb."}
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
            "description": f"Awakened {spec['species']} ({spec['size']}). Natural Attack: {spec['unarmed']}."
        }
    pool = ANCESTRY_HERITAGES.get(anc_key, GENERIC_HERITAGES)
    return random.choice(pool)
