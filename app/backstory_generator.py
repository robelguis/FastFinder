# backstory_generator.py
import random

def generate_epic_backstory(char_data: dict) -> list:
    name = char_data.get("name") or "The Hero"
    ancestry = char_data.get("ancestry") or "Human"
    cls = char_data.get("character_class") or "Adventurer"
    lvl = int(char_data.get("level") or 1)
    bg = char_data.get("background") or "unknown origins"
    
    # Force complete randomization seed uniqueness
    random.seed(f"{name}-{ancestry}-{cls}-{bg}-{lvl}")

    # --- ENTIRELY UNIQUE CHAPTER I PHRASING ---
    ch1_options = [
        f"Before {name} ever touched a blade or cast a spell, their existence was measured by the grueling demands of a {bg}. Days bled together in a haze of sweat and quiet labor, far away from the songs of glory.",
        f"Life for {name} began in the shadows of obscurity, shaped entirely by the rigorous daily grind of a {bg}. Those early years taught them how to endure hardship when comfort was nothing more than a distant dream.",
        f"Long-winded tavern tales mean nothing compared to the reality {name} faced as a {bg}. Surviving those harsh, formative days required an iron stomach and a refusal to break under pressure.",
        f"Every calloused hand and hardened glance {name} carried came from their time as a {bg}. It was an unglamorous, unforgiving beginning that quietly forged their underlying grit."
    ]

    # --- ENTIRELY UNIQUE CHAPTER II PHRASING ---
    ch2_options = [
        f"Bloodlines and destiny collided when {name}, a proud {ancestry}, felt the undeniable pull of a greater calling. Shedding their old life to walk the perilous road of the {cls}, they began mastering arts that terrify ordinary folk.",
        f"The inherent traditions of a {ancestry} run deep, but {name}'s path fractured permanently the day they embraced the mantle of a {cls}. Every grueling trial since has turned raw, unrefined potential into razor-sharp discipline.",
        f"Born into the vibrant heritage of a {ancestry}, {name} found themselves ill-fitted for a quiet existence. Stepping forward as a {cls}, they plunged headfirst into a life of calculated risks and supernatural hazards.",
        f"An unexpected catalyst upended everything {name} thought they knew. Drawing strength from their {ancestry} roots, they swore themselves to the disciplined path of the {cls}, transforming their entire identity."
    ]

    # --- ENTIRELY UNIQUE CHAPTER III PHRASING ---
    if lvl <= 2:
        ch3_options = [
            f"Now taking their very first tentative breaths as a Level {lvl} {cls}, {name} stands at the absolute beginning of a dangerous road, armed with little more than raw nerve and fierce determination.",
            f"At Level {lvl}, {name} is a newcomer to the adventuring scene. The safety of the past is gone, replaced by the unpredictable dangers of a world that respects only the strong."
        ]
    elif lvl <= 6:
        ch3_options = [
            f"Having survived the brutal filtration of the early road, {name} now commands respect as a capable Level {lvl} {cls}. Their initial blunders are gone, replaced by a growing local reputation.",
            f"Standing tall at Level {lvl}[cite: 8], {name} has proven their mettle as a {cls}. Frontier outposts and regional travelers now speak their name when discussing rising talent."
        ]
    elif lvl <= 14:
        ch3_options = [
            f"Now a hardened veteran operating at Level {lvl}, {name}'s exploits as a {cls} send ripples across provincial borders. Regional powers are finally starting to keep a close eye on their moves.",
            f"With a formidable presence at Level {lvl}, {name} moves through the world as an established {cls} whose choices actively shift the tides of local politics and danger."
        ]
    else:
        ch3_options = [
            f"Standing at the absolute zenith of mortal power at Level {lvl}, {name} has become a living legend. Their ongoing saga as a {cls} bends the history of the realm itself.",
            f"At Level {lvl}, {name} commands awe across empires. Their epic feats echo through the ages, transforming them from a mere traveler into a force of nature."
        ]

    # Clear seed so it doesn't lock global random states
    random.seed(None)

    return [
        {"chapter": "Chapter I: Roots in the Dust", "narrative": random.choice(ch1_options)},
        {"chapter": "Chapter II: The Awakening Spark", "narrative": random.choice(ch2_options)},
        {"chapter": "Chapter III: The Legend Unfolds", "narrative": random.choice(ch3_options)}
    ]
