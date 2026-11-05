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
    "alchemist": {
        "title": "Research Field",
        "options": [
            {"name": "Bomber", "description": "Specialized in thrown alchemical bombs and splash damage control."},
            {"name": "Chirurgeon", "description": "Medical master using Crafting for Medicine checks and creating restorative elixirs."},
            {"name": "Mutagenist", "description": "Transforms bodily capabilities through physical alchemical mutagens."},
            {"name": "Toxicologist", "description": "Masters weapon-applied poisons and elevated poison save DCs."}
        ]
    },
    "animist": {
        "title": "Apparition Practice",
        "options": [
            {"name": "Channeler", "description": "You allow apparitions to flood directly through your body, fueling powerful channeler stances and bursts."},
            {"name": "Sage", "description": "You commune deeply with the spirits of wisdom and memory to recall lost secrets and enhance spellcraft."},
            {"name": "Shaman", "description": "You guide restless spirits between the material realm and the spirit world, gaining curative and protective wards."}
        ]
    },
    "barbarian": {
        "title": "Instinct",
        "options": [
            {"name": "Animal Instinct", "description": "Your rage gives you powerful bestial unarmed strikes."},
            {"name": "Dragon Instinct", "description": "Your rage draws power from a draconic patron, adding elemental damage."},
            {"name": "Fury Instinct", "description": "Your rage is pure anger. You gain a 1st-level barbarian feat."},
            {"name": "Giant Instinct", "description": "You wield oversized weapons for massive additional rage damage."},
            {"name": "Spirit Instinct", "description": "Your rage channels ancestor spirits to fight undead and incorporeal targets."},
            {"name": "Superstition Instinct", "description": "A deep distrust of magic fuels your rage, granting bonuses against spells and temporary HP against magic."}
        ]
    },
    "bard": {
        "title": "Muse",
        "options": [
            {"name": "Enigma", "description": "Driven to uncover esoteric secrets, gaining Bardic Lore to Recall Knowledge on any subject."},
            {"name": "Maestro", "description": "Masters of performance, gaining the Lingering Composition focus spell."},
            {"name": "Polymath", "description": "Jack-of-all-trades; gain trained in Performance and Versatile Performance."},
            {"name": "Warrior", "description": "Martial skald; gain trained in martial weapons and medium armor."}
        ]
    },
    "champion": {
        "title": "Cause",
        "options": [
            {"name": "Paladin (Holy)", "description": "Your reaction is Retributive Strike to protect allies and strike back."},
            {"name": "Liberator (Holy)", "description": "Your reaction is Liberating Step to free allies from grab and immobilize effects."},
            {"name": "Redeemer (Holy)", "description": "Your reaction is Glimpse of Redemption to pacify enemies or sap their strikes."},
            {"name": "Tyrant (Unholy)", "description": "Your reaction is Iron Command to compel obedience and inflict mental torment or knock foes prone."},
            {"name": "Desecrator (Unholy)", "description": "Your reaction is Selfish Shield to absorb incoming damage with void power and boost your own resistance."},
            {"name": "Antipaladin (Unholy)", "description": "Your reaction is Destructive Vengeance to trade pain for amplified violence against your attacker."}
        ]
    },
    "cleric": {
        "title": "Doctrine",
        "options": [
            {"name": "Warpriest", "description": "Trained in medium armor and shields; martial weapon proficiency in deity's favored weapon."},
            {"name": "Cloistered Cleric", "description": "Mastery of divine magic; gain the Domain Initiate feat and increased spell DC."}
        ]
    },
    "commander": {
        "title": "Tactics Specialty",
        "options": [
            {"name": "Infantry Tactics", "description": "Specialized in ground formations, frontline shield walls, and coordinated melee pushes."},
            {"name": "Cavalry Tactics", "description": "Specialized in high mobility, shock charges, and hit-and-run mounted vanguard maneuvers."},
            {"name": "Naval Tactics", "description": "Specialized in boarding actions, boarding hooks, tight-quarter skirmishes, and aquatic battlefield control."},
            {"name": "Guerrilla Tactics", "description": "Specialized in ambush formations, rapid retreats, camouflage, and asymmetric skirmishing."}
        ]
    },
    "druid": {
        "title": "Druidic Order",
        "options": [
            {"name": "Animal Order", "description": "Bonds with an animal companion; gains Heal Animal order spell."},
            {"name": "Flame Order", "description": "Primal fire manipulator; gains Wildfire order spell."},
            {"name": "Leaf Order", "description": "Forest steward with a leshy familiar and Goodberry order spell."},
            {"name": "Stone Order", "description": "Deep earth sentinel; gains Crushing Ground order spell."},
            {"name": "Storm Order", "description": "Harnesses tempests and lightning; gains Tempest Surge order spell."},
            {"name": "Wave Order", "description": "Master of oceanic currents and tides; gains Rising Surf order spell."},
            {"name": "Wild Order", "description": "Shapeshifter tapping into primal morphology; gains Wild Shape."}
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
    "gunslinger": {
        "title": "Way",
        "options": [
            {"name": "Way of the Drifter", "description": "Masters fighting with a one-handed firearm in one hand and a melee weapon in the other."},
            {"name": "Way of the Pistolero", "description": "Specialized in single one-handed firearms and rapid duels."},
            {"name": "Way of the Sniper", "description": "Specialized in high-powered long range two-handed crossbows and firearms."},
            {"name": "Way of the Triggerbrand", "description": "Specialized in agile combat using versatile combination weapons."},
            {"name": "Way of the Vanguard", "description": "Specialized in close-quarters scatter weapons and heavy shotguns."}
        ]
    },
    "inventor": {
        "title": "Innovation",
        "options": [
            {"name": "Armor Innovation", "description": "Wields customized, modular power armor with defensive augmentations."},
            {"name": "Construct Innovation", "description": "Accompanied by a mechanical minion companion built for battle and utility."},
            {"name": "Weapon Innovation", "description": "Wields an over-engineered prototype weapon with unique offensive traits."}
        ]
    },
    "investigator": {
        "title": "Methodology",
        "options": [
            {"name": "Alchemical Sciences", "description": "Produces quick alchemical tinctures and investigative elixirs on the fly."},
            {"name": "Empiricism", "description": "Relies on lightning-fast sensory awareness and That's Odd perception checks."},
            {"name": "Forensic Medicine", "description": "Forensic examiner; supercharges Battle Medicine with extra healing and cooldown resets."},
            {"name": "Interrogation", "description": "Extracts clues through forceful social probing, Pointed Question, and lie detection."}
        ]
    },
    "kineticist": {
        "title": "Kinetic Gate",
        "options": [
            {"name": "Single Gate: Air", "description": "Pure air kineticist gaining Aerial Agility, Whispering Wind, and Four Winds impulses."},
            {"name": "Single Gate: Earth", "description": "Pure earth kineticist gaining Armor in Earth and Tremor impulses."},
            {"name": "Single Gate: Fire", "description": "Pure fire kineticist gaining Thermal Nimbus and Flying Flame impulses."},
            {"name": "Single Gate: Metal", "description": "Pure metal kineticist gaining Flashforge and Magnetic Shield defensive impulses."},
            {"name": "Single Gate: Water", "description": "Pure water kineticist gaining Ocean's Balm and Deflecting Wave impulses."},
            {"name": "Single Gate: Wood", "description": "Pure wood kineticist gaining Fresh Produce and Timber Sentinel barriers."},
            {"name": "Dual Gate: Fire & Earth", "description": "Composite kineticist channeling volcanic molten rock and Magma Leap."},
            {"name": "Dual Gate: Water & Wood", "description": "Composite kineticist nurturing life, spring water, and restorative surges."},
            {"name": "Dual Gate: Air & Metal", "description": "Composite kineticist manipulating magnetic cyclones and flying alloy shards."}
        ]
    },
    "magus": {
        "title": "Hybrid Study",
        "options": [
            {"name": "Inexorable Iron", "description": "Wields massive two-handed weapons and gains temporary HP when entering Arcane Cascade."},
            {"name": "Laughing Shadow", "description": "One-handed blade skirmisher; teleports via Dimensional Assault and deals extra damage to off-guard foes."},
            {"name": "Sparkling Targe", "description": "Shield and sword warden capable of blocking spells and physical strikes alike."},
            {"name": "Starlit Span", "description": "Channels Spellstrike through ranged weapons like bows and thrown blades."},
            {"name": "Twisting Tree", "description": "Transforms a humble staff into a versatile, agile, two-handed martial weapon."}
        ]
    },
    "oracle": {
        "title": "Mystery",
        "options": [
            {"name": "Battle", "description": "Curse of military struggle; gains heavy armor and martial weapon mastery."},
            {"name": "Bones", "description": "Walks the threshold of death; gains resistances to necromancy and void damage."},
            {"name": "Cosmos", "description": "Starlight and void buoyancy; gains physical resistance and elevated mobility."},
            {"name": "Flames", "description": "Blinding incinerating heat; covers the battlefield in ash and flame."},
            {"name": "Life", "description": "Overwhelming vitality; supercharges healing spells while suffering draining bleed."},
            {"name": "Lore", "description": "Overwhelming cosmic knowledge; gains Brain Drain and spontaneous Recall Knowledge."},
            {"name": "Tempest", "description": "Surrounded by rain, wind, and electrical storms that disrupt visibility and ranged attacks."}
        ]
    },
    "psychic": {
        "title": "Conscious Mind",
        "options": [
            {"name": "The Distant Gasp (Emotional Acceptance)", "description": "Telekinesis specialist (Mage Hand, Telekinetic Projectile). Key Attribute: Charisma."},
            {"name": "The Infinite Eye (Gathered Lore)", "description": "Precognition and sensory omniscience (Guidance, Glimpse Weakness). Key Attribute: Intelligence."},
            {"name": "The Oscillating Wave (Emotional Acceptance)", "description": "Thermodynamics blaster cycling fire and frost (Produce Flame, Ray of Frost). Key Attribute: Charisma."},
            {"name": "The Silent Whisper (Wandering Reverie)", "description": "Telepathy and psychological disruption (Message, Daze). Key Attribute: Charisma."},
            {"name": "The Tangible Dream (Precise Discipline)", "description": "Hard-light geometric shields and construct projection (Shield, Dancing Lights). Key Attribute: Intelligence."},
            {"name": "The Unbound Step (Precise Discipline)", "description": "Spatial warp and instantaneous mobility (Warp Step). Key Attribute: Intelligence."}
        ]
    },
    "ranger": {
        "title": "Hunter's Edge",
        "options": [
            {"name": "Flurry", "description": "Reduces Multiple Attack Penalty against your hunted prey to -3/-6 (or -2/-4 with agile weapons)."},
            {"name": "Outwit", "description": "Gain a +2 circumstance bonus to AC, Deception, Intimidation, Stealth, and Recall Knowledge against your hunted prey."},
            {"name": "Precision", "description": "Deal 1d8 additional precision damage on your first successful Strike each round against your hunted prey."}
        ]
    },
    "rogue": {
        "title": "Racket",
        "options": [
            {"name": "Mastermind", "description": "You use Recall Knowledge to make your foes flat-footed."},
            {"name": "Ruffian", "description": "You can use Sneak Attack with any simple weapon, not just agile or finesse weapons."},
            {"name": "Scoundrel", "description": "You feint with extreme grace and gain trained in Diplomacy and Deception."},
            {"name": "Thief", "description": "You can add your Dexterity modifier to damage rolls with finesse melee weapons."}
        ]
    },
    "sorcerer": {
        "title": "Bloodline",
        "options": [
            {"name": "Angelic (Divine)", "description": "Celestial patron providing Angelic Halo and divine healing spells."},
            {"name": "Demonic (Divine)", "description": "Abyssal heritage granting Glutton's Jaws and divine destruction."},
            {"name": "Draconic (Arcane)", "description": "Draconic heritage providing Dragon Claws focus spell and arcane spells."},
            {"name": "Fey (Primal)", "description": "Faerie heritage providing Faerie Dust and primal illusion/enchantment magic."}
        ]
    },
    "summoner": {
        "title": "Eidolon",
        "options": [
            {"name": "Beast Eidolon", "description": "Primal apex predator partner with enhanced charging and takedown strikes."},
            {"name": "Construct Eidolon", "description": "Clockwork or golem companion with physical damage resistances."},
            {"name": "Demon Eidolon", "description": "Abyssal juggernaut inflicting mental dread and savage combat maneuvers."},
            {"name": "Dragon Eidolon", "description": "Draconic partner with breath weapon and elemental breath scaling."},
            {"name": "Fey Eidolon", "description": "Trickster partner wielding innate primal enchantment and illusion spells."},
            {"name": "Undead Eidolon", "description": "Grave-bound companion with void vitality and draining touch."}
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
    "thaumaturge": {
        "title": "First Implement",
        "options": [
            {"name": "Amulet", "description": "Protective talisman granting defensive damage-reduction reactions against your exploited target."},
            {"name": "Chalice", "description": "Liquid relic providing continuous temporary HP and healing sips during combat."},
            {"name": "Lantern", "description": "Reveals unseen truths, invisible creatures, and provides illumination bonuses."},
            {"name": "Mirror", "description": "Reflective glass allowing you to project a simultaneous duplicate copy of yourself."},
            {"name": "Regalia", "description": "Emblem of authority boosting social checks and granting nearby allies damage bonuses."},
            {"name": "Tome", "description": "Esoteric grimoire providing daily rotating skill proficiencies and Recall Knowledge boons."},
            {"name": "Weapon", "description": "Imbued striking implement granting reactive strikes and critical disruption."}
        ]
    },
    "witch": {
        "title": "Patron Theme",
        "options": [
            {"name": "Curse (Occult)", "description": "Patron of malevolence; hexes enemies with Evil Eye and misfortune."},
            {"name": "Fate (Occult)", "description": "Patron of destiny; alters probability rolls with Nudge Fate."},
            {"name": "Fervor (Divine)", "description": "Patron of zealous faith; bolsters allies with divine fury and healing."},
            {"name": "Night (Occult)", "description": "Patron of darkness; shrouds foes in magical blindness and terror."},
            {"name": "Rune (Arcane)", "description": "Patron of inscribed magic; crafts arcane wards and sigil spells."},
            {"name": "Spinner of Threads (Occult)", "description": "Weaver of karmic lines; subtly guides fortune and repositioning."},
            {"name": "Wild (Primal)", "description": "Patron of primeval beasts and nature spirits; casts primal nature spells."}
        ]
    },
    "wizard": {
        "title": "Arcane School",
        "options": [
            {"name": "School of Battle Magic", "description": "Specialized in destructive evocation and abjuration spells."},
            {"name": "School of the Boundary", "description": "Specialized in teleportation, dimensional magic, and summoning."},
            {"name": "School of Unified Magical Theory", "description": "Universalist wizard gaining an extra drain familiar/focus ability."}
        ]
    }
}

def resolve_heritage(ancestry_name: str) -> Dict[str, str]:
    anc_key = ancestry_name.lower()
    if "awakened animal" in anc_key:
        spec = random.choice(AWAKENED_ANIMAL_SPECIES)
        return {
            "name": f"{spec['species']} ({spec['heritage']})",
            "description": f"You were awakened as a {spec['species']} ({spec['size']}). Heritage: {spec['heritage']}. Natural Attack: {spec['unarmed']}."
        }
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
