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
            models_to_try = ['gemini-3.8-flash', 'gemini-3.5-flash-lite']
            response = None
            last_error = None

            for model_name in models_to_try:
                for attempt in range(2):
                    try:
                        response = client.models.generate_content(
                            model=model_name,
                            contents=prompt,
                            config=types.GenerateContentConfig(
                                response_mime_type="application/json",
                                temperature=0.85,
                            ),
                        )
                        if response and response.text:
                            break
                    except Exception as e:
                        last_error = e
                        import time
                        time.sleep(2 ** attempt)
                        continue
                if response and response.text:
                    break

            if not response or not response.text:
                raise Exception(f"All models busy or failed. Last error: {str(last_error)}")

            raw_text = response.text.strip()
            if raw_text.startswith("```json"):
                raw_text = raw_text[7:]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]

            return json.loads(raw_text.strip())
        except Exception as e:
            print(f"LLM Backstory Generation Error: {e}")
            # Procedural fallback so the user never hits a generation error modal
            feat_list = ", ".join(feats[:4]) if feats else "standard training"
            return [
                {
                    "chapter": f"Chapter I: The Roots of {name}",
                    "narrative": f"Long before rising to Level {lvl} as a {cls}, {name} walked the shadowed paths of Golarion as a {ancestry} with the heritage of a {heritage if 'heritage' in locals() and heritage else ancestry}. Touched by the experiences of a {bg}, their early days were defined by quiet resilience and an unyielding will to survive in a harsh world."
                },
                {
                    "chapter": f"Chapter II: Trials and Ascendancy",
                    "narrative": f"As their powers grew, {name} mastered techniques such as {feat_list}. Navigating the complex politics and dangers of the Inner Sea, they forged alliances and faced down formidable perils that tested both body and spirit."
                },
                {
                    "chapter": f"Chapter III: The Legend Unbound",
                    "narrative": f"Now standing at the pinnacle of power as a Level {lvl} {cls}, {name} looks toward the horizon. Whether bound by duty, prophecy, or personal redemption, their chronicle is far from finished, and the legends of Golarion will long remember their name."
                }
            ]
