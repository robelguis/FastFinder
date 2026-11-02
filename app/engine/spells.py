import json
import re
import random
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

def clean_pf2e_markup(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"@UUID\[[^\]]+\]\{([^}]+)\}", r"\1", text)
    text = re.sub(r"@UUID\[(?:.*?\.)?([^\]\.]+?)\]", r"\1", text)
    text = re.sub(r"@Check\[[^\]]+\]\{([^}]+)\}", r"\1", text)
    text = re.sub(r"@Check\[[^\]]*type:([a-zA-Z]+)[^\]]*\]", r"\1 check", text)
    text = re.sub(r"@Damage\[[^\]]+\]\{([^}]+)\}", r"\1", text)
    text = re.sub(r"@Damage\[([^\]]+)\]", r"\1", text)
    text = re.sub(r"@[A-Za-z]+\[[^\]]+\]\{([^}]+)\}", r"\1", text)
    text = re.sub(r"@[A-Za-z]+\[[^\]]+\]", "", text)
    text = text.replace("[[", "").replace("]]", "")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    return text.strip()

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
    tradition_lower = tradition.lower()

    prof_bonus = 2 + level  # Trained + Level
    spell_dc = 10 + prof_bonus + attr_mod
    spell_attack = prof_bonus + attr_mod

    raw_spells = load_spells()
    
    matching_cantrips: List[Dict[str, Any]] = []
    matching_rank1: List[Dict[str, Any]] = []

    for sp in raw_spells:
        # Extract traits and traditions from flat or Foundry schema
        traits_list = sp.get("traits", [])
        if isinstance(traits_list, dict):
            traits_list = traits_list.get("value", [])

        # Check traditions field (standard in Foundry PF2e system)
        traditions = sp.get("traditions", [])
        if not traditions and isinstance(sp.get("system"), dict):
            trad_data = sp["system"].get("traits", {}).get("traditions", [])
            if isinstance(trad_data, list):
                traditions = trad_data

        combined_traits_lower = [str(t).lower() for t in traits_list]
        traditions_lower = [str(t).lower() for t in traditions]

        # Match tradition if explicitly tagged or listed under traditions
        matches_tradition = (
            tradition_lower in combined_traits_lower
            or tradition_lower in traditions_lower
            or len(traditions_lower) == 0  # fallback for universal/common spells
        )

        if not matches_tradition:
            continue

        # Extract spell rank
        rank = sp.get("rank")
        if rank is None and isinstance(sp.get("system"), dict):
            rank = sp["system"].get("level", {}).get("value", 1)
        if rank is None:
            rank = sp.get("level", 1)

        try:
            rank = int(rank)
        except (ValueError, TypeError):
            rank = 1

        is_cantrip = "cantrip" in combined_traits_lower or rank == 0

        if is_cantrip:
            matching_cantrips.append(sp)
        elif rank == 1:
            matching_rank1.append(sp)

    # Shuffle for variety
    random.shuffle(matching_cantrips)
    random.shuffle(matching_rank1)

    cantrip_count = 5
    rank1_count = 3 if level >= 2 else 2

    cantrip_list: List[SpellSummary] = []
    for sp in matching_cantrips[:cantrip_count]:
        traits = [t.title() for t in sp.get("traits", []) if isinstance(t, str)]
        desc = sp.get("summary") or sp.get("description", "")
        if not desc and isinstance(sp.get("system"), dict):
            desc = sp["system"].get("description", {}).get("value", "")

        cantrip_list.append(SpellSummary(
            name=sp["name"],
            rank=0,
            actions=sp.get("actions", "2 actions"),
            traits=traits,
            range=sp.get("range", "30 feet"),
            targets=sp.get("targets", "1 creature"),
            defense=sp.get("defense", "None"),
            description=clean_pf2e_markup(desc)
        ))

    rank1_list: List[SpellSummary] = []
    for sp in matching_rank1[:rank1_count]:
        traits = [t.title() for t in sp.get("traits", []) if isinstance(t, str)]
        desc = sp.get("summary") or sp.get("description", "")
        if not desc and isinstance(sp.get("system"), dict):
            desc = sp["system"].get("description", {}).get("value", "")

        rank1_list.append(SpellSummary(
            name=sp["name"],
            rank=1,
            actions=sp.get("actions", "2 actions"),
            traits=traits,
            range=sp.get("range", "30 feet"),
            targets=sp.get("targets", "1 creature"),
            defense=sp.get("defense", "None"),
            description=clean_pf2e_markup(desc)
        ))

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
