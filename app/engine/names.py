import random
from typing import Dict, List

ANCESTRY_NAMES: Dict[str, Dict[str, List[str]]] = {
    "anadi": {
        "first": ["Aruki", "Inigo", "Kiri", "Koko", "Lalina", "Mahu", "Niye", "Ruka", "Tapi", "Wanya", "Zira", "Kipuri", "Mbari", "Rulani"],
        "last": ["Silkweaver", "Threadspinner", "Webstrider", "Loomtender", "Netbinder", "Dewspinner", "Branchwalker"]
    },
    "android": {
        "first": ["Aegis-7", "Cassiel-4", "Echo-9", "Helix-3", "Ion-12", "Koren-5", "Lynx-8", "Null-2", "Prime-6", "Rivet-11", "Talon-1", "Vector-4", "Zero-10", "Zeta-7"],
        "last": []
    },
    "athamaru": {
        "first": ["Arukar", "Benthos", "Coralis", "Drakar", "Eshkor", "Ichtor", "Kallan", "Muraen", "Pelagor", "Riptide", "Sargass", "Thalor", "Vorkas"],
        "last": ["Deepcurrent", "Tidecaller", "Reefguardian", "Abysswalker", "Kelpdiver", "Seamount", "Wavedancer"]
    },
    "automaton": {
        "first": ["Bastion", "Bulwark", "Chronos", "Colossus", "Gorgon", "Mainspring", "Monolith", "Obelisk", "Phalanx", "Runeheart", "Sentinel", "Vanguard", "Wardstone"],
        "last": []
    },
    "awakened animal": {
        "first": ["Barnaby", "Bramble", "Bruno", "Clover", "Copper", "Grizz", "Jasper", "Luna", "Otis", "Pip", "Rusty", "Scout", "Shadow", "Silas", "Titus", "Whisper"],
        "last": []
    },
    "azarketi": {
        "first": ["Alaspar", "Braxus", "Caelia", "Daryx", "Kallisto", "Morwen", "Nereus", "Pelagia", "Riptide", "Talor", "Thalassa", "Vaelos", "Zephyrus"],
        "last": ["Tidecrest", "Wavestrider", "Deepwater", "Currentrunner", "Stormfin", "Coralbloom", "Abyssbrow"]
    },
    "bugbear": {
        "first": ["Bruiser", "Claw", "Gnasher", "Gore", "Grip", "Hulk", "Krag", "Mangler", "Marrow", "Prowl", "Rend", "Scar", "Skulk", "Stalker", "Thump"],
        "last": ["Bonecrusher", "Nightstalker", "Shadowstrangler", "Fleshrender", "Bloodsnarl", "Spinebreaker", "Skullrattler"]
    },
    "catfolk": {
        "first": ["Alyara", "Caelum", "Kallik", "Malkin", "Mizra", "Nyra", "Raza", "Sikari", "Silas", "Soraya", "Tani", "Zaida", "Zephyr"],
        "last": ["Nimbleclaw", "Shadowstalker", "Silentstride", "Moonpounce", "Duskwalker", "Swiftpaw", "Graceblade", "Softstep"]
    },
    "centaur": {
        "first": ["Aethel", "Boran", "Chiron", "Drakos", "Eurytos", "Galan", "Koros", "Nessos", "Pholos", "Rhoikos", "Rorik", "Thuron", "Zephyros"],
        "last": ["Plainshoof", "Windstrider", "Stormgallop", "Swiftflank", "Ironstride", "Grassrunner", "Stagchaser"]
    },
    "conrasu": {
        "first": ["Aura-of-Dawn", "Branch-Bent-True", "Circle-Unbroken", "Core-of-Oak", "Gleam-Through-Bough", "Knot-at-Rest", "Root-Deep", "Seed-Awakened", "Splinter-Turned", "Wood-Pulsing"],
        "last": []
    },
    "dragonet": {
        "first": ["Cinder", "Ember", "Flint", "Gleam", "Glint", "Ignis", "Pyre", "Scales", "Scorch", "Sizzle", "Spark", "Talon", "Vermith"],
        "last": ["Cinderwing", "Flamebreath", "Goldhoard", "Wyrmscale", "Brightspark", "Pyreflight"]
    },
    "dwarf": {
        "first": ["Adrik", "Baern", "Bardryn", "Brokk", "Brunhilda", "Dain", "Dolgrin", "Eberk", "Eldeth", "Gunnar", "Harbek", "Helga", "Hilda", "Kathra", "Kildrak", "Morgran", "Morgrim", "Orin", "Rurik", "Sindri", "Thorin", "Torbera", "Ulfgar", "Vistra"],
        "last": ["Anvilsmith", "Battlehammer", "Boulderbrow", "Coppervein", "Deepdelver", "Fireforge", "Forgehammer", "Frostbeard", "Goldseeker", "Ironfist", "Mithralvein", "Oakenhelm", "Rockjaw", "Steelshield", "Stonebreaker"]
    },
    "elf": {
        "first": ["Aeluran", "Aerith", "Alarion", "Amalthea", "Bryn", "Caelynn", "Caladrel", "Eliandra", "Enna", "Erevan", "Faelyn", "Faeranduil", "Fhaertala", "Galanodel", "Kaelen", "Lian", "Liadon", "Meliamne", "Miriandra", "Naeris", "Sariel", "Sylas", "Thelian", "Theren", "Vaelin"],
        "last": ["Brightblade", "Dewspark", "Duskrunner", "Featherfall", "Glimmerwing", "Mistglen", "Moondancer", "Nightbreeze", "Oakshadow", "Silverbow", "Silverfrond", "Starwhisper", "Sunstrider", "Swiftwind", "Willowshade"]
    },
    "fetchling": {
        "first": ["Arach", "Caelum", "Dusk", "Erebus", "Kallista", "Lurien", "Mirage", "Nyx", "Riven", "Shade", "Umbra", "Vane", "Vesper", "Wraith"],
        "last": ["Shadowstep", "Gloomveil", "Nightweaver", "Duskshroud", "Fadeaway", "Mirrorstrider", "Dimwalker"]
    },
    "fleshwarp": {
        "first": ["Amalgam", "Blight", "Chitin", "Gristle", "Husk", "Marrow", "Muton", "Patchwork", "Quirk", "Rictus", "Sinew", "Stitch", "Surge", "Viscus"],
        "last": []
    },
    "ghoran": {
        "first": ["Amaryllis", "Briar", "Calanthe", "Dahlia", "Flora", "Hyacinth", "Lotus", "Myrtle", "Oleander", "Petal", "Saffron", "Thistle", "Verbena", "Yarrow"],
        "last": ["Bloomkeeper", "Rootbound", "Greenblossom", "Thornweaver", "Sporebearer", "Vinecaller"]
    },
    "gnome": {
        "first": ["Bimble", "Boddynock", "Breena", "Burgell", "Dimble", "Eldon", "Fizban", "Fonkin", "Gerbo", "Gimble", "Kora", "Namfoodle", "Nissa", "Nyx", "Orryn", "Pippin", "Quinn", "Seebo", "Sindri", "Spindle", "Tink", "Warryn", "Waywocket", "Wrenn", "Zanna", "Zook"],
        "last": ["Brambletoes", "Clockspinner", "Cogturner", "Copperkettle", "Fizzlebang", "Geargrinder", "Gimbalcrank", "Pocketwheel", "Quicktinker", "Sparkwhistle", "Springhopper", "Steamspark", "Turnscrew"]
    },
    "goblin": {
        "first": ["Biter", "Bogg", "Brak", "Chuffy", "Claw", "Flea", "Gnasher", "Gob", "Grik", "Grub", "Gutter", "Krik", "Maggot", "Mogmurch", "Nail", "Pinch", "Poog", "Reta", "Scrap", "Skitter", "Slark", "Snag", "Spit", "Squeal", "Stump", "Twitch", "Vrax", "Zib"],
        "last": ["Bonegnawer", "Doghater", "Earslicer", "Firetosser", "Gutterprowler", "Horsechopper", "Mudlicker", "Mudsplatter", "Pickleprowler", "Ratcatcher", "Slugchewer", "Stinkmonger", "Toenibbler"]
    },
    "goloma": {
        "first": ["Alkura", "Chitrak", "Ghazal", "Karkash", "Kurok", "Makari", "Ozul", "Pashk", "Rathik", "Sharuk", "Tarkal", "Vashk", "Zulok"],
        "last": ["Eighteyes", "Allseeing", "Feargazer", "Watchful", "Shadowvigil", "Deepwatcher"]
    },
    "halfling": {
        "first": ["Alton", "Andry", "Bree", "Callie", "Cora", "Corin", "Finnan", "Garret", "Jillian", "Kipp", "Kith", "Lavinia", "Lindal", "Lyle", "Merigold", "Merric", "Milo", "Osborn", "Perrin", "Pip", "Portia", "Rosie", "Seraph", "Tobias", "Verna", "Wellby"],
        "last": ["Amberhollow", "Appleblossom", "Brushgather", "Copperkettle", "Goodbarrel", "Greenbottle", "Highhill", "Proudfoot", "Quickstep", "Sweetwater", "Tealeaf", "Thistlebrook", "Underbough", "Warmhearth"]
    },
    "hobgoblin": {
        "first": ["Azrak", "Braggart", "Durzok", "Garl", "Hark", "Kag", "Korvash", "Malkor", "Radok", "Tark", "Ulgor", "Vang", "Varok", "Vorg", "Zark"],
        "last": ["Ironstride", "Steelbrand", "Shieldbreaker", "Warborn", "Ashcleaver", "Bloodbanner", "Dreadmarch"]
    },
    "human": {
        "first": ["Aldous", "Althea", "Bastian", "Bran", "Caelan", "Cassian", "Corin", "Danica", "Darius", "Elena", "Elowen", "Evander", "Gareth", "Isolde", "Julius", "Kallista", "Kestrel", "Lucan", "Lyra", "Marek", "Mirela", "Morrigan", "Rhiannon", "Rowan", "Sabrina", "Seraphina", "Soren", "Talia", "Theron", "Vance", "Vesper"],
        "last": ["Alderton", "Ashford", "Blackwood", "Crowley", "Dunmore", "Gryphon", "Hawthorne", "Ironwood", "Kestrel", "Oakhaven", "Rothwell", "Sterling", "Valen", "Vandermere", "Winterbourne"]
    },
    "jotunborn": {
        "first": ["Asger", "Bodil", "Dagmar", "Einar", "Frode", "Geir", "Halvar", "Ingrid", "Jorund", "Kari", "Leif", "Magnus", "Ragnvald", "Sigrid", "Torstein", "Viggo"],
        "last": ["Froststrider", "Stormcleaver", "Cragbreaker", "Thunderpeak", "Icefist", "Stonecrusher", "Highclaff"]
    },
    "kashrishi": {
        "first": ["Bhor", "Chandi", "Dharba", "Kavi", "Moksha", "Navin", "Prithvi", "Riddhi", "Soma", "Tarun", "Vayu", "Vidya"],
        "last": ["Hornbearer", "Quietgrove", "Mindgleam", "Stoutback", "Spiretender", "Ponderous"]
    },
    "kholo": {
        "first": ["Barkash", "Chitter", "Gnash", "Gore", "Hrak", "Kagur", "Marrow", "Nark", "Rend", "Rip", "Scab", "Slink", "Snarl", "Vorak"],
        "last": ["Bonechewer", "Hyenablood", "Packhowler", "Goretusk", "Cackler", "Spinebreaker"]
    },
    "kitsune": {
        "first": ["Chiyo", "Daiki", "Hana", "Hayato", "Kaito", "Kenji", "Kohaku", "Mai", "Ren", "Rin", "Sakura", "Shin", "Sora", "Yuki", "Yumi"],
        "last": ["Foxfire", "Nine-tails", "Silvermist", "Moonshade", "Autumnleaf", "Silkwhisper", "Goldenfur"]
    },
    "kobold": {
        "first": ["Dax", "Droop", "Enga", "Faz", "Gix", "Hiss", "Kael", "Kip", "Klonk", "Meepo", "Mikmek", "Nark", "Prik", "Rax", "Rik", "Sik", "Skel", "Snag", "Sniv", "Tik", "Trexx", "Varn", "Vesk", "Zik", "Zul"],
        "last": ["Cavernscout", "Dragonscale", "Eggtender", "Goldseeker", "Puffbreath", "Snakeskin", "Tailwhip", "Trapmender", "Tunnelrat", "Wyrmspeaker"]
    },
    "leshy": {
        "first": ["Acorn", "Alder", "Aspen", "Bark", "Birch", "Bramble", "Briar", "Burdock", "Clover", "Dandelion", "Fern", "Hazel", "Ivy", "Juniper", "Lichen", "Marigold", "Moss", "Nettle", "Petal", "Pinecone", "Root", "Rowan", "Sage", "Snapdragon", "Sorrel", "Sprout", "Thistle", "Thorn", "Tumbleweed", "Twig", "Willow", "Yarrow"],
        "last": []
    },
    "lizardfolk": {
        "first": ["Darask", "Gartok", "Hassk", "Isskar", "Kess", "Krogar", "Morok", "Slark", "Ssith", "Veska", "Zhar", "Zilka"],
        "last": ["Basker", "Coldscale", "Deepwalker", "Mudwalker", "Riverfang", "Sunbasker", "Swampstrider"]
    },
    "merfolk": {
        "first": ["Ariel", "Caspian", "Coralia", "Delphin", "Kallan", "Maris", "Nerida", "Oceanus", "Pelagia", "Ronan", "Sirena", "Thalassa", "Triton"],
        "last": ["Tidewhisper", "Coralcrest", "Abyssborne", "Foamstrider", "Pearlseeker", "Wavesinger"]
    },
    "minotaur": {
        "first": ["Asterion", "Baphomet", "Brakos", "Drakon", "Gore", "Kragor", "Malthus", "Rend", "Tauron", "Thokk", "Toros", "Urgok", "Valkin"],
        "last": ["Hornstrike", "Labyrinthkeeper", "Ironhoof", "Mazewalker", "Brassbrow", "Earthshaker"]
    },
    "nagaji": {
        "first": ["Ashvini", "Basuki", "Karkota", "Manasa", "Nagendra", "Padma", "Shesha", "Takshak", "Vasuki", "Vritra"],
        "last": ["Coilbound", "Venomfang", "Emeraldscale", "Serpentstride", "Slithergold", "Hoodcrest"]
    },
    "orc": {
        "first": ["Ardavan", "Brakka", "Dench", "Drog", "Feng", "Gash", "Gell", "Gorg", "Gorun", "Grom", "Henk", "Holg", "Hurok", "Imsh", "Keth", "Krag", "Krusk", "Malthor", "Mok", "Morga", "Murok", "Rakka", "Ront", "Shagrat", "Thokk", "Torok", "Urgok", "Vorg", "Zark"],
        "last": ["Ashcleaver", "Bloodfang", "Bonecrusher", "Doomhammer", "Gorehowl", "Goretusk", "Ironfang", "Ironhide", "Shieldbreaker", "Skullsplitter", "Spinebreaker", "Stormscar", "Warsnout"]
    },
    "poppet": {
        "first": ["Button", "Calico", "Felt", "Fluff", "Needle", "Patch", "Pin", "Ragdoll", "Rags", "Sackcloth", "Spool", "Stitch", "Tatter", "Thimble", "Thread", "Woolly"],
        "last": []
    },
    "ratfolk": {
        "first": ["Barnaby", "Chitter", "Gnash", "Kip", "Nib", "Patter", "Rik", "Scamp", "Snick", "Titch", "Whiskers", "Zik"],
        "last": ["Barrowsnoop", "Cheesemonger", "Packbound", "Quickwhiskers", "Shadowscamper", "Tailtwister"]
    },
    "samsaran": {
        "first": ["Amara", "Bodhi", "Chiran", "Devan", "Indra", "Kalyan", "Nirvan", "Pravin", "Rohan", "Siddh", "Veda", "Vivek"],
        "last": ["Lifeturner", "Pastwalker", "Soulweaver", "Cycleborn", "Reborn", "Memorykeeper"]
    },
    "sarangay": {
        "first": ["Bantay", "Bayani", "Datu", "Ginoo", "Kidlat", "Lakan", "Makisig", "Mayon", "Sinag", "Tala", "Tikbalang"],
        "last": ["Jewelhorn", "Stoutheart", "Gemsnout", "Ironridge", "Hornshine"]
    },
    "shisk": {
        "first": ["Barak", "Chitral", "Ghor", "Kharok", "Kurash", "Quill", "Spike", "Thorn", "Vark", "Zulash"],
        "last": ["Quillback", "Cavedelver", "Stonebristle", "Deepburrow", "Sharpcrest"]
    },
    "shoony": {
        "first": ["Barnaby", "Benton", "Biscuit", "Buster", "Clover", "Daisy", "Gordo", "Mochi", "Otis", "Penny", "Pippa", "Roscoe", "Toby", "Waffles"],
        "last": ["Barksdale", "Bristlechin", "Cozyhearth", "Puddlejumper", "Pugwash", "Shortpaw", "Snoutworthy", "Trundlefoot", "Waggles"]
    },
    "skeleton": {
        "first": ["Bones", "Calvaria", "Clack", "Femur", "Grim", "Hollow", "Marrow", "Ossis", "Rattle", "Ribs", "Scapula", "Skull", "Tibias"],
        "last": []
    },
    "sprite": {
        "first": ["Breeze", "Cinder", "Dewdrop", "Flicker", "Glimmer", "Meadow", "Petal", "Pip", "Pixie", "Puck", "Spark", "Tinker", "Twinkle", "Whisper", "Zephyr"],
        "last": ["Gleamwing", "Moonpetal", "Sunspark", "Breezeflight", "Dewhopper", "Quickflutter"]
    },
    "strix": {
        "first": ["Acro", "Corvus", "Falcon", "Kalon", "Kestrel", "Nyctos", "Orik", "Phobos", "Plume", "Raptor", "Screech", "Talon", "Varkos"],
        "last": ["Highroost", "Nightwing", "Cragfeather", "Stormtalon", "Windperch", "Darkplume"]
    },
    "surki": {
        "first": ["Chirp", "Click", "Grit", "Mandible", "Nicker", "Pincer", "Quarry", "Rumble", "Scritch", "Tunnel", "Vibration"],
        "last": []
    },
    "tanuki": {
        "first": ["Bunta", "Danzo", "Genzo", "Goro", "Hachiro", "Kintaro", "Mamoru", "Ponta", "Raikou", "Saburo", "Tetsuo"],
        "last": ["Kettlebelly", "Leafcrown", "Bellydrum", "Trickster", "Sakeflask", "Gourdhopper"]
    },
    "tengu": {
        "first": ["Beak", "Chirp", "Corvus", "Karasu", "Kite", "Koro", "Kro", "Magpie", "Plume", "Rook", "Rustle", "Scrap", "Talon", "Zhi"],
        "last": ["Crowfeather", "Swordbeak", "Glittercollector", "Windscavenger", "Blackwing", "Brighteye"]
    },
    "tripkee": {
        "first": ["Bloop", "Croak", "Gribbit", "Hops", "Kip", "Lily", "Moss", "Puddle", "Ribbit", "Slime", "Splash", "Tad", "Toad"],
        "last": ["Pondhopper", "Lilypad", "Bogstrider", "Mudleaper", "Reedsinger", "Waterstrider"]
    },
    "vanara": {
        "first": ["Bali", "Ganesh", "Hanuman", "Kapi", "Makara", "Nala", "Neel", "Rama", "Sugriva", "Tara", "Vali"],
        "last": ["Treeleaper", "Taildancer", "Canopyrunner", "Swiftbranch", "Boughbender"]
    },
    "vishkanya": {
        "first": ["Ananta", "Chandra", "Gauri", "Indira", "Kavita", "Lila", "Mohini", "Padma", "Radha", "Saras", "Usha", "Vidya"],
        "last": ["Venomveil", "Silktongue", "Poisonkiss", "Vipershadow", "Coilwhisper", "Sweetvenom"]
    },
    "wayang": {
        "first": ["Batu", "Bayu", "Dalang", "Kresna", "Lurah", "Pramana", "Rama", "Semar", "Surya", "Wahyu"],
        "last": ["Shadowplay", "Puppetmaster", "Darkwhisper", "Gloomveil", "Nightshade"]
    },
    "yaksha": {
        "first": ["Alaka", "Kubera", "Manibhadra", "Nalakuvara", "Panchika", "Purna", "Sankha", "Vaisravana"],
        "last": ["Earthguardian", "Treasurekeeper", "Rootbound", "Stoutpost", "Goldhoard"]
    },
    "yaoguai": {
        "first": ["Bai", "Hei", "Huli", "Jing", "Long", "Mao", "Mo", "Niu", "Shen", "Tian", "Wang", "Xie"],
        "last": ["Spirittransformer", "Shadowshifter", "Mistform", "Fellborn", "Phantomstride"]
    }
}

def generate_ancestry_name(ancestry: str) -> str:
    key = ancestry.lower().strip()
    table = ANCESTRY_NAMES.get(key)
    
    if not table:
        table = ANCESTRY_NAMES["human"]
        
    first = random.choice(table["first"])
    lasts = table.get("last", [])
    
    # 85% chance of surname/clan name if the ancestry customarily uses one
    if lasts and random.random() < 0.85:
        return f"{first} {random.choice(lasts)}"
    return first
