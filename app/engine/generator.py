import json
import re
import random
from pathlib import Path
from typing import Dict, Any, List, Optional, Set
from app.engine.models import (
    CharacterSheet,
    AttributeModifiers,
    Defenses,
    Proficiency,
    FeatSummary,
)
from app.engine.names import generate_ancestry_name
from app.engine.equipment import resolve_equipment
from app.engine.skills import resolve_character_skills
from app.engine.spells import resolve_spellcasting

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"

ATTRIBUTES = ["str", "dex", "con", "int", "wis", "cha"]

RANK_MAP = {
    1: (2, "T"),  # Trained
    2: (4, "E"),  # Expert
    3: (6, "M"),  # Master
    4: (8, "L"),  # Legendary
}

def clean_pf2e_text(text: str) -> str:
    if not text:
        return ""
    # Strip HTML tags
    text = re.sub(r"<[^>]+>", "", text)
    # Convert @UUID[...Item.Demoralize]{Demoralize} -> Demoralize
    text = re.sub(r"@UUID\[[^\]]*\.([A-Za-z0-9_ -]+)\]\{([^}]+)\}", r"\2", text)
    # Convert @UUID[...Item.Demoralize] -> Demoralize
    text = re.sub(r"@UUID\[[^\]]*\.([A-Za-z0-9_ -]+)\]", r"\1", text)
    # Convert @Check[type:athletics|dc:...] -> Athletics check
    text = re.sub(r"@Check\[[^\]]*type:([a-z]+)[^\]]*\]", r"\1 check", text)
    # Convert @Damage[...] -> damage
    text = re.sub(r"@Damage\[[^\]]*\]", "damage", text)
    # Normalize excessive spaces/newlines
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    return text.strip()

def load_data(filename: str) -> Any:
    path = DATA_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Missing {filename}. Ensure scripts have been run.")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

class PF2eGenerator:
    def __init__(self):
        self.ancestries = {a["name"].lower(): a for a in load_data("ancestries.json")}
        self.classes = {c["name"].lower(): c for c in load_data("classes.json")}
        self.backgrounds = {b["name"].lower(): b for b in load_data("backgrounds.json")}
        self.feats = load_data("feats.json")

    def _calc_prof(self, rank_val: int, level: int, attr_mod: int) -> Proficiency:
        prof_bonus, letter = RANK_MAP.get(rank_val, (2, "T"))
        return Proficiency(rank=prof_bonus, rank_letter=letter, modifier=prof_bonus + level + attr_mod)

    def generate(
        self,
        ancestry_name: Optional[str] = None,
        class_name: Optional[str] = None,
        char_name: Optional[str] = None
    ) -> CharacterSheet:
        # 1. Select Ancestry, Class, Background
        if ancestry_name and ancestry_name.lower() in self.ancestries:
            anc = self.ancestries[ancestry_name.lower()]
        else:
            core_ancestries = ["human", "dwarf", "elf", "goblin", "halfling", "orc", "leshy", "gnome", "kobold"]
            chosen = random.choice([k for k in core_ancestries if k in self.ancestries] or list(self.ancestries.keys()))
            anc = self.ancestries[chosen]

        if class_name and class_name.lower() in self.classes:
            cls = self.classes[class_name.lower()]
        else:
            core_classes = ["fighter", "rogue", "wizard", "cleric", "barbarian", "ranger", "bard"]
            chosen = random.choice([k for k in core_classes if k in self.classes] or list(self.classes.keys()))
            cls = self.classes[chosen]

        bg = random.choice(list(self.backgrounds.values()))
        resolved_name = char_name.strip() if char_name and char_name.strip() else generate_ancestry_name(anc["name"])

        # 2. Track Attribute Boosts (Max +4 at Level 1)
        mods = {attr: 0 for attr in ATTRIBUTES}

        # Step A: Ancestry Boosts & Flaws
        applied_anc_boosts: Set[str] = set()
        for boost_option in anc.get("boosts", []):
            valid_targets = [b.lower() for b in boost_option if b.lower() in ATTRIBUTES and b.lower() not in applied_anc_boosts]
            if not valid_targets:
                valid_targets = [a for a in ATTRIBUTES if a not in applied_anc_boosts]
            chosen_target = random.choice(valid_targets)
            mods[chosen_target] += 1
            applied_anc_boosts.add(chosen_target)

        for flaw_option in anc.get("flaws", []):
            for fl in flaw_option:
                fl = fl.lower()
                if fl in mods:
                    mods[fl] -= 1

        # Step B: Background Boosts
        applied_bg_boosts: Set[str] = set()
        for boost_option in bg.get("boosts", []):
            valid_targets = [
                b.lower() for b in boost_option 
                if b.lower() in ATTRIBUTES 
                and b.lower() not in applied_bg_boosts 
                and mods[b.lower()] < 4
            ]
            if not valid_targets:
                valid_targets = [a for a in ATTRIBUTES if a not in applied_bg_boosts and mods[a] < 4]
            if valid_targets:
                chosen_target = random.choice(valid_targets)
                mods[chosen_target] += 1
                applied_bg_boosts.add(chosen_target)

        # Step C: Class Key Attribute Boost
        key_options = [k.lower() for k in cls.get("key_attributes", []) if k.lower() in ATTRIBUTES and mods[k.lower()] < 4]
        if not key_options:
            key_options = [k.lower() for k in cls.get("key_attributes", []) if k.lower() in ATTRIBUTES]
        key_attr = random.choice(key_options) if key_options else "str"
        if mods[key_attr] < 4:
            mods[key_attr] += 1

        # Step D: 4 Free Boosts
        free_boosts_applied: Set[str] = set()
        priority = [key_attr, "con", "dex", "wis", "str", "cha", "int"]
        
        for attr in priority:
            if len(free_boosts_applied) < 4:
                if attr not in free_boosts_applied and mods[attr] < 4:
                    mods[attr] += 1
                    free_boosts_applied.add(attr)

        if len(free_boosts_applied) < 4:
            for attr in ATTRIBUTES:
                if len(free_boosts_applied) < 4 and attr not in free_boosts_applied and mods[attr] < 4:
                    mods[attr] += 1
                    free_boosts_applied.add(attr)

        for attr in ATTRIBUTES:
            if mods[attr] > 4:
                mods[attr] = 4

        # 3. Defenses & Proficiencies
        level = 1
        fort_rank = cls.get("saving_throws", {}).get("fortitude", 1)
        ref_rank = cls.get("saving_throws", {}).get("reflex", 1)
        will_rank = cls.get("saving_throws", {}).get("will", 1)
        perception_rank = cls.get("perception", 1)

        fort_prof = self._calc_prof(fort_rank, level, mods["con"])
        ref_prof = self._calc_prof(ref_rank, level, mods["dex"])
        will_prof = self._calc_prof(will_rank, level, mods["wis"])
        perception_prof = self._calc_prof(perception_rank, level, mods["wis"])

        # 4. Resolve Equipment & AC (with MAP)
        equipment_loadout, calculated_ac, shield_bonus = resolve_equipment(
            cls["name"],
            str_mod=mods["str"],
            dex_mod=mods["dex"],
            level=level
        )

        total_hp = max(1, anc.get("hp", 8) + cls.get("hp_per_level", 8) + mods["con"])

        # 5. Starting Feat Selection (Cleaned rules text)
        cls_name_lower = cls["name"].lower()
        eligible_feats = [
            f for f in self.feats
            if f.get("category") == "class"
            and f.get("level") == 1
            and cls_name_lower in [t.lower() for t in f.get("traits", [])]
        ]
        
        chosen_feats = []
        if eligible_feats:
            feat_pick = random.choice(eligible_feats)
            cleaned_desc = clean_pf2e_text(feat_pick.get("description", ""))
            chosen_feats.append(FeatSummary(
                id=feat_pick["id"],
                name=feat_pick["name"],
                category="class",
                action_cost=feat_pick.get("action_cost"),
                traits=feat_pick.get("traits", []),
                description=cleaned_desc
            ))

        # 6. Full 16 Core Skills List
        all_skills = resolve_character_skills(
            class_name=cls["name"],
            background_data=bg,
            attribute_mods=mods,
            level=level
        )

        # 7. Spellcasting
        spellcasting_data = resolve_spellcasting(
            class_name=cls["name"],
            attribute_mods=mods,
            level=level
        )

        return CharacterSheet(
            name=resolved_name,
            level=level,
            ancestry=anc["name"],
            background=bg["name"],
            character_class=cls["name"],
            size=anc.get("size", "med"),
            speed=anc.get("speed", 25),
            attributes=AttributeModifiers(**mods),
            defenses=Defenses(
                ac=calculated_ac,
                shield_bonus=shield_bonus,
                hp=total_hp,
                fortitude=fort_prof,
                reflex=ref_prof,
                will=will_prof,
            ),
            perception=perception_prof,
            all_skills=all_skills,
            equipment=equipment_loadout,
            spellcasting=spellcasting_data,
            feats=chosen_feats,
            traits=[anc["name"].lower(), cls["name"].lower()],
        )
