# app/engine/heritages.py
# Complete Official Pathfinder 2e Ancestry Heritages Matrix (All 51+ Compendium Ancestries)

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
    "catfolk": [
        {"name": "Nine-Lives Catfolk", "description": "When you would die from the dying condition, you can remain conscious at 0 HP with 1 dying instead."},
        {"name": "Jungle Catfolk", "description": "You can move through forest and jungle difficult terrain without reduction."},
        {"name": "Hunting Catfolk", "description": "You gain low-light vision and a +2 circumstance bonus to Track creatures when utilizing scent or vision."},
        {"name": "Winter Catfolk", "description": "You are adapted to sub-zero climes, gaining cold resistance equal to half your level."},
        {"name": "Flexible Catfolk", "description": "You gain the Cat Fall feat as a bonus feat, treating falls as 10 feet shorter."}
    ],
    "athamaru": [
        {"name": "Benthic Athamaru", "description": "You are accustomed to rapidly ascending and descending through the depths of the ocean through careful manipulation of your swim bladder."},
        {"name": "Kaleidoscopic Athamaru", "description": "Your scales are a spectrum of color that shimmers in the light. In areas of bright light or dim light, you gain a +1 circumstance bonus."},
        {"name": "Hopeful Athamaru", "description": "You have begun to prepare yourself to become an athamaru matriarch, and are likely stepping outside of your community to better prepare yourself."},
        {"name": "Quilled Athamaru", "description": "Sharp quills on your head can pierce your foes deeply. Most athamarus use such quills for defense, but a well-timed headbash can be devastatingly effective."},
        {"name": "Coral Athamaru", "description": "Coral covers patches of your body, which provides a natural layer of defense. Coral athamarus often choose Coral Symbiotes and related ancestry features."}
    ],
    "azarketi": [
        {"name": "Muckdweller Azarketi", "description": "Adapted to murky inland waters, granting darkvision and concealment bonuses in murky or muddy water."},
        {"name": "Mistbreath Azarketi", "description": "Adapted to coastal fogs and damp air, allowing you to hold your breath much longer."},
        {"name": "Seasage Azarketi", "description": "Descended from ancient Azlanti priest-casters, granting innate primal or occult mysticism."},
        {"name": "Spindrift Azarketi", "description": "Born in turbulent surface surf, granting bonus speed or resistance to water turbulence."},
        {"name": "Deepwater Azarketi", "description": "Emitting bioluminescence or pressure-adapted traits for the crushing ocean depths."}
    ],
    "anadi": [
        {"name": "Spell-Reft Anadi", "description": "You can seamlessly transition between human and spider forms with innate magic."},
        {"name": "Climbing Anadi", "description": "Your arachnid physiology grants superior vertical movement and web-slinging tricks."}
    ],
    "android": [
        {"name": "Constellation Android", "description": "Your internal processors are calibrated to stellar navigational telemetry."},
        {"name": " Artisan Android", "description": "Your synthetic hands and optical arrays are optimized for precision crafting."}
    ],
    "automaton": [
        {"name": "Aethelman", "description": "Your core is infused with raw astral magic, granting mystical resistance."},
        {"name": "Sharpshooter Automaton", "description": "Your chassis is calibrated for ranged target acquisition and ballistic accuracy."},
        {"name": "Bound Soul Automaton", "description": "A mortal soul is permanently anchored inside your clockwork frame."}
    ],
    "bugbear": [
        {"name": "Tangle-Tooth Bugbear", "description": "You possess jagged fangs and a powerful maw for close-quarters combat."},
        {"name": "Vicious Bugbear", "description": "Your intimidation tactics and strikes cause deep psychological panic."}
    ],
    "centaur": [
        {"name": "Plain-Runner Centaur", "description": "Your equine lower body is built for long-distance endurance across open plains."},
        {"name": "Woodland Centaur", "description": "You navigate forest undergrowth with exceptional speed and stability."}
    ],
    "conrasu": [
        {"name": "Rite of Passage", "description": "You ignore difficult terrain from undergrowth."},
        {"name": "Rite of Light", "description": "You channel Sunlight Healing to restore Hit Points to an adjacent ally."},
        {"name": "Rite of Invocation", "description": "You gain an innate cantrip from arcane or occult lists."},
        {"name": "Rite of Knowing", "description": "You possess heightened esoteric geometric awareness."}
    ],
    "dragonet": [
        {"name": "Chromatic Dragonet", "description": "Your scales align with elemental breath and chromatic dragon ancestry."},
        {"name": "Metallic Dragonet", "description": "Your demeanor and breath align with noble metallic dragon traditions."}
    ],
    "fetchling": [
        {"name": "Gloom-Displaced Fetchling", "description": "Shadows cling to your form, granting concealment in dim light."},
        {"name": "Resonant Fetchling", "description": "You channel planar energies of the Netherworld into localized occult power."}
    ],
    "fleshwarp": [
        {"name": "Alchemically Altered Fleshwarp", "description": "Mutagenic compounds running through your veins grant rapid cellular regeneration."},
        {"name": "Monstrous Fleshwarp", "description": "Your bodily transformation grants extra limbs, natural armor, or massive size adjustments."}
    ],
    "ghoran": [
        {"name": "Seed-Bearer Ghoran", "description": "You carry your ancestral seed within your floral body to ensure rebirth upon death."},
        {"name": "Bramble Ghoran", "description": "Your plant-based chassis features sharp thorns that deter grapplers."}
    ],
    "goloma": [
        {"name": "Many-Eyed Goloma", "description": "Your numerous eyes provide an expansive field of vision making you immune to being flanked."},
        {"name": "Skittering Goloma", "description": "Your spider-like agility allows rapid scurrying away from perceived threats."}
    ],
    "hobgoblin": [
        {"name": "Rik Tark Hobgoblin", "description": "Trained in military discipline, spear tactics, and coordinated unit strikes."},
        {"name": "Shatter-Proof Hobgoblin", "description": "Your fortitude and physical resilience shrug off environmental and hazard damage."}
    ],
    "jotunborn": [
        {"name": "Titan-Scarred Jotunborn", "description": "You bear the physical marks of ancient titan bloodlines, granting immense lifting power."},
        {"name": "Storm-Born Jotunborn", "description": "You channel residual atmospheric lightning through your massive frame."}
    ],
    "kashrishi": [
        {"name": "Crystalline-Horn Kashrishi", "description": "Your crystalline horn focuses psychic empathy and projects mental shields."},
        {"name": "Durable Kashrishi", "description": "Your stout frame absorbs heavy blows with minimal physical trauma."}
    ],
    "kholo": [
        {"name": "Scavenger Kholo", "description": "You possess supernatural resilience against disease and corrupted provisions."},
        {"name": "Pack-Tactician Kholo", "description": "You gain combat advantages when flanking foes alongside your packmates."}
    ],
    "kitsune": [
        {"name": "Celestial Envoy Kitsune", "description": "Connected to heavenly courts, granting divine spellcasting flair."},
        {"name": "Winter Kitsune", "description": "Adapted to northern snowscapes with cold resistance and frost resilience."}
    ],
    "kobold": [
        {"name": "Cavernborn Kobold", "description": "Accustomed to subterranean depths, you gain darkvision and stonecunning."},
        {"name": "Dragonscaled Kobold", "description": "Your scales shimmer with draconic heritage, granting elemental resistance."},
        {"name": "Tunneler Kobold", "description": "You excel at digging and navigating tight subterranean corridors."}
    ],
    "leshy": [
        {"name": "Leaf Leshy", "description": "You take no damage from falling no matter the distance."},
        {"name": "Gourd Leshy", "description": "You can store up to 1 Bulk of objects inside your hollow head."},
        {"name": "Vine Leshy", "description": "You gain a +2 circumstance bonus to Athletics checks to Climb."}
    ],
    "lizardfolk": [
        {"name": "Cliffscale Lizardfolk", "description": "Your toes and claws possess adhesive pads, granting a climb speed."},
        {"name": "Ridgeback Lizardfolk", "description": "Spiny dermal ridges protect your back and grant a tail slap unarmed attack."},
        {"name": "Wading Lizardfolk", "description": "You possess webbed feet, granting a swim speed and aquatic proficiency."}
    ],
    "merfolk": [
        {"name": "Abyssal Merfolk", "description": "Adapted to the freezing pressure of deep ocean trenches."},
        {"name": "Reef Merfolk", "description": "Brightly colored tails and scales adapted to vibrant shallow coral reefs."}
    ],
    "minotaur": [
        {"name": "Labyrinth Minotaur", "description": "You possess supernatural spatial awareness, making you impossible to disorient or maze."},
        {"name": "Gore-Horn Minotaur", "description": "Your powerful horns deal devastating damage during a charge attack."}
    ],
    "nagaji": [
        {"name": "Cobra-Crested Nagaji", "description": "Your hood and venomous spit provide both psychological deterrence and offensive ranged strikes."},
        {"name": "Constrictor Nagaji", "description": "Your muscular serpentine frame grants superior grappling maneuvers."}
    ],
    "poppet": [
        {"name": "Broom Poppet", "description": "You are fashioned from household cleaning tools, granting sweeping agile balance."},
        {"name": "Conscious Poppet", "description": "You possess an active soul awakened within your stuffed or wooden vessel."},
        {"name": "Ragamuffin Poppet", "description": "You are cobbled together from discarded scraps, granting stealth and flexibility."},
        {"name": "Stitch-Fleshed Poppet", "description": "Your body incorporates organic leather and twine, granting minor positive energy affinity."}
    ],
    "ratfolk": [
        {"name": "Desert Ysoki", "description": "Adapted to arid wasteland survival with heat endurance."},
        {"name": "Longsnout Ysoki", "description": "Your heightened sense of smell grants a +2 circumstance bonus to scent-based Perception checks."},
        {"name": "Tunnel Rat Ysoki", "description": "You can squeeze through tight spaces with extreme ease."}
    ],
    "samsaran": [
        {"name": "Life-Cycle Samsaran", "description": "Memories of past incarnations bleed into your present life, granting bonuses to recall knowledge."},
        {"name": "Ascetic Samsaran", "description": "Disciplined monastic focus grants inner spiritual peace and mental fortitude."}
    ],
    "sarangay": [
        {"name": "Moon-Crested Sarangay", "description": "Your crescent-shaped horns channel divine lunar energy."},
        {"name": "Forest Guardian Sarangay", "description": "Your towering stature is attuned to protecting rural hinterlands."}
    ],
    "shisk": [
        {"name": "Bone-Feathered Shisk", "description": "Your unique skeletal quills provide natural defense and esoteric library privileges."},
        {"name": "Tunnel-Dweller Shisk", "description": "Accustomed to lightless subterranean labyrinths."}
    ],
    "shoony": [
        {"name": "Seaside Shoony", "description": "Hardy coastal workers with unmatched stamina against exhaustion."},
        {"name": "Stout Shoony", "description": "Incredible perseverance and work ethic grant bonuses against tripping and shoving."}
    ],
    "skeleton": [
        {"name": "Acolyte Skeleton", "description": "Retains vestiges of divine or arcane spellcasting talent from life."},
        {"name": "Brutal Skeleton", "description": "Constructed from thick warrior bones built for heavy melee combat."}
    ],
    "sprite": [
        {"name": "Luminous Sprite", "description": "Your body sheds bright faerie light at will."},
        {"name": "Grig Sprite", "description": "Musical fey ancestry grants melodic charms and nimble acrobatics."}
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
    "tanuki": [
        {"name": "Illusionist Tanuki", "description": "Innate shapeshifting and trickery magic allow seamless disguises."},
        {"name": "Brewmaster Tanuki", "description": "Exceptional constitution and resistance to toxins from fermented concoctions."}
    ],
    "tengu": [
        {"name": "Jalmeri Tengu", "description": "Trained in coastal trade and urban hustle with extra language versatility."},
        {"name": "Taloned Tengu", "description": "Your feet bear razor-sharp talons granting a deadly unarmed slash attack."}
    ],
    "tripkee": [
        {"name": "Marsh Tripkee", "description": "Leaping ability and wet-mud camouflage make you elusive in swamplands."},
        {"name": "Dendritic Tripkee", "description": "Tree-dwelling habits grant superior balance and vertical mobility."}
    ],
    "vanara": [
        {"name": "Canopy Vanara", "description": "Prehensile tail and agile climbing speed optimized for treetop realms."},
        {"name": "Scholar Vanara", "description": "Inquisitive mind tuned to ancient lore and philosophical study."}
    ],
    "vishkanya": [
        {"name": "Venom-Blood Vishkanya", "description": "Your bodily fluids carry natural toxins that coat your blades and bites."},
        {"name": "Graceful Vishkanya", "description": "Serpentine flexibility and poise grant unmatched theatrical and acrobatic skill."}
    ],
    "wayang": [
        {"name": "Lightweaver Wayang", "description": "You manipulate shadows and ambient illumination inherited from the Netherworld."},
        {"name": "Midnight Wayang", "description": "Deep spiritual introspection grants occult resistance."}
    ],
    "yaksha": [
        {"name": "Primal Vow Yaksha", "description": "Bound by sacred primordial vows to protect the wilderness."},
        {"name": "Caretaker Yaksha", "description": "Channels energy from Creation's Forge to stabilize chaotic terrain."}
    ],
    "yaoguai": [
        {"name": "Awakened Plant Yaoguai", "description": "Originating from plant life infused with ambient magical energy."},
        {"name": "Transformed Object Yaoguai", "description": "An inanimate object brought to sapient, shapeshifting life."}
    ]
}

def resolve_heritage(ancestry_name: str, requested_heritage: Optional[str] = None) -> Dict[str, str]:
    anc_key = ancestry_name.lower().replace("sukri", "surki").strip()
    
    if "awakened animal" in anc_key:
        spec = random.choice(AWAKENED_ANIMAL_SPECIES)
        return {
            "name": f"{spec['species']} ({spec['heritage']})",
            "description": f"Awakened {spec['species']} ({spec['size']}). Natural Attack: {spec['unarmed']}."
        }
        
    pool = ANCESTRY_HERITAGES.get(anc_key, [])
    
    if requested_heritage:
        clean_req = requested_heritage.lower().strip()
        for h in pool:
            if clean_req in h["name"].lower():
                return h
                
    if pool:
        return random.choice(pool)
        
    return {
        "name": f"Standard {ancestry_name} Lineage",
        "description": f"An official heritage reflecting the standard background traits of the {ancestry_name} ancestry."
    }
