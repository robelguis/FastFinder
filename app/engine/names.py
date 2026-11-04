import random
from typing import Dict, List

ANCESTRY_NAMES: Dict[str, Dict[str, List[str]]] = {
    "dwarf": {
        "first": [
            "Dolgrin", "Brunhilda", "Thrum", "Kraglin", "Gunnar", "Helga",
            "Orin", "Borgan", "Marnie", "Barundar", "Dain", "Hilda", "Thorin",
            "Vondal", "Eldeth", "Bardryn", "Morgran", "Brokk", "Sindri", "Rurik",
            "Kathra", "Adrik", "Baern", "Kildrak", "Vistra", "Torbera", "Ulfgar",
            "Morgrim", "Gimrak", "Duergar", "Eberk", "Harbek", "Orik", "Thorek"
        ],
        "last": [
            "Ironfist", "Stonebreaker", "Coppervein", "Deepdelver", "Forgehammer",
            "Anvilsmith", "Goldseeker", "Rockjaw", "Fireforge", "Frostbeard",
            "Battlehammer", "Oakenhelm", "Steelshield", "Mithralvein", "Boulderbrow"
        ]
    },
    "elf": {
        "first": [
            "Caladrel", "Faeranduil", "Lian", "Sylas", "Kaelen", "Thelian",
            "Eliandra", "Vaelin", "Amalthea", "Aerith", "Erevan", "Fhaertala",
            "Ilphukiir", "Rethnor", "Theren", "Caelynn", "Sylleste", "Alluin",
            "Alarion", "Bryn", "Enna", "Galanodel", "Liadon", "Meliamne",
            "Naeris", "Sariel", "Xanaphia", "Aeluran", "Faelyn", "Miriandra"
        ],
        "last": [
            "Moondancer", "Starwhisper", "Silverfrond", "Nightbreeze", "Sunstrider",
            "Oakshadow", "Glimmerwing", "Dewspark", "Featherfall", "Willowshade",
            "Duskrunner", "Silverbow", "Mistglen", "Brightblade", "Swiftwind"
        ]
    },
    "gnome": {
        "first": [
            "Bimble", "Nissa", "Quinn", "Zook", "Breena", "Tink", "Fizban",
            "Pippin", "Kora", "Wrenn", "Dimble", "Fonkin", "Gimble", "Nyx",
            "Orryn", "Sindri", "Waywocket", "Boddynock", "Burgell", "Eldon",
            "Gerbo", "Namfoodle", "Seebo", "Warryn", "Zanna", "Spindle"
        ],
        "last": [
            "Sparkwhistle", "Geargrinder", "Fizzlebang", "Clockspinner", "Brambletoes",
            "Copperkettle", "Cogturner", "Springhopper", "Quicktinker", "Steamspark",
            "Pocketwheel", "Turnscrew", "Gimbalcrank"
        ]
    },
    "goblin": {
        "first": [
            "Chuffy", "Poog", "Reta", "Mogmurch", "Zib", "Grik", "Snag",
            "Skitter", "Krik", "Brak", "Vrax", "Biter", "Gnasher", "Squeal",
            "Scrap", "Stump", "Twitch", "Bogg", "Claw", "Flea", "Gob",
            "Grub", "Gutter", "Maggot", "Pinch", "Spit", "Slark", "Nail"
        ],
        "last": [
            "Mudlicker", "Toenibbler", "Earslicer", "Firetosser", "Stinkmonger",
            "Ratcatcher", "Gutterprowler", "Doghater", "Horsechopper",
            "Pickleprowler", "Bonegnawer", "Slugchewer", "Mudsplatter"
        ]
    },
    "halfling": {
        "first": [
            "Alton", "Cora", "Milo", "Perrin", "Rosie", "Wellby", "Kith",
            "Bree", "Corin", "Lyle", "Merric", "Andry", "Callie", "Jillian",
            "Lavinia", "Portia", "Seraph", "Osborn", "Finnan", "Garret",
            "Lindal", "Pip", "Tobias", "Verna", "Merigold", "Kipp"
        ],
        "last": [
            "Tealeaf", "Greenbottle", "Underbough", "Brushgather", "Goodbarrel",
            "Highhill", "Thistlebrook", "Proudfoot", "Warmhearth", "Sweetwater",
            "Appleblossom", "Quickstep", "Copperkettle", "Amberhollow"
        ]
    },
    "human": {
        "first": [
            "Kallista", "Darius", "Elena", "Marek", "Talia", "Cassian",
            "Vesper", "Bran", "Rhiannon", "Caelan", "Soren", "Althea",
            "Gareth", "Isolde", "Corin", "Danica", "Rowan", "Lyra", "Vance",
            "Seraphina", "Theron", "Morrigan", "Lucan", "Elowen", "Bastian",
            "Mirela", "Aldous", "Julius", "Evander", "Sabrina", "Kestrel"
        ],
        "last": [
            "Vandermere", "Ironwood", "Oakhaven", "Crowley", "Blackwood",
            "Ashford", "Dunmore", "Sterling", "Valen", "Hawthorne",
            "Kestrel", "Winterbourne", "Gryphon", "Rothwell", "Alderton"
        ]
    },
    "leshy": {
        "first": [
            "Acorn", "Bramble", "Clover", "Moss", "Sprout", "Fern", "Thorn",
            "Twig", "Bark", "Willow", "Briar", "Petal", "Snapdragon",
            "Burdock", "Thistle", "Alder", "Aspen", "Birch", "Dandelion",
            "Ivy", "Juniper", "Lichen", "Marigold", "Nettle", "Pinecone",
            "Rowan", "Sage", "Sorrel", "Tumbleweed", "Yarrow", "Hazel", "Root"
        ],
        "last": []  # Leshies carry single nature-aspect names
    },
    "orc": {
        "first": [
            "Ardavan", "Krusk", "Grom", "Thokk", "Urgok", "Shagrat", "Brakka",
            "Morga", "Drog", "Gorun", "Malthor", "Rakka", "Gorg", "Krag",
            "Murok", "Vorg", "Zark", "Dench", "Feng", "Gell", "Henk", "Holg",
            "Imsh", "Keth", "Ront", "Mok", "Hurok", "Gash", "Torok"
        ],
        "last": [
            "Skullsplitter", "Ironhide", "Bloodfang", "Goretusk", "Bonecrusher",
            "Doomhammer", "Stormscar", "Gorehowl", "Spinebreaker", "Ashcleaver",
            "Warsnout", "Ironfang", "Shieldbreaker"
        ]
    },
    
    "shoony": {
        "first": [
            "Buster", "Barnaby", "Pippa", "Roscoe", "Daisy", "Toby", "Waffles",
            "Mochi", "Otis", "Biscuit", "Clover", "Benton", "Gordo", "Penny"
        ],
        "last": [
            "Pugwash", "Snoutworthy", "Shortpaw", "Barksdale", "Puddlejumper",
            "Trundlefoot", "Waggles", "Cozyhearth", "Bristlechin"
        ]
    },
    "catfolk": {
        "first": [
            "Alyara", "Kallik", "Mizra", "Raza", "Sikari", "Tani", "Zaida",
            "Malkin", "Silas", "Caelum", "Nyra", "Soraya", "Zephyr"
        ],
        "last": [
            "Nimbleclaw", "Shadowstalker", "Silentstride", "Moonpounce",
            "Duskwalker", "Swiftpaw", "Graceblade"
        ]
    },
    "lizardfolk": {
        "first": [
            "Darask", "Kess", "Morok", "Slark", "Veska", "Zilka", "Gartok",
            "Hassk", "Isskar", "Krogar", "Ssith", "Zhar"
        ],
        "last": [
            "Basker", "Swampstrider", "Sunbasker", "Deepwalker", "Coldscale",
            "Mudwalker", "Riverfang"
        ]
    },
    "ratfolk": {
        "first": [
            "Barnaby", "Chitter", "Gnash", "Kip", "Nib", "Rik", "Snick",
            "Titch", "Whiskers", "Zik", "Scamp", "Patter"
        ],
        "last": [
            "Cheesemonger", "Quickwhiskers", "Packbound", "Tailtwister",
            "Shadowscamper", "Barrowsnoop"
        ]
    },
"kobold": {
        "first": [
            "Mikmek", "Enga", "Sniv", "Varn", "Kael", "Rax", "Zul", "Skel",
            "Tik", "Vesk", "Zik", "Kip", "Dax", "Droop", "Meepo", "Nark",
            "Sik", "Faz", "Gix", "Hiss", "Klonk", "Prik", "Rik", "Snag", "Trexx"
        ],
        "last": [
            "Dragonscale", "Trapmender", "Tunnelrat", "Cavernscout", "Tailwhip",
            "Eggtender", "Wyrmspeaker", "Snakeskin", "Goldseeker", "Puffbreath"
        ]
    }
}

def generate_ancestry_name(ancestry: str) -> str:
    key = ancestry.lower()
    table = ANCESTRY_NAMES.get(key)
    
    if not table:
        table = ANCESTRY_NAMES["human"]
        
    first = random.choice(table["first"])
    lasts = table.get("last", [])
    
    # 85% chance of clan/surname if one exists for the ancestry
    if lasts and random.random() < 0.85:
        return f"{first} {random.choice(lasts)}"
    return first
