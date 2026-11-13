# backstory_generator.py
import random

def generate_epic_backstory(char_data: dict) -> list:
    name = char_data.get("name") or "The Hero"
    ancestry = char_data.get("ancestry") or "Human"
    cls = char_data.get("character_class") or "Adventurer"
    lvl = int(char_data.get("level") or 1)
    bg = char_data.get("background") or "unknown origins"
    
    # Pick a completely random structural layout style (0, 1, or 2)
    style_choice = random.randint(0, 2)
    
    if style_choice == 0:
        # Style A: The Chronicle / Legend Log format
        return [
            {
                "chapter": "I. The Formative Years",
                "narrative": f"Long before {name} ever caught the eye of fate, they were simply surviving day-to-day as a {bg}. Those early hardships forged an unyielding core long before any grand ambitions took root."
            },
            {
                "chapter": "II. The Turning Point",
                "narrative": f"A sudden shift shattered the quiet life. Drawing upon the hidden strengths of a {ancestry}, {name} stepped unhesitatingly onto the path of the {cls}, leaving their old world behind in a blaze of resolve."
            },
            {
                "chapter": "III. Current Standing",
                "narrative": f"Now operating at Level {lvl}, {name}'s presence as a {cls} commands attention across the region, turning heads and altering the balance of power wherever their travels take them."
            }
        ]
        
    elif style_choice == 1:
        # Style B: Narrative Vignette format (More atmospheric, storytelling tone)
        return [
            {
                "chapter": "The Dust of the Past",
                "narrative": f"Ask anyone from the old days about {name}, and they will tell you stories of a weary traveler shaped entirely by the grueling lifestyle of a {bg}. Every scar and calloused hand told a story of endurance."
            },
            {
                "chapter": "The Spark of Destiny",
                "narrative": f"Bloodlines run deep, and for a {ancestry}, the call of something greater is never far away. When {name} embraced the mantle of a {cls}, the transition wasn't a choice—it was an awakening."
            },
            {
                "chapter": "The Rising Tide",
                "narrative": f"At Level {lvl}, the stakes are entirely different now. No longer a novice dodging shadows, {name} walks the realm as a seasoned {cls}, carving a path that history itself is beginning to notice."
            }
        ]
        
    else:
        # Style C: Mythic/Epic Tale format (Slightly more dramatic and grand)
        return [
            {
                "chapter": "Act I: Humble Beginnings",
                "narrative": f"History rarely remembers where legends are born. For {name}, those days were spent laboring quietly as a {bg}, learning the brutal lessons of the world through patience and grit."
            },
            {
                "chapter": "Act II: The Forge of Purpose",
                "narrative": f"Destiny found {name} not in grand halls, but in the crucible of trial. Merging the ancient heritage of a {ancestry} with the lethal discipline of a {cls}, a true champion was forged."
            },
            {
                "chapter": "Act III: The Unfolding Saga",
                "narrative": f"Now standing as a formidable Level {lvl} {cls}, {name} commands a presence that echoes through taverns, camps, and royal courts alike, proving that the past is only prologue."
            }
        ]
