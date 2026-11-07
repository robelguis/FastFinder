import json
from pathlib import Path
from typing import Dict, Any, List, Optional

EQUIPMENT_DATA_PATH = Path("data/equipment.json")

# Category caches
COMPENDIUM_ARMORS: Dict[str, List[Dict[str, Any]]] = {
    "heavy": [], "medium": [], "light": [], "unarmored": []
}
COMPENDIUM_SHIELDS: List[Dict[str, Any]] = []
COMPENDIUM_MAGIC_ITEMS: Dict[int, List[Dict[str, Any]]] = {lvl: [] for lvl in range(1, 8)}

SPELLCASTING_CLASSES = {
    "bard", "cleric", "druid", "oracle", "psychic", "sorcerer", "witch", "wizard",
    "magus", "summoner", "animist", "necromancer"
}

OCCULT_TRADITION = {"bard", "psychic", "necromancer"}
DIVINE_TRADITION = {"cleric", "oracle", "champion", "animist"}
ARCANE_TRADITION = {"wizard", "magus"}
PRIMAL_TRADITION = {"druid"}

MARTIAL_CLASSES = {
    "barbarian", "champion", "fighter", "gunslinger", "monk", "ranger", "rogue",
    "swashbuckler", "inventor", "guardian", "commander", "thaumaturge", "investigator"
}

def can_equip_item(item: Dict[str, Any], cls_key: str, str_mod: int, dex_mod: int, level: int) -> bool:
    """Validate item level, magic tradition, and skill/attribute prerequisites."""
    item_lvl = item.get("level", 0)
    if item_lvl > level:
        return False

    name = item.get("name", "").lower()
    desc = item.get("description", "").lower()
    traits = [t.lower() for t in item.get("traits", [])]

    # 1. Staves, Wands, and Scrolls - strict caster lock
    is_wand_or_staff = (
        name.startswith("wand of") or 
        name.startswith("staff of") or 
        "wand" in traits or 
        "staff" in traits or
        any(t in ["wand", "scroll", "staff"] for t in traits) or
        "cast a spell" in desc or 
        "spell slot" in desc
    )
    if is_wand_or_staff and cls_key not in SPELLCASTING_CLASSES:
        return False

    # 2. Occult prerequisites
    if "occult" in traits or "occultism" in desc or "pendant of the occult" in name:
        if cls_key not in OCCULT_TRADITION and cls_key not in ["witch", "sorcerer", "summoner"]:
            return False

    # 3. Arcane prerequisites
    if "arcane" in traits or "arcana" in desc:
        if cls_key not in ARCANE_TRADITION and cls_key not in ["witch", "sorcerer", "investigator", "summoner"]:
            return False

    # 4. Divine prerequisites
    if "divine" in traits or "religion" in desc or "holy" in traits or "unholy" in traits:
        if cls_key not in DIVINE_TRADITION and cls_key not in ["witch", "sorcerer", "summoner"]:
            return False

    # 5. Primal prerequisites
    if "primal" in traits or "nature" in desc:
        if cls_key not in PRIMAL_TRADITION and cls_key not in ["ranger", "witch", "sorcerer", "summoner"]:
            return False

    # 6. Specific skill requirements
    if "crafting" in desc or "repair" in desc or "crafter" in name:
        if cls_key not in ["inventor", "alchemist"] and str_mod < 2:
            return False

    if "performance" in desc or "instrument" in desc or "persona mask" in name:
        if cls_key != "bard" and "swashbuckler" not in cls_key:
            return False

    if "thievery" in desc or "lockpick" in desc:
        if cls_key not in ["rogue", "investigator", "swashbuckler"] and dex_mod < 2:
            return False

    if "stealth" in desc or "cloak of the bat" in name:
        if cls_key not in ["rogue", "ranger", "swashbuckler", "monk"] and dex_mod < 2:
            return False

    # 7. Heavy martial athletics
    if "athletics" in desc or "shove" in desc or "trip" in desc:
        if str_mod < 2 and cls_key not in MARTIAL_CLASSES:
            return False

    return True

def load_compendium():
    """Populate category pools from data/equipment.json."""
    if not EQUIPMENT_DATA_PATH.exists():
        return

    with open(EQUIPMENT_DATA_PATH, "r", encoding="utf-8") as f:
        items = json.load(f)

    for item in items:
        itype = item.get("type")
        lvl = item.get("level", 0)
        cat = (item.get("category") or "").lower()

        if itype == "armor" and lvl == 0:
            if cat in COMPENDIUM_ARMORS:
                COMPENDIUM_ARMORS[cat].append({
                    "name": item["name"],
                    "ac_bonus": item.get("ac_bonus", 0),
                    "dex_cap": item.get("dex_cap", 0),
                    "bulk": item.get("bulk", "1"),
                    "cost_sp": int(item.get("price_gp", 0) * 10)
                })

        elif itype == "shield" and lvl <= 7:
            COMPENDIUM_SHIELDS.append({
                "name": item["name"],
                "level": lvl,
                "ac_bonus": item.get("ac_bonus", 2),
                "bulk": item.get("bulk", "1"),
                "cost_sp": int(item.get("price_gp", 0) * 10),
                "description": item.get("description", "")
            })

        elif itype == "equipment" and 1 <= lvl <= 7:
            price = item.get("price_gp", 0)
            if 10 <= price <= 500 and item.get("description"):
                COMPENDIUM_MAGIC_ITEMS[lvl].append({
                    "name": item["name"],
                    "level": lvl,
                    "cost_gp": int(price),
                    "bulk": item.get("bulk", "L"),
                    "traits": item.get("traits", []),
                    "description": item.get("description", "").strip()
                })

load_compendium()
