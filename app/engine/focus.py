from typing import Dict, Any, List, Optional
from app.engine.models import FocusSpellData, SpellSummary, FeatSummary

KNOWN_FOCUS_SPELLS: Dict[str, Dict[str, Any]] = {
    "lay on hands": {
        "name": "Lay on Hands",
        "rank": 1,
        "actions": "1 action",
        "traits": ["Focus", "Healing", "Holy", "Manipulate", "Vitality"],
        "range": "Touch",
        "targets": "1 willing living creature or 1 undead creature",
        "defense": "None or basic Fortitude",
        "description": "Your hands glow with divine vitality. If the target is a willing living creature, you restore 6 Hit Points (plus 6 per heightened rank) and grant a +2 status bonus to AC for 1 round. If the target is undead, you deal 1d6 vitality damage (basic Fortitude save)."
    },
    "heal companion": {
        "name": "Heal Companion",
        "rank": 1,
        "actions": "1 action",
        "traits": ["Focus", "Healing", "Manipulate", "Primal", "Vitality"],
        "range": "Touch",
        "targets": "Your animal companion",
        "defense": "None",
        "description": "You heal your animal companion with primal energy. You restore 1d8 Hit Points to your animal companion. If you spend 2 actions, the range increases to 30 feet and you restore 1d8+8 Hit Points (heightened +1 adds 1d8+8)."
    },
    "ki strike": {
        "name": "Ki Strike",
        "rank": 1,
        "actions": "1 action",
        "traits": ["Focus", "Manipulate", "Monk"],
        "range": "Self",
        "targets": "Self",
        "defense": "None",
        "description": "Channel your ki into a physical strike. Make an unarmed Strike with a +1 status bonus to your attack roll. The strike deals an extra 1d6 damage of your choice: force, lawful, vitality, or void (heightened +2 adds +1d6)."
    },
    "counter-performance": {
        "name": "Counter-Performance",
        "rank": 1,
        "actions": "Reaction",
        "traits": ["Bard", "Composition", "Concentrate", "Focus", "Mental"],
        "range": "60 feet",
        "targets": "You and allies in area",
        "defense": "None",
        "description": "Trigger: You or an ally within 60 feet rolls a saving throw against an auditory or visual effect. Reaction: Roll a Performance check. Affected allies can use your result instead of their save."
    },
    "vessel spell": {
        "name": "Garden's Protection (Vessel Spell)",
        "rank": 1,
        "actions": "1 action",
        "traits": ["Animist", "Focus", "Manipulate", "Primal"],
        "range": "30 feet",
        "targets": "1 ally",
        "defense": "None",
        "description": "Spirits of growth encircle the ally. The target gains temporary Hit Points equal to 3 + your Wisdom modifier and ignores difficult terrain for 1 round."
    }
}

CLASS_BASE_FOCUS = {
    "champion": {
        "spell_key": "lay on hands",
        "tradition": "Divine",
        "attr": "cha"
    },
    "bard": {
        "spell_key": "counter-performance",
        "tradition": "Occult",
        "attr": "cha"
    },
    "animist": {
        "spell_key": "vessel spell",
        "tradition": "Divine",
        "attr": "wis"
    }
}

def resolve_focus_spells(
    class_name: str,
    feats: List[FeatSummary],
    attribute_mods: Dict[str, int],
    level: int = 1
) -> Optional[FocusSpellData]:
    cls_key = class_name.lower()
    spells: List[SpellSummary] = []
    points = 0
    tradition = "Divine"
    key_attr = "cha"

    # 1. Base Class Devotion Spells
    if cls_key in CLASS_BASE_FOCUS:
        cfg = CLASS_BASE_FOCUS[cls_key]
        tradition = cfg["tradition"]
        key_attr = cfg["attr"]
        sp_data = KNOWN_FOCUS_SPELLS[cfg["spell_key"]]
        spells.append(SpellSummary(**sp_data))
        points += 1

    # 2. Check Feats & Archetypes
    for f in feats:
        fname = f.name.lower()
        if "heal companion" in fname or "heal animal" in fname:
            if "heal companion" not in [s.name.lower() for s in spells]:
                spells.append(SpellSummary(**KNOWN_FOCUS_SPELLS["heal companion"]))
                points += 1
                key_attr = "wis"
                tradition = "Primal"
        elif "ki strike" in fname:
            if "ki strike" not in [s.name.lower() for s in spells]:
                spells.append(SpellSummary(**KNOWN_FOCUS_SPELLS["ki strike"]))
                points += 1
                key_attr = "wis"
                tradition = "Divine"
        elif "healing touch" in fname or "lay on hands" in fname:
            if "lay on hands" not in [s.name.lower() for s in spells]:
                spells.append(SpellSummary(**KNOWN_FOCUS_SPELLS["lay on hands"]))
                points += 1
                key_attr = "cha"
                tradition = "Divine"

    if not spells:
        return None

    max_fp = max(1, min(3, points))
    attr_mod = attribute_mods.get(key_attr, 0)
    prof = 2 + level
    dc = 10 + prof + attr_mod
    atk = prof + attr_mod

    focus_rank = max(1, (level + 1) // 2)
    for s in spells:
        s.rank = focus_rank

    return FocusSpellData(
        focus_points=max_fp,
        max_focus_points=max_fp,
        tradition=tradition,
        casting_attribute=key_attr.upper(),
        spell_dc=dc,
        spell_attack=atk,
        spells=spells
    )
