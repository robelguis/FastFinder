import json
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
PACKS_DIR = BASE_DIR / "source_data" / "packs" / "pf2e"
OUTPUT_DIR = BASE_DIR / "data"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

HTML_TAG_RE = re.compile(r"<[^>]+>")

def clean_text(text: str) -> str:
    if not text:
        return ""
    plain = HTML_TAG_RE.sub(" ", text)
    return " ".join(plain.split())

def parse_ancestries():
    path = PACKS_DIR / "ancestries"
    results = []
    if not path.exists():
        print(f"Warning: {path} not found.")
        return

    for file in path.rglob("*.json"):
        if file.name.startswith("_"):
            continue
        with open(file, "r", encoding="utf-8") as f:
            raw = json.load(f)
            if not isinstance(raw, dict) or raw.get("name") is None:
                continue
            sys = raw.get("system", {})
            if not isinstance(sys, dict):
                continue
            
            boosts = []
            for b in sys.get("boosts", {}).values() if isinstance(sys.get("boosts"), dict) else []:
                val = b.get("value", []) if isinstance(b, dict) else b
                if val:
                    boosts.append(val)
            
            flaws = []
            for fl in sys.get("flaws", {}).values() if isinstance(sys.get("flaws"), dict) else []:
                val = fl.get("value", []) if isinstance(fl, dict) else fl
                if val:
                    flaws.append(val)

            size_val = sys.get("size", "med")
            if isinstance(size_val, dict):
                size_val = size_val.get("value", "med")

            languages = sys.get("languages", {})
            if isinstance(languages, dict):
                lang_val = languages.get("value", [])
            elif isinstance(languages, list):
                lang_val = languages
            else:
                lang_val = []

            results.append({
                "id": raw.get("_id"),
                "name": raw.get("name"),
                "hp": sys.get("hp", 8),
                "speed": sys.get("speed", 25),
                "size": size_val,
                "boosts": boosts,
                "flaws": flaws,
                "languages": lang_val,
                "description": clean_text(sys.get("description", {}).get("value", "") if isinstance(sys.get("description"), dict) else "")
            })

    out_file = OUTPUT_DIR / "ancestries.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"Parsed {len(results)} ancestries -> {out_file.name}")

def parse_classes():
    path = PACKS_DIR / "classes"
    results = []
    if not path.exists():
        print(f"Warning: {path} not found.")
        return

    for file in path.rglob("*.json"):
        if file.name.startswith("_"):
            continue
        with open(file, "r", encoding="utf-8") as f:
            raw = json.load(f)
            if not isinstance(raw, dict) or raw.get("name") is None:
                continue
            sys = raw.get("system", {})
            if not isinstance(sys, dict):
                continue
            
            key_ability = sys.get("keyAbility", {})
            if isinstance(key_ability, dict):
                key_attr = key_ability.get("value", [])
            elif isinstance(key_ability, list):
                key_attr = key_ability
            else:
                key_attr = []

            results.append({
                "id": raw.get("_id"),
                "name": raw.get("name"),
                "hp_per_level": sys.get("hp", 8),
                "key_attributes": key_attr,
                "perception": sys.get("perception", 1),
                "saving_throws": sys.get("savingThrows", {}),
                "attacks": sys.get("attacks", {}),
                "defenses": sys.get("defenses", {}),
                "trained_skills_count": sys.get("trainedSkills", {}).get("additional", 2) if isinstance(sys.get("trainedSkills"), dict) else 2,
                "description": clean_text(sys.get("description", {}).get("value", "") if isinstance(sys.get("description"), dict) else "")
            })

    out_file = OUTPUT_DIR / "classes.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"Parsed {len(results)} classes -> {out_file.name}")

def parse_backgrounds():
    path = PACKS_DIR / "backgrounds"
    results = []
    if not path.exists():
        print(f"Warning: {path} not found.")
        return

    for file in path.rglob("*.json"):
        if file.name.startswith("_"):
            continue
        with open(file, "r", encoding="utf-8") as f:
            raw = json.load(f)
            if not isinstance(raw, dict) or raw.get("name") is None:
                continue
            sys = raw.get("system", {})
            if not isinstance(sys, dict):
                continue
            
            boosts = []
            for b in sys.get("boosts", {}).values() if isinstance(sys.get("boosts"), dict) else []:
                val = b.get("value", []) if isinstance(b, dict) else b
                if val:
                    boosts.append(val)

            trained_skills = sys.get("trainedSkills", {})
            skills_val = trained_skills.get("value", []) if isinstance(trained_skills, dict) else trained_skills

            results.append({
                "id": raw.get("_id"),
                "name": raw.get("name"),
                "boosts": boosts,
                "trained_skills": skills_val,
                "trained_lore": sys.get("trainedLore", ""),
                "description": clean_text(sys.get("description", {}).get("value", "") if isinstance(sys.get("description"), dict) else "")
            })

    out_file = OUTPUT_DIR / "backgrounds.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"Parsed {len(results)} backgrounds -> {out_file.name}")

def parse_feats():
    path = PACKS_DIR / "feats"
    results = []
    if not path.exists():
        print(f"Warning: {path} not found.")
        return

    for file in path.rglob("*.json"):
        if file.name.startswith("_"):
            continue
        with open(file, "r", encoding="utf-8") as f:
            raw = json.load(f)
            if not isinstance(raw, dict) or raw.get("name") is None:
                continue
            sys = raw.get("system", {})
            if not isinstance(sys, dict):
                continue
            
            traits_obj = sys.get("traits", {})
            traits = traits_obj.get("value", []) if isinstance(traits_obj, dict) else []
            rarity = traits_obj.get("rarity", "common") if isinstance(traits_obj, dict) else "common"
            
            category = sys.get("category", "")
            
            level_obj = sys.get("level", 1)
            level = level_obj.get("value", 1) if isinstance(level_obj, dict) else level_obj
            
            raw_prereqs = sys.get("prerequisites", {}).get("value", []) if isinstance(sys.get("prerequisites"), dict) else []
            prereqs = [p.get("value", "") if isinstance(p, dict) else str(p) for p in raw_prereqs]

            actions_obj = sys.get("actions", {})
            action_cost = actions_obj.get("value") if isinstance(actions_obj, dict) else None

            results.append({
                "id": raw.get("_id"),
                "name": raw.get("name"),
                "category": category,
                "level": level,
                "rarity": rarity,
                "traits": traits,
                "prerequisites": prereqs,
                "action_cost": action_cost,
                "description": clean_text(sys.get("description", {}).get("value", "") if isinstance(sys.get("description"), dict) else "")
            })

    out_file = OUTPUT_DIR / "feats.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"Parsed {len(results)} feats -> {out_file.name}")

if __name__ == "__main__":
    print("Beginning extraction from source_data/packs/pf2e...")
    parse_ancestries()
    parse_classes()
    parse_backgrounds()
    parse_feats()
    print("Extraction complete. Clean datasets are ready in data/.")
