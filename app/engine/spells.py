import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from app.engine.models import SpellSummary, SpellcastingData, SpellSlotTracker

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"

SPELLCASTING_CLASSES = {
    "wizard": {"tradition": "Arcane", "attribute": "int"},
    "cleric": {"tradition": "Divine", "attribute": "wis"},
    "druid": {"tradition": "Primal", "attribute": "wis"},
    "bard": {"tradition": "Occult", "attribute": "cha"},
    "sorcerer": {"tradition": "Arcane", "attribute": "cha"},
    "witch": {"tradition": "Occult", "attribute": "int"},
    "oracle": {"tradition": "Divine", "attribute": "cha"},
    "psychic": {"tradition": "Occult", "attribute": "int"},
}

def load_spells() -> List[Dict[str, Any]]:
    path = DATA_DIR / "spells.json"
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def resolve_spellcasting(class_name: str, attribute_mods: Dict[str, int], level: int = 1) -> Optional[SpellcastingData]:
    cls_key = class_name.lower()
    if cls_key not in SPELLCASTING_CLASSES:
        return None

    cfg = SPELLCASTING_CLASSES[cls_key]
    key_attr = cfg["attribute"]
    attr_mod = attribute_mods.get(key_attr, 0)
    tradition = cfg["tradition"]

    prof_bonus = 2 + level  # Trained + Level
    spell_dc = 10 + prof_bonus + attr_mod
    spell_attack = prof_bonus + attr_mod

    raw_spells = load_spells()
    cantrip_list: List[SpellSummary] = []
    rank1_list: List[SpellSummary] = []

    for sp in raw_spells:
        traits = [t.title() for t in sp.get("traits", [])]
        if tradition not in traits and "Common" not in traits:
            continue
        
        entry = SpellSummary(
            name=sp["name"],
            rank=sp.get("rank", 1),
            actions=sp.get("actions", "2 actions"),
            traits=traits,
            range=sp.get("range", "30 feet"),
            targets=sp.get("targets", "1 creature"),
            defense=sp.get("defense", "None"),
            description=sp.get("summary") or sp.get("description", "")
        )

        if sp.get("rank") == 0 and len(cantrip_list) < 5:
            cantrip_list.append(entry)
        elif sp.get("rank") == 1 and len(rank1_list) < (3 if level == 2 else 2):
            rank1_list.append(entry)

    # Spell Slot Tracker: Level 1 = 2 slots, Level 2 = 3 slots
    max_rank1_slots = 3 if level >= 2 else 2
    slots = [SpellSlotTracker(rank=1, max_slots=max_rank1_slots, used_slots=0)]

    return SpellcastingData(
        tradition=tradition,
        casting_attribute=key_attr.upper(),
        spell_dc=spell_dc,
        spell_attack=spell_attack,
        cantrips=cantrip_list,
        rank_1_spells=rank1_list,
        slots=slots
    )
