# backstory_generator.py
import random

def generate_epic_backstory(char_data: dict) -> list:
    name = char_data.get("name") or "The Hero"
    ancestry = char_data.get("ancestry") or "Human"
    cls = char_data.get("character_class") or "Adventurer"
    lvl = int(char_data.get("level") or 1)
    bg = char_data.get("background") or "unknown origins"
    
    chapter_1_pool = [
        f"Long before the weight of legendary arms rested upon {name}'s shoulders, their days were defined by the meticulous routines of a {bg}. In those quiet, grueling hours, survival was a craft honed through sheer repetition rather than grand destiny.",
        f"The early years of {name}'s life were shaped entirely by the demands of being a {bg}. Far from the luxuries of court or college, they learned the harsh truths of the world through calloused hands and stubborn endurance.",
        f"Before the call to adventure took hold, {name} walked a simpler, more perilous path as a {bg}. Every challenge faced during those formative days taught them how to outlast misfortune when all other options failed."
    ]

    cls_lower = cls.lower()
    if any(c in cls_lower for c in ["cleric", "oracle", "witch", "psychic", "magus"]):
        awakening_theme = f"channeling unseen forces and wrestling with cosmic mysteries"
    elif any(c in cls_lower for c in ["fighter", "guardian", "barbarian", "champion"]):
        awakening_theme = f"withstanding brutal impacts and learning the absolute cost of failure on the front lines"
    elif any(c in cls_lower for c in ["rogue", "investigator", "swashbuckler", "ranger"]):
        awakening_theme = f"navigating the razor's edge between shadows and sudden, decisive action"
    else:
        awakening_theme = f"mastering a discipline that ordinary folk view with a mixture of awe and fear"

    chapter_2_pool = [
        f"As a {ancestry} navigating a world that rarely offered easy answers, {name}'s path fundamentally shifted when a latent calling took root. By stepping onto the path of the {cls}, they immersed themselves in {awakening_theme}, turning raw grit into specialized power.",
        f"Carrying the distinct heritage of a {ancestry}, {name} never expected the pivot that defined their life. Embracing the mantle of a {cls}, they threw themselves headlong into {awakening_theme}, forging a resolute identity from the chaos of their early trials.",
        f"The bloodline and traditions of a {ancestry} left a deep imprint on {name}, but it was the sudden awakening to the life of a {cls} that forged their true mettle, forcing them to adapt through {awakening_theme}."
    ]

    if lvl == 1:
        zenith_narrative = f"Now taking their very first steps into a much larger world as a Level {lvl} {cls}, {name} leaves the safety of their past behind, armed with little more than sharp instincts and unyielding resolve."
    elif lvl <= 5:
        zenith_narrative = f"Having survived the brutal filtration of the early road, {name} now stands as a capable Level {lvl} {cls}. Their early blunders have faded, replaced by a growing reputation that commands respect in local taverns and guild halls."
    elif lvl <= 15:
        zenith_narrative = f"As a seasoned operative and veteran at Level {lvl}, {name}'s exploits as a {cls} are spoken of with cautious reverence. Regional powers and rival factions have begun to take careful note of their rising influence."
    else:
        zenith_narrative = f"Standing at the absolute pinnacle of mortal capability as a Level {lvl} {cls}, {name} commands a legendary presence across the realm. Their ongoing saga is no longer just a personal journey, but a force that bends the history of the age."

    return [
        {"chapter": "Chapter I: Roots in the Dust", "narrative": random.choice(chapter_1_pool)},
        {"chapter": "Chapter II: The Awakening Spark", "narrative": random.choice(chapter_2_pool)},
        {"chapter": "Chapter III: The Legend Unfolds", "narrative": zenith_narrative}
    ]
