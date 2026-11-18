import random

# Linguistic family mapping for every official Pathfinder 2e & Remaster Ancestry
ANC_LINGUISTIC_FAMILIES = {
    # Humanoid / Common
    "human": "human", "halfling": "halfling", "dwarf": "dwarf", "elf": "elf",
    "aiuvarin": "elf", "dromaar": "orc", "samsaran": "celestial", "wayang": "shadow",
    # Goblins & Small Folk
    "goblin": "goblin", "gnome": "gnome", "kobold": "kobold", "shoony": "shoony",
    "grippli": "grippli", "tripkee": "grippli", "tanuki": "fae",
    # Orcs & Brutal/Martial
    "orc": "orc", "hobgoblin": "orc", "bugbear": "orc", "minotaur": "orc",
    "lesh": "leshy", "leshy": "leshy",
    # Beastkin & Animal Folk
    "catfolk": "beast", "amurrun": "beast", "lizardfolk": "beast", "iruxi": "beast",
    "ratfolk": "beast", "ysoki": "beast", "tengu": "avian", "anadi": "beast",
    "kashrishi": "beast", "vanara": "beast", "centaur": "beast", "kholo": "beast",
    "gnoll": "beast", "awakened animal": "beast", "sarangay": "beast",
    # Aquatic & Planar
    "azarketi": "aquatic", "merfolk": "aquatic", "athamaru": "aquatic",
    "undine": "aquatic", "sylph": "elemental", "ifrit": "elemental",
    "iftit": "elemental", "oread": "elemental", "suli": "elemental",
    "ardande": "leshy", "talos": "construct",
    # Exotic / Magical / Construct / Draconic
    "automaton": "construct", "conrasu": "construct", "poppet": "construct",
    "android": "construct", "skeleton": "undead", "dhampir": "undead",
    "fleshwarp": "fleshwarp", "fetchling": "shadow", "kayal": "shadow",
    "shisk": "underground", "strix": "avian",
    "surki": "exotic", "goloma": "exotic", "vishkanya": "exotic",
    "nagaji": "draconic", "dragonet": "draconic", "dragonblood": "draconic",
    "kitsune": "fae", "sprite": "fae", "changeling": "fae",
    "nephilim": "celestial", "aasimar": "celestial", "yaksha": "celestial",
    "tiefling": "fiendish", "ganzi": "exotic", "aphorite": "construct",
    "duskwalker": "undead", "hungerseed": "fiendish",
}

LINGUISTIC_BANKS = {
    "human": {
        "prefixes": ["Kat", "Thal", "Zan", "Olg", "Cyr", "Row", "Mar", "Vand", "Dor", "Elen", "Marc", "Val", "Ald", "Cor", "Bren", "Luc", "Ser", "Gar", "Jul", "Cass"],
        "medials": ["er", "and", "in", "ist", "or", "ur", "al", "ev", "ar", "on"],
        "suffixes": ["a", "en", "us", "ia", "os", "is", "an", "er", "ette", "ric", "lyn", "ardo"],
        "surnames": ["Vancaskerkin", "Cold-Broker", "Ashen-Gale", "Swift-River", "Ironwood", "Markov", "Brightwood", "Crestfall", "Harrowfield", "Thornwall", "Stormwatch", "Silverbrook", "Alderidge", "Blackwater", "Redwyne"]
    },
    "dwarf": {
        "prefixes": ["Thor", "Bal", "Dorg", "Thrain", "Mor", "Dol", "Krag", "Dar", "Tor", "Gar", "Hjal", "Bryn", "Kaz", "Brok", "Dain", "Gim", "Snor", "Dur", "Vond", "Rur"],
        "medials": ["grim", "gar", "mun", "dur", "fin", "kan", "dor", "bek", "rik", "var"],
        "suffixes": ["ar", "in", "um", "ok", "ir", "ak", "gran", "heim", "orn", "ik"],
        "surnames": ["Lodestone", "Anvil-Bane", "Iron-Foot", "Copper-Beard", "Stone-Hearth", "Shield-Breaker", "Coppervein", "Deepdelver", "Goldpick", "Granitehelm", "Forgeheart", "flintstrike", "Oathhammer", "Runemantle"]
    },
    "elf": {
        "prefixes": ["Ael", "Fael", "Syl", "Elar", "Tari", "Cyr", "Gal", "Val", "Naer", "Lyr", "Thia", "Cal", "Fin", "Aer", "Vael", "Sel", "Ily", "Ryn", "Thal", "Lor"],
        "medials": ["on", "en", "ath", "and", "or", "ist", "ael", "ir", "yn", "ess"],
        "suffixes": ["in", "a", "ion", "iss", "eth", "el", "ian", "as", "riel", "ora", "iel", "an"],
        "surnames": ["Meliamne", "Silver-Frond", "Moon-Whisper", "Starlight", "Glow-Brook", "Wind-Runner", "Silvermist", "Dawnleaf", "Starweaver", "Sunspire", "Mistrunner", "Duskwhisper", "Glimmerbough", "Dewsong"]
    },
    "goblin": {
        "prefixes": ["Zaz", "Muck", "Snag", "Grix", "Krag", "Boil", "Rot", "Wart", "Zap", "Skum", "Snot", "Fizz", "Gnar", "Chomp", "Snik", "Blit", "Crag", "NIB", "Zog", "Skab"],
        "medials": ["ble", "gie", "ik", "og", "rat", "snit", "gut", "zog", "nik", "bog"],
        "suffixes": ["zle", "toot", "snag", "gut", "face", "tooth", "pox", "bang", "biter", "lick"],
        "surnames": ["Muck-Raker", "Trash-Finder", "Bone-Gnawer", "Swamp-Stalker", "Gutter-Snipe", "Mudlicker", "Fire-Starter", "Pickle-Chewer", "Dog-Slicer", "Rust-Bucket", "Toad-Catcher", "ash-Sniffer"]
    },
    "halfling": {
        "prefixes": ["Milo", "Finn", "Ros", "Pip", "Dais", "Mir", "Cor", "Tans", "Jasp", "Bramb", "Tob", "Pos", "Merr", "Sam", "Bell", "Ned", "Wren", "Lark", "Hobb", "Clov"],
        "medials": ["dob", "will", "per", "cot", "lock", "tans", "bur", "pod", "kin", "berry"],
        "suffixes": ["y", "o", "a", "er", "en", "ip", "ie", "in", "by", "son"],
        "surnames": ["Brightwood", "Apple-Orchard", "Hill-Topper", "Tea-Kettle", "Bramble-Foot", "Brambletoes", "Goodbarrel", "Underbough", "Warmhearth", "Thistlewhistle", "Meadowbrook", "Honeycomb", "Puddlejumper"]
    },
    "orc": {
        "prefixes": ["Brak", "Grom", "Thar", "Urz", "Karg", "Mog", "Dur", "Zurg", "Kull", "Rath", "Thokk", "Grish", "Vorg", "Drak", "Skar", "Morg", "Bruk", "Gor", "Kraz", "Naz"],
        "medials": ["gar", "rok", "ash", "lok", "nak", "gor", "mak", "tar", "ruk", "zul"],
        "suffixes": ["ok", "ash", "ar", "ul", "az", "grom", "oth", "ak", "urg", "or"],
        "surnames": ["Blood-Eye", "Skull-Splitter", "Iron-Hide", "Tusk-Biter", "Storm-Caller", "Doomhammer", "Bone-Crusher", "Ash-Fist", "War-Born", "Grim-Tusk", "gore-Cleaver", "Shattershield", "Redfang"]
    },
    "gnome": {
        "prefixes": ["Wizz", "Fiz", "Bix", "Nim", "Pimb", "Zook", "Bimb", "Tink", "Glim", "Snick", "Quib", "Dabb", "Zany", "Pip", "Jink", "Bozz", "Flib", "Wob", "Sprock", "Gizz"],
        "medials": ["wig", "pop", "tick", "bam", "zop", "flip", "whir", "bloop", "snick", "tock"],
        "suffixes": ["snap", "spark", "wink", "dle", "widget", "bop", "fizz", "spring", "gear", "whistle"],
        "surnames": ["Clock-Winder", "Glimmer-Spark", "Tumble-Down", "Pebble-Pouch", "Spring-Loaded", "Fizzle-Bang", "Copper-Coil", "Bright-Button", "Prism-Gazer", "Whirligig", "Tinker-bell", "Boggle-Box"]
    },
    "kobold": {
        "prefixes": ["Zix", "Krix", "Vex", "Ska", "Mir", "Trix", "Rix", "Zor", "Vrix", "Kess", "Snix", "Drax", "Pex", "Nyx", "Razz", "Qix", "Skiv", "Zek", "Tik", "Brix"],
        "medials": ["iss", "kiz", "vaz", "rix", "sazz", "vex", "nik", "zar", "kess", "tix"],
        "suffixes": ["ax", "ix", "us", "os", "rix", "en", "ak", "is", "ex", "oz"],
        "surnames": ["Ashen-Gale", "Scale-Singer", "Dragon-Worship", "Tail-Lash", "Cave-Crawler", "Coldscale", "Trap-Maker", "Spark-Fang", "Gem-Sniffer", "Tunnel-Runner", "Wyrm-Sworn", "Soot-Claw"]
    },
    "leshy": {
        "prefixes": ["Bramble", "Spore", "Moss", "Fern", "Root", "Seed", "Petal", "Bark", "Leaf", "Juniper", "Thorn", "Acorn", "Willow", "Clover", "Cedar", "Nettle", "Hazel", "Rowan", "Alder", "Birch"],
        "medials": ["heart", "weaver", "stride", "bloom", "glen", "bough", "sap", "bud", "vine", "stem"],
        "suffixes": ["ling", "ton", "ish", "keeper", "walker", "sprout", "bloom", "shade", "root", "bark"],
        "surnames": ["Green-Thumb", "Sun-Seeker", "Dew-Drinker", "Canopy-Runner", "Brambleheart", "Root-Binder", "Pollen-Drift", "Deep-Loam", "Rain-Catcher", "Bark-Skin", "Wild-Bloom", "Grove-Tender"]
    },
    "beast": {
        "prefixes": ["Rem", "Sul", "Tar", "Kha", "Zul", "Hiss", "Ske", "Voh", "Thok", "Nix", "Kar", "Raksh", "Zan", "Mow", "Korr", "Vash", "Tigr", "Panth", "Lup", "Urs"],
        "medials": ["ash", "esh", "irr", "uss", "ick", "su", "arr", "ok", "an", "ur"],
        "suffixes": ["a", "en", "us", "ar", "ok", "iss", "on", "ik", "ra", "esh"],
        "surnames": ["Wave-Crest", "Sun-Prowler", "Shadow-Stalker", "Swamp-Stalker", "Scale-Keeper", "Feather-Step", "Swift-Claw", "Night-Hunter", "mane-Runner", "Pack-Leader", "Wild-Fang", "Dusk-Prowler", "Thorn-Pelt"]
    },
    "shoony": {
        "prefixes": ["Bask", "Pug", "Snuff", "Mugg", "Barn", "Toby", "Bisc", "Ruf", "Padd", "Chum", "Wagg", "Bork"],
        "medials": ["le", "er", "by", "sy", "kin", "ton"],
        "suffixes": ["s", "y", "o", "ie", "ton", "wick"],
        "surnames": ["Mud-Puddle", "Warm-Hearth", "Loyal-Heart", "Turnip-Patch", "Soft-Ear", "Burrow-Guard", "Good-Boy", "Hearth-Keeper"]
    },
    "grippli": {
        "prefixes": ["Kerm", "Rib", "Croak", "Bog", "Glim", "Padd", "Tad", "Mire", "Reed", "Hopp", "Slick", "Plop"],
        "medials": ["bit", "bl", "ip", "og", "ak", "ul"],
        "suffixes": ["it", "op", "ak", "in", "y", "os"],
        "surnames": ["Lily-Pad", "Marsh-Leaper", "Reed-Singer", "Mist-Hopper", "Bog-Trotter", "Dew-Tongue", "Swamp-strider", "Canopy-Glider"]
    },
    "aquatic": {
        "prefixes": ["Tid", "Mar", "Cor", "Ner", "Pel", "Sal", "Ebb", "Thal", "Brin", "Kelp", "Ond", "Aqu", "Syr", "Trit", "Delph"],
        "medials": ["ath", "or", "un", "iss", "al", "en", "os", "ir"],
        "suffixes": ["us", "a", "ia", "os", "is", "on", "iel", "ora"],
        "surnames": ["Deep-Watcher", "Tide-Singer", "Coral-Gazer", "Abyssal-Born", "Wave-Treader", "Pearl-Diver", "Current-Rider", "Foam-Walker", "Trench-Guard", "Reef-Keeper", "salt-Breeze"]
    },
    "elemental": {
        "prefixes": ["Ign", "Zeph", "Terr", "Aure", "Pyr", "Cind", "Gale", "Crag", "Breez", "Magm", "Flint", "Siroc", "temp", "Onyx", "Quarz"],
        "medials": ["is", "or", "an", "eth", "ar", "ul", "on", "yr"],
        "suffixes": ["us", "a", "os", "is", "on", "ar", "iel", "ax"],
        "surnames": ["Ember-Heart", "Gale-Strider", "Stone-Born", "Spark-Weaver", "Cinder-Step", "Cloud-Walker", "Granite-Fist", "Storm-Caller", "Ash-Dancer", "Sun-forged"]
    },
    "construct": {
        "prefixes": ["Aegis", "Cog", "Piston", "Brass", "Iron", "Unit", "Vessel", "Remnant", "Axiom", "Cipher", "Vector", "Bastion", "Anvil", "Chrono", "Servo", "Ferrum"],
        "medials": ["-01", "-07", "-42", "-99", "-X", "-Prime", "-Alpha", "-Omega", "-IV", "-IX"],
        "suffixes": ["Core", "Sentinel", "Guardian", "Construct", "Warden", "Frame", "Engine", "Vanguard"],
        "surnames": ["Clockwork Vanguard", "Gilded Sentinel", "Cogheart", "Ironclad", "Awakened Core", "Brass-Bound", "Steel-Soul", "Runeforged", "Gear-wright", "Aether-Spindle", "Titan-Frame"]
    },
    "undead": {
        "prefixes": ["Grim", "Rattle", "Sepulch", "Dusk", "Harr", "Marr", "Vesp", "Crypt", "Mort", "Ash", "Blight", "Shade", "Wraith", "Osse"],
        "medials": ["or", "ath", "ul", "un", "er", "is", "ov", "an"],
        "suffixes": ["ix", "us", "is", "or", "en", "a", "os", "heim"],
        "surnames": ["Bone-Collector", "Soul-Binder", "Grave-Walker", "Tomb-Guard", "Ashen-Wraith", "Death-Whisper", "Marrow-Born", "Crypt-Keeper", "Pale-Shroud", "Hollow-Crown", "Dust-Walker"]
    },
    "shadow": {
        "prefixes": ["Nyx", "Umbr", "Vesper", "Dusk", "Noct", "Shad", "Ereb", "Teneb", "Gloom", "Sable", "Murk", "Cimmer"],
        "medials": ["al", "is", "or", "en", "ath", "yr", "os", "un"],
        "suffixes": ["is", "a", "os", "on", "eth", "ia", "us", "ra"],
        "surnames": ["Shadow-Step", "Dusk-Weaver", "Night-Veil", "Umbral-Gaze", "Gloam-Walker", "Void-Strider", "Midnight-Sun", "Dark-Mirror", "Twilight-Born"]
    },
    "avian": {
        "prefixes": ["Aer", "Tal", "Kestrel", "Corv", "Falc", "Zeph", "Plum", "Skye", "Rapt", "Aquil", "Gryph", "Swoop"],
        "medials": ["on", "is", "ar", "en", "ath", "ir", "os"],
        "suffixes": ["ix", "a", "us", "or", "is", "on", "iel"],
        "surnames": ["Sky-Talon", "Wind-Wing", "Cloud-Perch", "Gale-Feather", "High-Soarer", "Storm-Beak", "Crag-Nester", "Sun-Wing", "Feather-Fall"]
    },
    "underground": {
        "prefixes": ["Chasm", "Deep", "Shale", "Onyx", "Grot", "Subt", "Basalt", "Caver", "Umber", "Dusk", "Geode", "Flint"],
        "medials": ["or", "an", "is", "ul", "ek", "ar"],
        "suffixes": ["is", "ak", "on", "us", "a", "eth"],
        "surnames": ["Deep-Walker", "Stone-Lore", "Echo-Finder", "Crystal-Gazer", "Dark-Delver", "Spire-Climber", "Silent-Step", "Vein-Seeker"]
    },
    "fleshwarp": {
        "prefixes": ["Mut", "Chimer", "Vex", "Aberr", "Morph", "Syth", "Kark", "Zyg", "Graft", "Splice", "Vor", "Neth"],
        "medials": ["or", "ax", "is", "ul", "en", "og"],
        "suffixes": ["is", "on", "ax", "us", "a", "oid"],
        "surnames": ["Twice-Born", "Flesh-Shaper", "Scar-Woven", "Altered-One", "Vat-Survivor", "Odd-Limb", "Many-Eyed", "Stitched-Soul"]
    },
    "draconic": {
        "prefixes": ["Drak", "Ign", "Vyrm", "Scale", "Aure", "Pyr", "Zir", "Baham", "Tiam", "Kral", "Saph", "Voryn"],
        "medials": ["or", "ax", "is", "ar", "on", "eth", "yr"],
        "suffixes": ["on", "ax", "is", "us", "ar", "ia", "os"],
        "surnames": ["Flame-Scale", "Wyrm-Blood", "Hoard-Keeper", "Sky-Roar", "Ember-Claw", "Dragon-Heart", "Scale-Bound", "Cinder-Breath", "Talon-Strike"]
    },
    "celestial": {
        "prefixes": ["Seraph", "Aure", "Sol", "Lum", "Cael", "Hal", "Astra", "Rad", "Div", "Ely", "Vesper", "Orif"],
        "medials": ["iel", "or", "an", "is", "el", "ar", "on"],
        "suffixes": ["iel", "a", "us", "on", "is", "ia", "el"],
        "surnames": ["Dawn-Bringer", "Light-Bearer", "Star-Born", "Halo-Crowned", "Sun-Sworn", "Grace-Walker", "Heaven-Sent", "Radiant-Shield", "Sky-Ward"]
    },
    "fiendish": {
        "prefixes": ["Mal", "Azaz", "Bael", "Vorg", "Infern", "Asmod", "Abad", "Zari", "Meph", "Khor", "Neth", "Dread"],
        "medials": ["or", "ath", "is", "ul", "az", "on", "ek"],
        "suffixes": ["os", "is", "ax", "us", "a", "or", "iel"],
        "surnames": ["Hell-Fire", "Ash-Sworn", "Brimstone", "Bane-Blood", "Dark-Pact", "Cinder-Horn", "Shadow-Flame", "Iron-Chain", "Sin-Eater"]
    },
    "fae": {
        "prefixes": ["Puck", "Titan", "Bramb", "Goss", "Briar", "Oakh", "Verd", "Ober", "Sylph", "Fae", "Mab", "Thist"],
        "medials": ["ael", "ith", "yn", "or", "is", "en", "ar"],
        "suffixes": ["ia", "is", "eth", "en", "a", "on", "iel"],
        "surnames": ["Glade-Walker", "Wild-Heart", "Moon-Dancer", "Twilight-Seeker", "Mist-Weaver", "Star-blossom", "Dream-Spinner", "Green-Mantle", "Fey-Touched"]
    },
    "exotic": {
        "prefixes": ["Xan", "Voh", "Kry", "Ssz", "Qor", "Zul", "Thra", "Zeph", "Aeth", "Kael", "Vael", "Orin", "Syr", "Zyr", "Quin", "Vex", "Xyl", "Kyr"],
        "medials": ["iss", "vaz", "th", "rr", "ael", "or", "yn", "os", "ir", "en"],
        "suffixes": ["us", "is", "ar", "ix", "on", "ia", "eth", "os", "an", "yl"],
        "surnames": ["Star-Touched", "Rift-Walker", "Void-Gazer", "Fate-Weaver", "Primeval-Seeker", "Aether-Born", "Planar-Drifter", "Astral-Watcher", "Time-Lost", "Mystic-Bound"]
    }
}

# Universal fallback for any custom, obscure, or homebrew ancestry name not explicitly mapped
DEFAULT_RULES = {
    "prefixes": [
        "Kor", "Vel", "Tess", "Mor", "Sael", "Vand", "Zor", "Xan",
        "Thal", "Bryn", "Kael", "Drav", "Orin", "Syl", "Cael", "Riven",
        "Torin", "Lyra", "Fen", "Mal", "Aure", "Dorian", "Sorin", "Vael"
    ],
    "medials": ["an", "or", "en", "iss", "ael", "ir", "on", "eth", "ar", "ul", "yn", "os"],
    "suffixes": ["is", "us", "ar", "ia", "on", "en", "a", "os", "eth", "el", "an", "ix"],
    "surnames": [
        "Wayfinder", "Star-Gazer", "Dawn-Bringer", "Wild-Runner", "Horizon-Seeker",
        "Storm-Watcher", "Ash-Walker", "Iron-Bound", "Mist-Strider", "Oath-Keeper",
        "Dusk-Walker", "Flame-Bearer", "Frost-Born", "Shadow-Step", "Stone-Shield",
        "Wind-Whisper", "Light-Bringer", "Void-Touched", "Sky-Weaver", "Path-Breaker"
    ]
}

_GENERATED_NAME_CACHE = set()

def generate_golarion_name(ancestry: str) -> str:
    anc_raw = (ancestry or "").lower().strip()

    # Resolve linguistic family dynamically
    family_key = DEFAULT_RULES
    for key, family in ANC_LINGUISTIC_FAMILIES.items():
        if key in anc_raw:
            family_key = LINGUISTIC_BANKS.get(family, DEFAULT_RULES)
            break

    for _ in range(100):
        pref = random.choice(family_key["prefixes"])
        med = random.choice(family_key["medials"]) if random.random() > 0.35 else ""
        suf = random.choice(family_key["suffixes"])
        surname = random.choice(family_key["surnames"]).title() if "-" not in family_key["surnames"][0] else random.choice(family_key["surnames"])

        # Normalize casing cleanly (preserve hyphenated construct tags like Aegis-01Core)
        if "-" in med:
            first_name = f"{pref}{med}{suf}"
        else:
            first_name = f"{pref}{med}{suf}".capitalize()

        full_name = f"{first_name} {surname}"

        if full_name not in _GENERATED_NAME_CACHE:
            _GENERATED_NAME_CACHE.add(full_name)
            return full_name

    # Fallback if cache saturated
    pref = random.choice(family_key["prefixes"])
    med = random.choice(family_key["medials"])
    suf = random.choice(family_key["suffixes"])
    first_name = f"{pref}{med}{suf}" if "-" in med else f"{pref}{med}{suf}".capitalize()
    return f"{first_name} {random.choice(family_key['surnames'])}"
