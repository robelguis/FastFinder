import json
from typing import Dict, Any
from app.engine.models import CharacterSheet

def export_to_foundry_actor(sheet: CharacterSheet) -> Dict[str, Any]:
    items = []

    # Weapons and Strikes
    for strike in sheet.equipment.strikes:
        items.append({
            "name": strike.name,
            "type": "weapon",
            "system": {
                "damage": {"die": strike.damage_dice},
                "damageType": strike.damage_type.lower(),
                "traits": {"value": [t.lower() for t in strike.traits]},
                "equipped": {"value": True}
            }
        })

    # Armor
    if sheet.equipment.armor:
        items.append({
            "name": sheet.equipment.armor.name,
            "type": "armor",
            "system": {
                "equipped": {"value": True}
            }
        })

    # Consumables
    for con in sheet.equipment.consumables:
        items.append({
            "name": con.name,
            "type": "consumable",
            "system": {
                "quantity": con.quantity,
                "description": {"value": con.description}
            }
        })

    # Feats & Special Abilities
    for feat in sheet.feats:
        items.append({
            "name": feat.name,
            "type": "feat",
            "system": {
                "description": {"value": feat.description},
                "traits": {"value": [t.lower() for t in feat.traits]},
                "actionType": {"value": "action" if feat.action_cost else "passive"},
                "actions": {"value": feat.action_cost}
            }
        })

    # Spells (Cantrips, Rank 1, Rank 2)
    if sheet.spellcasting:
        all_spells = (
            sheet.spellcasting.cantrips
            + sheet.spellcasting.rank_1_spells
            + sheet.spellcasting.rank_2_spells
        )
        for sp in all_spells:
            items.append({
                "name": sp.name,
                "type": "spell",
                "system": {
                    "level": {"value": sp.rank},
                    "traits": {"value": [t.lower() for t in sp.traits]},
                    "description": {"value": sp.description}
                }
            })

    # Map Attributes to Foundry system stats
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
            "perception": {"value": sheet.perception.modifier}
        },
        "saves": {
            "fortitude": {"value": sheet.defenses.fortitude.modifier},
            "reflex": {"value": sheet.defenses.reflex.modifier},
            "will": {"value": sheet.defenses.will.modifier}
        },
        "details": {
            "level": {"value": sheet.level},
            "heritage": {"value": sheet.heritage or ""},
            "ancestry": {"value": sheet.ancestry},
            "background": {"value": sheet.background},
            "class": {"value": sheet.character_class}
        }
    }

    actor_dict = {
        "name": sheet.name,
        "type": "character",
        "system": system_data,
        "items": items
    }

    return actor_dict
