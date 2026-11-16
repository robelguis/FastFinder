# app/engine/names.py
# Expanded Golarion-Specific Naming Tables by Ancestry and Region

import random

ANCESTRY_NAMES = {
    "surki": {
        "first": [
            "Krix", "Vexis", "Zurl", "Chitter", "Skree", "Miri", "Nesk", "Trixa", 
            "Vrak", "Ziv", "Crixus", "Vesper", "Scurry", "Nix", "Tessk", "Voss", 
            "Zarek", "Kurn", "Moxie", "Xylar", "Vrix", "Kall", "Zinn", "Tarek",
            "Pox", "Glint", "Vot", "Zix", "Krall", "Slink", "Tss", "Wrix"
        ],
        "surnames": [
            "of the Deep Tunnel", "Chitter-Clack", "Resonant", "Vibration-Seeker", 
            "Shard-Bearer", "Gleam-Finder", "Sub-Slayer", "Vault-Walker", "Echo-Listener",
            "Tunneler", "Stone-Whisperer", "Core-Scuttler", "Rumble-Guard", "Pebble-Toes"
        ]
    },
    "elf": {
        "first": [
            "Aelorin", "Caelen", "Elenia", "Faelar", "Ilivana", "Larethian", "Melian", 
            "Naerys", "Saelthorn", "Teleri", "Aerdeth", "Valanthe", "Theren", "Queth",
            "Mialee", "Galinndan", "Himo", "Sariel", "Keyleth", "Amras", "Erevan"
        ],
        "surnames": [
            "Silverfrond", "Moonwhisper", "Star-Glance", "Amastacia", "Galanodel", 
            "Holimion", "Liadon", "Meliamne", "Nailo", "Siannodel", "Xiloscient"
        ]
    },
    "dwarf": {
        "first": [
            "Dagnar", "Thorgar", "Helga", "Bragor", "Korgan", "Morgran", "Thura", 
            "Vondal", "Barendd", "Brogar", "Eberk", "Fargrim", "Harsk", "Orsik", 
            "Rangrim", "Torunn", "Kathra", "Morgryn", "Artor", "Grimnir"
        ],
        "surnames": [
            "Ironfoot", "Stonehammer", "Copper-Eye", "Anvil-Bane", "Deep-Miners",
            "Boulder-Shield", "Silverbeard", "Gold-Grip", "Battlehammer", "Lodestone"
        ]
    },
    "goblin": {
        "first": [
            "Skrap", "Zazz", "Chibs", "Grix", "Nibble", "Snag", "Trix", "Vrak", 
            "Zog", "Mug", "Grib", "Bazz", "Snik", "Pluck", "Gnash", "Wriggle",
            "Sprocket", "Fizz", "Boggle", "Krunk", "Zazzle", "Skitch"
        ],
        "surnames": [
            "Muck-Raker", "Dog-Biter", "Trash-Heap", "Fire-Maker", "Tooth-Puller",
            "Gutter-Scum", "Bone-Gnawer", "Sewer-Rat", "Gobbler", "Rust-Collector"
        ]
    },
    "gnome": {
        "first": [
            "Bimble", "Fizzle", "Glimmer", "Pip", "Quill", "Trixie", "Zazzle", 
            "Wiggle", "Pimpernel", "Zook", "Dimble", "Fibble", "Garpdbib", 
            "Namfoodle", "Roondar", "Seebo", "Sindri", "Warryn", "Bixby"
        ],
        "surnames": [
            "Tinkertop", "Nockturne", "Glimmershine", "Clock-Winder", "Spark-Spitter",
            "Color-Splash", "Bogglebell", "Whistle-Brake", "Fidget-Gear"
        ]
    },
    "orc": {
        "first": [
            "Brak", "Grush", "Kark", "Mog", "Throm", "Uruk", "Zog", "Garl", 
            "Durn", "Thraka", "Karg", "Gorm", "Vrog", "Bazrak", "Hrogath", "Morg"
        ],
        "surnames": [
            "Blood-Eye", "Skull-Splitter", "Iron-Tusk", "Bone-Crusher", "Flesh-Rend",
            "Ash-Maker", "Storm-Bringer", "Savage-Heart"
        ]
    },
    "human_taldor": {
        "first": [
            "Aurelius", "Cassian", "Drusilla", "Evander", "Flavia", "Gideon", 
            "Horatio", "Julian", "Lucian", "Maxima", "Octavia", "Valerius", 
            "Antonia", "Darius", "Livia", "Tiberius", "Vistra", "Cornelius"
        ],
        "surnames": [
            "Glorio", "Vane", "Corvosa", "Priscus", "Aquila", "Seneca", 
            "Aloro", "Balder", "D'Orlov", "Vendicci", "Marcella"
        ]
    },
    "human_varisia": {
        "first": [
            "Balthazar", "Corina", "Dmitri", "Elsa", "Garret", "Katerina", 
            "Nikolai", "Radu", "Stefan", "Vanya", "Milos", "Svetlana", 
            "Anya", "Boris", "Yuri", "Natasha", "Olgierd"
        ],
        "surnames": [
            "Vancaskerkin", "Patrus", "Sczarni", "Kadavros", "Shvetto", 
            "Glavius", "Zandro", "Orlov", "Markov", "Zelensky"
        ]
    },
    "human_mwangi": {
        "first": [
            "Ayo", "Chidi", "Efia", "Jengo", "Kofi", "Nia", "Osei", "Sefu", 
            "Zola", "Bao", "Fela", "Kwame", "Zuri", "Tariq", "Imani", "Jabari"
        ],
        "surnames": [
            "Mumin", "Zenith", "Banda", "Kinte", "Diop", "Cissoko", 
            "Okafor", "Eze", "Mensah", "Diallo"
        ]
    },
    "human_tian": {
        "first": [
            "Bayar", "Chen", "Daichi", "Fen", "Geng", "Huang", "Jian", 
            "Mei", "Ren", "Sora", "Tao", "Yin", "Bo", "Hao", "Li", "Qing"
        ],
        "surnames": [
            "Sung", "Lin", "Fang", "Shen", "Tan", "Huang", "Chou", "Liu", "Bai"
        ]
    }
}

DEFAULT_NAMES = {
    "first": [
        "Aiden", "Lyra", "Cyrus", "Thalia", "Varis", "Selene", "Orion", "Vesper",
        "Dorian", "Kaelen", "Rowan", "Tariq", "Mira", "Zane", "Sariel"
    ],
    "surnames": [
        "Brightwood", "Stormrider", "Nightshade", "Ironwood", "Sun-Seeker",
        "Wave-Crest", "Ashen-Gale", "Swift-River", "Cold-Broker"
    ]
}

def generate_golarion_name(ancestry: str = "") -> str:
    anc = (ancestry or "").lower().strip()
    pool = DEFAULT_NAMES
    
    if anc in ANCESTRY_NAMES:
        pool = ANCESTRY_NAMES[anc]
    elif "human" in anc:
        pool = random.choice([
            ANCESTRY_NAMES["human_taldor"], 
            ANCESTRY_NAMES["human_varisia"], 
            ANCESTRY_NAMES["human_mwangi"],
            ANCESTRY_NAMES["human_tian"]
        ])
        
    first = random.choice(pool["first"])
    last = random.choice(pool["surnames"])
    return f"{first} {last}"
