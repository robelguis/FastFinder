import random

# Linguistic family mapping for every official Pathfinder 2e Ancestry & Versatile Heritage
ANC_LINGUISTIC_FAMILIES = {
    # Humanoid / Common
    "human": "human", "halfling": "halfling", "dwarf": "dwarf", "elf": "elf",
    # Goblins & Small Folk
    "goblin": "goblin", "gnome": "gnome", "kobold": "kobold", "shoony": "shoony", "grippli": "grippli",
    # Orcs & Brutal/Martial
    "orc": "orc", "hobgoblin": "orc", "lesh": "leshy", "leshy": "leshy",
    # Beastkin & Animal Folk
    "catfolk": "beast", "lizardfolk": "beast", "ratfolk": "beast", "tengu": "beast",
    "anadi": "beast", "kashrishi": "beast", "vanara": "beast", "centaur": "beast",
    # Aquatic
    "azarketi": "aquatic", "undine": "aquatic", "sylph": "elemental", "iftit": "elemental", "oread": "elemental",
    # Exotic / Magical / Construct
    "automaton": "construct", "conrasu": "construct", "poppet": "construct", "skeleton": "undead",
    "fleshwarp": "fleshwarp", "fetchling": "shadow", "shisk": "underground", "strix": "avian",
    "surki": "exotic", "goloma": "exotic", "vishkanya": "exotic", "nagaji": "draconic",
    "kitsune": "fae", "sprite": "fae", "nephilim": "celestial", "aasimar": "celestial", "tiefling": "fiendish"
}

LINGUISTIC_BANKS = {
    "human": {
        "prefixes": ["Kat", "Thal", "Zan", "Olg", "Cyr", "Row", "Mar", "Vand", "Dor", "Elena", "Marcus", "Valen"],
        "medials": ["er", "and", "in", "ist", "or", "ur", "al"],
        "suffixes": ["a", "en", "us", "ia", "os", "is", "an", "er"],
        "surnames": ["Vancaskerkin", "Cold-Broker", "Ashen-Gale", "Swift-River", "Ironwood", "Markov", "Brightwood"]
    },
    "dwarf": {
        "prefixes": ["Thor", "Bal", "Dorg", "Thrain", "Mor", "Dol", "Krag", "Dar", "Tor", "Gar", "Hjal", "Bryn"],
        "medials": ["grim", "gar", "mun", "dur", "fin", "kan", "dor", "bek"],
        "suffixes": ["ar", "in", "um", "ok", "ir", "ak", "gran", "heim"],
        "surnames": ["Lodestone", "Anvil-Bane", "Iron-Foot", "Copper-Beard", "Stone-Hearth", "Shield-Breaker", "Coppervein"]
    },
    "elf": {
        "prefixes": ["Ael", "Fael", "Syl", "Elar", "Tari", "Cyr", "Gal", "Val", "Naer", "Lyr", "Thia"],
        "medials": ["on", "en", "ath", "and", "or", "ist", "ael"],
        "suffixes": ["in", "a", "ion", "iss", "eth", "el", "ian", "as"],
        "surnames": ["Meliamne", "Silver-Frond", "Moon-Whisper", "Starlight", "Glow-Brook", "Wind-Runner", "Silvermist"]
    },
    "goblin": {
        "prefixes": ["Zaz", "Muck", "Snag", "Grix", "Krag", "Boil", "Rot", "Wart", "Zap", "Skum", "Snot"],
        "medials": ["ble", "gie", "ik", "og", "rat", "snit", "gut"],
        "suffixes": ["zle", "toot", "snag", "gut", "face", "tooth", "pox"],
        "surnames": ["Muck-Raker", "Trash-Finder", "Bone-Gnawer", "Swamp-Stalker", "Gutter-Snipe", "Mudlicker"]
    },
    "halfling": {
        "prefixes": ["Milo", "Finn", "Rosie", "Pippin", "Daisy", "Miri", "Corin", "Tansy", "Jasper", "Bramble"],
        "medials": ["dob", "will", "per", "cot", "lock", "tans"],
        "suffixes": ["y", "o", "a", "er", "en", "ip", "ie"],
        "surnames": ["Brightwood", "Apple-Orchard", "Hill-Topper", "Tea-Kettle", "Bramble-Foot", "Brambletoes"]
    },
    "orc": {
        "prefixes": ["Brak", "Grom", "Thar", "Urz", "Karg", "Mog", "DUR", "Zurg", "Kull", "Rath", "Thokk"],
        "medials": ["gar", "rok", "ash", "lok", "nak"],
        "suffixes": ["ok", "ash", "ar", "ul", "az", "grom"],
        "surnames": ["Blood-Eye", "Skull-Splitter", "Iron-Hide", "Tusk-Biter", "Storm-Caller", "Doomhammer"]
    },
    "gnome": {
        "prefixes": ["Wizzle", "Fiz", "Bix", "Nim", "Pimble", "Zook", "Bimble"],
        "medials": ["wig", "pop", "tick", "bam"],
        "suffixes": ["snap", "spark", "wink", "dle"],
        "surnames": ["Clock-Winder", "Glimmer-Spark", "Tumble-Down", "Pebble-Pouch"]
    },
    "kobold": {
        "prefixes": ["Zix", "Krix", "Vex", "Ska", "Miri", "Trix", "Rix", "Zor", "Vrix", "Kess"],
        "medials": ["iss", "kiz", "vaz", "rix"],
        "suffixes": ["ax", "ix", "us", "os", "rix", "en"],
        "surnames": ["Ashen-Gale", "Scale-Singer", "Dragon-Worship", "Tail-Lash", "Cave-Crawler", "Coldscale"]
    },
    "leshy": {
        "prefixes": ["Bramble", "Spore", "Moss", "Fern", "Root", "Seed", "Petal", "Bark", "Leaf", "Juniper"],
        "medials": ["heart", "weaver", "stride", "bloom", "glen"],
        "suffixes": ["ling", "ton", "ish", "keeper", "walker"],
        "surnames": ["Green-Thumb", "Sun-Seeker", "Dew-Drinker", "Canopy-Runner", "Brambleheart"]
    },
    "beast": {
        "prefixes": ["Rem", "Sula", "Tari", "Kha", "Zul", "Hiss", "Ske", "Voh", "Thok", "Nix", "Karas"],
        "medials": ["ash", "esh", "irr", "uss", "ick", "su"],
        "suffixes": ["a", "en", "us", "ar", "ok", "iss"],
        "surnames": ["Wave-Crest", "Sun-Prowler", "Shadow-Stalker", "Swamp-Stalker", "Scale-Keeper", "Feather-Step"]
    },
    "aquatic": {
        "prefixes": ["Tid", "Mar", "Cor", "Nere", "Pel", "Sal", "Ebb"],
        "medials": ["ath", "or", "un", "iss"],
        "suffixes": ["us", "a", "ia", "os"],
        "surnames": ["Deep-Watcher", "Tide-Singer", "Coral-Gazer", "Abyssal-Born", "Wave-Treader"]
    },
    "construct": {
        "prefixes": ["Aegis", "Cog", "Piston", "Brass", "Iron", "Unit", "Vessel", "Remnant"],
        "medials": ["-01", "-99", "-X", "-Beta", "-Prime"],
        "suffixes": ["Core", "Sentinel", "Guardian", "Construct"],
        "surnames": ["Clockwork Vanguard", "Gilded Sentinel", "Cogheart", "Ironclad", "Awakened Core"]
    },
    "undead": {
        "prefixes": ["Grim", "Rattle", "Sepulcher", "Dusk", "Harrow", "Marrow", "Vesper", "Crypt"],
        "medials": ["or", "ath", "ul", "un"],
        "suffixes": ["ix", "us", "is", "or"],
        "surnames": ["Bone-Collector", "Soul-Binder", "Grave-Walker", "Tomb-Guard", "Ashen-Wraith"]
    },
    "fae": {
        "prefixes": ["Puck", "Titania", "Bramble", "Gossamer", "Briar", "Oakheart", "Verdant"],
        "medials": ["ael", "ith", "yn", "or"],
        "suffixes": ["ia", "is", "eth", "en"],
        "surnames": ["Glade-Walker", "Wild-Heart", "Moon-Dancer", "Twilight-Seeker"]
    },
    "exotic": {
        "prefixes": ["Xan", "Voh", "Kry", "Ssz", "Qor", "Zul", "Thra"],
        "medials": ["iss", "vaz", "th", "rr"],
        "suffixes": ["us", "is", "ar", "ix"],
        "surnames": ["Star-Touched", "Rift-Walker", "Void-Gazer", "Fate-Weaver", "Primeval-Seeker"]
    }
}

# Universal fallback for any custom, obscure, or homebrew ancestry name not explicitly mapped
DEFAULT_RULES = {
    "prefixes": ["Kor", "Vel", "Tess", "Mor", "Sael", "Vand", "Zor", "Xan"],
    "medials": ["an", "or", "en", "iss"],
    "suffixes": ["is", "us", "ar", "ia"],
    "surnames": ["Wayfinder", "Star-Gazer", "Dawn-Bringer", "Wild-Runner", "Horizon-Seeker"]
}

_GENERATED_NAME_CACHE = set()

def generate_golarion_name(ancestry: str) -> str:
    anc_raw = ancestry.lower().strip()
    
    # Resolve linguistic family dynamically
    family_key = DEFAULT_RULES
    for key, family in ANC_LINGUISTIC_FAMILIES.items():
        if key in anc_raw:
            family_key = LINGUISTIC_BANKS.get(family, DEFAULT_RULES)
            break
            
    for _ in range(50):
        pref = random.choice(family_key["prefixes"])
        med = random.choice(family_key["medials"]) if random.random() > 0.4 else ""
        suf = random.choice(family_key["suffixes"])
        surname = random.choice(family_key["surnames"])
        
        first_name = f"{pref}{med}{suf}".capitalize()
        full_name = f"{first_name} {surname}"
        
        if full_name not in _GENERATED_NAME_CACHE:
            _GENERATED_NAME_CACHE.add(full_name)
            return full_name
            
    return f"{random.choice(family_key['prefixes'])}{random.choice(family_key['suffixes']).capitalize()} {random.choice(family_key['surnames'])}"
