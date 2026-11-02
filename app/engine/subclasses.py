import random
from typing import Dict, Any, List, Optional

# Ancestry Heritages Matrix
ANCESTRY_HERITAGES: Dict[str, List[Dict[str, str]]] = {
    "human": [
        {"name": "Versatile Human", "description": "You gain a general feat of your choice at 1st level."},
        {"name": "Skilled Human", "description": "You become trained in one additional skill of your choice."},
        {"name": "Half-Elf (Aiuvarin)", "description": "You gain low-light vision and the elf trait."},
        {"name": "Half-Orc (Dromaar)", "description": "You gain low-light vision and the orc trait."}
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
    "leshy": [
        {"name": "Leaf Leshy", "description": "You take no damage from falling no matter the distance."},
        {"name": "Gourd Leshy", "description": "You can store up to 1 Bulk of objects inside your hollow head."},
        {"name": "Vine Leshy", "description": "You gain a +2 circumstance bonus to Athletics checks to Climb."}
    ]
}

# Generic Versatile Fallback for other ancestries
GENERIC_HERITAGES = [
    {"name": "Versatile Heritage", "description": "You gain a general feat of your choice at 1st level."},
    {"name": "Skilled Heritage", "description": "You become trained in one additional skill."}
]

# Class Subclasses Matrix
CLASS_SUBCLASSES: Dict[str, Dict[str, Any]] = {
    "animist": {
        "title": "Apparition Practice",
        "options": [
            {"name": "Channeler", "description": "You allow apparitions to flood directly through your body, fueling powerful channeler stances and bursts."},
            {"name": "Sage", "description": "You commune deeply with the spirits of wisdom and memory to recall lost secrets and enhance spellcraft."},
            {"name": "Shaman", "description": "You guide restless spirits between the material realm and the spirit world, gaining curative and protective wards."}
        ]
    },
    "exemplar": {
        "title": "Ikon",
        "options": [
            {"name": "Body Ikon (Gleaming Scar)", "description": "Your physical vessel is marked with transcendent divine endurance."},
            {"name": "Weapon Ikon (Mighty Weapon)", "description": "Your weapon channels mythological strikes that cleave through enemy defenses."},
            {"name": "Worn Ikon (Radiant Crown)", "description": "You bear a relic radiating sovereign majesty and authority."}
        ]
    },
    "rogue": {
        "title": "Racket",
        "options": [
            {"name": "Thief", "description": "You can add your Dexterity modifier to damage rolls with finesse melee weapons."},
            {"name": "Ruffian", "description": "You can use Sneak Attack with any simple weapon, not just agile or finesse weapons."},
            {"name": "Scoundrel", "description": "You feint with extreme grace and gain trained in Diplomacy and Deception."},
            {"name": "Mastermind", "description": "You use Recall Knowledge to make your foes flat-footed."}
        ]
    },
    "barbarian": {
        "title": "Instinct",
        "options": [
            {"name": "Fury Instinct", "description": "Your rage is pure anger. You gain a 1st-level barbarian feat."},
            {"name": "Dragon Instinct", "description": "Your rage draws power from a draconic patron, adding elemental damage."},
            {"name": "Giant Instinct", "description": "You wield oversized weapons for massive additional rage damage."},
            {"name": "Spirit Instinct", "description": "Your rage channels ancestor spirits to fight undead and incorporeal targets."},
            {"name": "Animal Instinct", "description": "Your rage gives you powerful bestial unarmed strikes."}
        ]
    },
    "cleric": {
        "title": "Doctrine",
        "options": [
            {"name": "Warpriest", "description": "Trained in medium armor and shields; martial weapon proficiency in deity's favored weapon."},
            {"name": "Cloistered Cleric", "description": "Mastery of divine magic; gain the Domain Initiate feat and increased spell DC."}
        ]
    },
    "champion": {
        "title": "Cause",
        "options": [
            {"name": "Paladin (Holy)", "description": "Your reaction is Retributive Strike to protect allies and strike back."},
            {"name": "Liberator (Holy)", "description": "Your reaction is Liberating Step to free allies from grab and immobilize effects."},
            {"name": "Redeemer (Holy)", "description": "Your reaction is Glimpse of Redemption to pacify enemies or sap their strikes."}
        ]
    },
    "bard": {
        "title": "Muse",
        "options": [
            {"name": "Maestro", "description": "Masters of performance, gaining the Lingering Composition focus spell."},
            {"name": "Polymath", "description": "Jack-of-all-trades; gain trained in Performance and Versatile Performance."},
            {"name": "Warrior", "description": "Martial skald; gain trained in martial weapons and medium armor."}
        ]
    },
    "wizard": {
        "title": "Arcane School",
        "options": [
            {"name": "School of Battle Magic", "description": "Specialized in destructive evocation and abjuration spells."},
            {"name": "School of Unified Magical Theory", "description": "Universalist wizard gaining an extra drain familiar/focus ability."},
            {"name": "School of the Boundary", "description": "Specialized in teleportation, dimensional magic, and summoning."}
        ]
    },
    "sorcerer": {
        "title": "Bloodline",
        "options": [
            {"name": "Draconic (Arcane)", "description": "Draconic heritage providing Dragon Claws focus spell and arcane spells."},
            {"name": "Angelic (Divine)", "description": "Celestial patron providing Angelic Halo and divine healing spells."},
            {"name": "Fey (Primal)", "description": "Faerie heritage providing Faerie Dust and primal illusion/enchantment magic."},
            {"name": "Demonic (Divine)", "description": "Abyssal heritage granting Glutton's Jaws and divine destruction."}
        ]
    },
    "swashbuckler": {
        "title": "Style",
        "options": [
            {"name": "Braggart", "description": "You gain panache by demoralizing foes with Demoralize checks."},
            {"name": "Fencer", "description": "You gain panache by faking out your foes using Create a Diversion or Feint."},
            {"name": "Gymnast", "description": "You gain panache by overpowering foes with Grapple, Shove, or Trip."}
        ]
    },
    "gunslinger": {
        "title": "Way",
        "options": [
            {"name": "Way of the Pistolero", "description": "Specialized in single one-handed firearms and rapid duels."},
            {"name": "Way of the Sniper", "description": "Specialized in high-powered long range two-handed crossbows and firearms."},
            {"name": "Way of the Vanguard", "description": "Specialized in close-quarters scatter weapons and heavy shotguns."}
        ]
    },
    "kineticist": {
        "title": "Kinetic Gate",
        "options": [
            {"name": "Single Gate: Fire", "description": "Pure fire kineticist gaining Thermal Nimbus and Flying Flame impulses."},
            {"name": "Single Gate: Water", "description": "Pure water kineticist gaining Ocean's Balm and Deflecting Wave impulses."},
            {"name": "Single Gate: Earth", "description": "Pure earth kineticist gaining Armor in Earth and Tremor impulses."},
            {"name": "Dual Gate: Fire & Earth", "description": "Composite kineticist channeling volcanic molten rock and lava impulses."}
        ]
    }
}

def resolve_heritage(ancestry_name: str) -> Dict[str, str]:
    anc_key = ancestry_name.lower()
    pool = ANCESTRY_HERITAGES.get(anc_key, GENERIC_HERITAGES)
    return random.choice(pool)

def resolve_subclass(class_name: str) -> Optional[Dict[str, str]]:
    cls_key = class_name.lower()
    data = CLASS_SUBCLASSES.get(cls_key)
    if not data:
        return None
    choice = random.choice(data["options"])
    return {
        "title": data["title"],
        "name": choice["name"],
        "description": choice["description"]
    }
