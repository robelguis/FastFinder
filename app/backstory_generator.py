import os
from google import genai
from google.genai import types
import json
import random

class PF2eGenerator:
    def generate_epic_backstory(self, char_data: dict) -> list:
        client = genai.Client()
        name = char_data.get("name") or "The Hero"
        ancestry = char_data.get("ancestry") or "Human"
        heritage = char_data.get("heritage", "")
        cls = char_data.get("character_class") or "Adventurer"
        lvl = int(char_data.get("level") or 1)
        bg = char_data.get("background") or "Unknown"
        archetype = char_data.get("archetype", "None")
        
        feats = [f.get("name") for f in char_data.get("feats", []) if isinstance(f, dict)]
        skills = [s.get("name") for s in char_data.get("all_skills", []) if isinstance(s, dict) and s.get("rank", 0) >= 2]
        
        equipment = char_data.get("equipment", {})
        strikes = equipment.get("strikes", []) if isinstance(equipment, dict) else []
        weapons = [w.get("name") for w in strikes if isinstance(w, dict)]
        
        companion = char_data.get("companion")
        companion_info = f"{companion.get('name')} ({companion.get('creature_type')})" if companion and isinstance(companion, dict) else "None"

        prompt = f"""
        You are a master fantasy novelist and Pathfinder 2e lore master. Write a deeply immersive, rich, 
        and evocative three-chapter backstory for the following character sheet. Avoid formulaic templates, 
        cliché boilerplate openings, or robotic summaries. Weave their mechanical traits organically into the narrative.

        CHARACTER DATA:
        - Name: {name}
        - Ancestry & Heritage: {ancestry} ({heritage})
        - Background: {bg}
        - Class & Level: Level {lvl} {cls}
        - Archetype: {archetype}
        - Key Trained Skills: {', '.join(skills) if skills else 'General frontier skills'}
        - Notable Feats & Abilities: {', '.join(feats[:5]) if feats else 'Standard training'}
        - Signature Weapons / Gear: {', '.join(weapons) if weapons else 'Standard gear'}
        - Animal Companion / Familiar / Partner: {companion_info}

        FORMAT REQUIREMENT:
        Return the response strictly as a JSON list of objects with "chapter" and "narrative" keys matching this structure:
        [
            {{"chapter": "Chapter I: [Evocative Title]", "narrative": "[Prose text...]"}},
            {{"chapter": "Chapter II: [Evocative Title]", "narrative": "[Prose text...]"}},
            {{"chapter": "Chapter III: [Evocative Title]", "narrative": "[Prose text...]"}}
        ]
        """

        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.85,
                ),
            )
            return json.loads(response.text)
        except Exception as e:
            print(f"LLM Backstory Generation Error: {e}")
            return [
                {
                    "chapter": f"The Chronicle of {name}",
                    "narrative": f"A Level {lvl} {cls} hailing from a background as a {bg}, {name} carries the unique heritage of a {ancestry} forward into a dangerous world."
                }
            ]
