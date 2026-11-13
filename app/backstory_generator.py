# backstory_generator.py
import random

def generate_epic_backstory(char_data: dict) -> list:
    name = char_data.get("name") or "The Hero"
    ancestry = char_data.get("ancestry") or "Human"
    cls = char_data.get("character_class") or "Adventurer"
    lvl = int(char_data.get("level") or 1)
    bg = char_data.get("background") or "unknown origins"
    
    bg_lower = bg.lower()
    cls_lower = cls.lower()

    # --- Chapter I: Completely Unique Origin Angles ---
    if "artisan" in bg_lower or "craft" in bg_lower or "engineer" in bg_lower:
        ch1 = f"{name} spent their formative years bent over smoking forges and workbench blueprints as a {bg}, believing their life's work would begin and end with mechanical perfection—until a fateful creation changed everything."
    elif "corpse" in bg_lower or "graveyard" in bg_lower or "undertaker" in bg_lower:
        ch1 = f"Working the bleak midnight shifts as a {bg}, {name} grew far too familiar with the quiet finality of death. While others fled from things that go bump in the night, {name} learned precisely how fragile mortal life truly is."
    elif "scholar" in bg_lower or "acolyte" in bg_lower or "student" in bg_lower:
        ch1 = f"Buried under ancient, crumbling tomes in dusty archives, {name} originally sought answers through scholarship as a {bg}. But history's margins held darker secrets than the library shelves ever intended to reveal."
    else:
        ch1 = f"The unforgiving terrain of the frontier shaped {name} during their days as a {bg}. Away from civilization's comforts, they mastered the art of endurance long before drawing a weapon in anger."

    # --- Chapter II: Class & Ancestry Dynamic Integration ---
    if any(c in cls_lower for c in ["cleric", "oracle", "witch"]):
        ch2 = f"When a profound, otherworldly summons pierced the veil of ordinary life, it upended everything. Embracing their heritage as a {ancestry}, {name} answered the divine call of the {cls}, binding their fate to unseen cosmic powers."
    elif any(c in cls_lower for c in ["fighter", "guardian", "barbarian", "champion"]):
        ch2 = f"Blood and iron tested {name}'s resolve when crisis struck. Drawing upon the stubborn bloodline of a {ancestry}, they stepped forward onto the brutal path of the {cls}, standing as an unyielding wall against oncoming doom."
    elif any(c in cls_lower for c in ["rogue", "investigator", "ranger", "swashbuckler"]):
        ch2 = f"Operating in the dangerous margins where law fails, {name} used their natural {ancestry} cunning to slip through the cracks. Committing entirely to the path of the {cls}, they became a phantom hunter navigating a treacherous world."
    else:
        ch2 = f"A sudden, catalytic turning point shattered {name}'s quiet routine. Harnessing the innate resilience of a {ancestry}, they embraced the rigorous discipline of the {cls}, stepping out to carve a new path through the chaos."

    # --- Chapter III: Level & Impact Scaling ---
    if lvl == 1:
        ch3 = f"Now standing at the precipice of their journey as a Level 1 {cls}, {name} leaves the shadows of their past behind, armed with nothing more than raw instinct and a fierce refusal to break."
    elif lvl <= 5:
        ch3 = f"Having survived the brutal filtration of the early road, {name} has carved out a sharp reputation as a Level {lvl} {cls}. Local guilds and frontier outposts now speak their name with newfound respect."
    elif lvl <= 15:
        ch3 = f"Now a hardened veteran at Level {lvl}, {name}'s exploits as a {cls} ripple across regional borders. Rival factions and regional powers are finally beginning to realize what happens when they cross {name}'s path."
    else:
        ch3 = f"At the absolute zenith of mortal power as a Level {lvl} {cls}, {name} is no longer just a traveler—they are a living pillar of history, whose ongoing legend echoes like a force of nature across the realm."

    return [
        {"chapter": "Chapter I: Roots in the Dust", "narrative": ch1},
        {"chapter": "Chapter II: The Awakening Spark", "narrative": ch2},
        {"chapter": "Chapter III: The Legend Unfolds", "narrative": ch3}
    ]
