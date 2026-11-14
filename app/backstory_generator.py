def generate_epic_backstory(self, char_data: dict) -> list:
        name = char_data.get("name") or "The Hero"
        ancestry = char_data.get("ancestry") or "Human"
        cls = char_data.get("character_class") or "Adventurer"
        lvl = int(char_data.get("level") or 1)
        bg = char_data.get("background") or "unknown origins"
        archetype = char_data.get("archetype")
        companion = char_data.get("companion")
        feats = char_data.get("feats", [])

        # Extract a couple of notable feats if available
        feat_names = []
        for f in feats:
            if isinstance(f, dict):
                f_name = f.get("name")
            else:
                f_name = getattr(f, "name", None)
            if f_name and "Dedication" not in f_name and "Weapon Specialization" not in f_name:
                feat_names.append(f_name)
        
        notable_feat = random.choice(feat_names) if feat_names else "sharp resourcefulness"

        # Chapter I: Roots & Background integration
        ch1 = (
            f"Long before {name} ever stepped onto the path of destiny, their days were defined by the grueling, "
            f"grounded realities of being a {bg}. Working through those early trials, they mastered practical skills like "
            f"their signature knack for {notable_feat}, learning early on that survival belongs to the persistent."
        )

        # Chapter II: Ancestry, Class, & Dedication integration
        arch_text = f" and later embracing the secretive teachings of the {archetype} archetype" if archetype else ""
        ch2 = (
            f"As a proud {ancestry} navigating a dangerous world, {name} found their true calling when they took up "
            f"the mantle of a {cls}{arch_text}. Every grueling test of discipline transformed raw potential into hardened, "
            f"focused expertise."
        )

        # Chapter III: Level, Scale, & Companion/Familiar integration
        companion_text = ""
        if companion and isinstance(companion, dict):
            comp_name = companion.get("name", "faithful companion")
            comp_type = companion.get("creature_type", "companion")
            companion_text = f" Side by side with their loyal {comp_type}, {comp_name},"
        elif companion:
            companion_text = f" Side by side with their trusted companion,"

        if lvl <= 2:
            ch3 = f"Now taking their first steps at Level {lvl},{companion_text} {name} stands ready to face whatever perils the frontier throws their way."
        elif lvl <= 6:
            ch3 = f"Having survived the brutal trials of the early road at Level {lvl},{companion_text} {name} has built a sharp, hard-earned reputation across the local territory."
        elif lvl <= 14:
            ch3 = f"Now a seasoned operative operating at Level {lvl},{companion_text} {name}'s exploits command genuine respect as regional powers begin to take notice."
        else:
            ch3 = f"Standing at the absolute zenith of mortal power at Level {lvl},{companion_text} {name} is a living legend whose ongoing saga echoes across empires."

        return [
            {"chapter": "Chapter I: Roots and Reality", "narrative": ch1},
            {"chapter": "Chapter II: The Turning Point", "narrative": ch2},
            {"chapter": "Chapter III: The Road Ahead", "narrative": ch3}
        ]
