import re
import uuid
from typing import Any, Dict, Union
from app.engine.models import CharacterSheet

RANK_MAP = {"U": 0, "T": 1, "E": 2, "M": 3, "L": 4}
SKILL_ABILITY_MAP = {
    "acrobatics": "dex",
    "arcana": "int",
    "athletics": "str",
    "crafting": "int",
    "deception": "cha",
    "diplomacy": "cha",
    "intimidation": "cha",
    "medicine": "wis",
    "nature": "wis",
    "occultism": "int",
    "performance": "cha",
    "religion": "wis",
    "society": "int",
    "stealth": "dex",
    "survival": "wis",
    "thievery": "dex",
}


def _parse_int_bonus(val: Any, fallback: int = 0) -> int:
    if isinstance(val, int):
        return val
    m = re.search(r"[+-]?\d+", str(val or ""))
    return int(m.group(0)) if m else fallback


def export_to_foundry_actor(sheet_or_dict: Union[CharacterSheet, Dict[str, Any]]) -> Dict[str, Any]:
    sheet = (
        sheet_or_dict
        if isinstance(sheet_or_dict, CharacterSheet)
        else CharacterSheet.model_validate(sheet_or_dict)
    )
    items = []

    # 1. Weapons and Strikes
    for strike in sheet.equipment.strikes:
        items.append({
            "_id": uuid.uuid4().hex[:16],
            "name": strike.name,
            "type": "weapon",
            "system": {
                "damage": {"die": strike.damage_dice},
                "damageType": (strike.damage_type or "bludgeoning").lower(),
                "bonus": {"value": _parse_int_bonus(strike.attack_bonus)},
                "traits": {"value": [t.lower() for t in (strike.traits or [])]},
                "equipped": {"carryType": "held", "handsHeld": 1},
            },
        })

    # 2. Armor
    if sheet.equipment.armor:
        items.append({
            "_id": uuid.uuid4().hex[:16],
            "name": sheet.equipment.armor.name,
            "type": "armor",
            "system": {
                "description": {"value": getattr(sheet.equipment.armor, "description", "") or ""},
                "equipped": {"carryType": "worn", "inSlot": True},
            },
        })

    # 3. Gear & Shields
    for gear_item in (getattr(sheet.equipment, "gear", None) or []):
        gear_name = gear_item if isinstance(gear_item, str) else getattr(gear_item, "name", str(gear_item))
        is_shield = "shield" in gear_name.lower()
        items.append({
            "_id": uuid.uuid4().hex[:16],
            "name": gear_name,
            "type": "shield" if is_shield else "equipment",
            "system": {
                "acBonus": 2 if is_shield else 0,
                "equipped": {"carryType": "held" if is_shield else "worn"},
            },
        })

    # 4. Consumables
    for con in sheet.equipment.consumables:
        items.append({
            "_id": uuid.uuid4().hex[:16],
            "name": con.name,
            "type": "consumable",
            "system": {
                "quantity": con.quantity,
                "description": {"value": getattr(con, "description", "") or ""},
            },
        })

    # 5. Feats & Special Abilities
    for feat in sheet.feats:
        items.append({
            "_id": uuid.uuid4().hex[:16],
            "name": feat.name,
            "type": "feat",
            "system": {
                "description": {"value": feat.description or ""},
                "traits": {"value": [t.lower() for t in (feat.traits or [])]},
                "actionType": {"value": "action" if feat.action_cost else "passive"},
                "actions": {"value": feat.action_cost},
            },
        })

    # 6. Spellcasting Entry + Linked Standard Spells (Foundry PF2e v6+ schema)
    if sheet.spellcasting:
        sc_entry_id = uuid.uuid4().hex[:16]
        tradition = (sheet.spellcasting.tradition or "arcane").lower()
        items.append({
            "_id": sc_entry_id,
            "name": f"{tradition.title()} Spellcasting",
            "type": "spellcastingEntry",
            "system": {
                "tradition": {"value": tradition},
                "prepared": {"value": "spontaneous" if ("spontaneous" in str(getattr(sheet.spellcasting, "casting_type", "") or "").lower() or (sheet.character_class or "").lower() in {"bard", "oracle", "psychic", "sorcerer", "summoner"}) else "prepared"},
                "spelldc": {
                    "value": sheet.spellcasting.spell_attack,
                    "dc": sheet.spellcasting.spell_dc,
                },
            },
        })

        all_spells = (
            list(sheet.spellcasting.cantrips or [])
            + list(sheet.spellcasting.rank_1_spells or [])
            + list(sheet.spellcasting.rank_2_spells or [])
            + list(sheet.spellcasting.rank_3_spells or [])
        )
        for sp in all_spells:
            items.append({
                "_id": uuid.uuid4().hex[:16],
                "name": sp.name,
                "type": "spell",
                "system": {
                    "level": {"value": sp.rank},
                    "location": {"value": sc_entry_id},
                    "traits": {"value": [t.lower() for t in (sp.traits or [])]},
                    "description": {"value": sp.description or ""},
                },
            })

    # 7. Focus Spells
    focus_pool_val = 0
    focus_pool_max = 0
    if sheet.focus_spells:
        focus_pool_val = sheet.focus_spells.focus_points
        focus_pool_max = sheet.focus_spells.max_focus_points
        for fsp in sheet.focus_spells.spells:
            items.append({
                "_id": uuid.uuid4().hex[:16],
                "name": fsp.name,
                "type": "spell",
                "system": {
                    "category": {"value": "focus"},
                    "level": {"value": fsp.rank},
                    "traits": {"value": [t.lower() for t in (fsp.traits or [])]},
                    "description": {"value": fsp.description or ""},
                },
            })

    # 8. Companion / Familiar / Eidolon Feature Item
    if sheet.companion:
        comp = sheet.companion
        comp_desc = (
            f"<p><strong>Type:</strong> {comp.creature_type} | "
            f"<strong>AC:</strong> {comp.ac} | <strong>HP:</strong> {comp.hp} | "
            f"<strong>Speed:</strong> {comp.speed} ft</p>"
            f"<p><strong>Saves:</strong> Fort +{comp.fortitude}, Ref +{comp.reflex}, Will +{comp.will}</p>"
        )
        items.append({
            "_id": uuid.uuid4().hex[:16],
            "name": f"Companion: {comp.name} ({comp.creature_type})",
            "type": "feat",
            "system": {
                "category": "classfeature",
                "description": {"value": comp_desc},
            },
        })

    # 9. Skills Mapping (PF2e v6+ system.skills)
    skills_dict: Dict[str, Any] = {}
    for sk in (sheet.all_skills or []):
        sk_key = (sk.name or "").strip().lower()
        if sk_key in SKILL_ABILITY_MAP:
            skills_dict[sk_key] = {
                "rank": RANK_MAP.get((sk.rank_letter or "U").upper(), 0),
                "mod": sk.modifier,
                "attribute": SKILL_ABILITY_MAP[sk_key],
            }

    # 10. Map Attributes & Core Stats to Foundry system schema
    attrs = sheet.attributes
    system_data = {
        "abilities": {
            "str": {"mod": attrs.strength},
            "dex": {"mod": attrs.dexterity},
            "con": {"mod": attrs.constitution},
            "int": {"mod": attrs.intelligence},
            "wis": {"mod": attrs.wisdom},
            "cha": {"mod": attrs.charisma},
        },
        "attributes": {
            "hp": {"value": sheet.defenses.hp, "max": sheet.defenses.hp},
            "ac": {"value": sheet.defenses.ac},
            "speed": {"value": sheet.speed},
            "perception": {"value": sheet.perception.modifier},
        },
        "resources": {
            "focus": {
                "value": focus_pool_val,
                "max": focus_pool_max,
            }
        },
        "saves": {
            "fortitude": {"value": sheet.defenses.fortitude.modifier},
            "reflex": {"value": sheet.defenses.reflex.modifier},
            "will": {"value": sheet.defenses.will.modifier},
        },
        "skills": skills_dict,
        "details": {
            "level": {"value": sheet.level},
            "heritage": {"value": sheet.heritage or ""},
            "ancestry": {"value": sheet.ancestry},
            "background": {"value": sheet.background},
            "class": {"value": sheet.character_class},
        },
    }

    return {
        "name": sheet.name,
        "type": "character",
        "system": system_data,
        "items": items,
    }
