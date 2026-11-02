from typing import Dict, Any, List
from app.engine.models import CharacterSheet

# Map core skill names to Foundry PF2e short slugs
FOUNDRY_SKILL_SLUGS: Dict[str, str] = {
    "Acrobatics": "acr",
    "Arcana": "arc",
    "Athletics": "ath",
    "Crafting": "cra",
    "Deception": "dec",
    "Diplomacy": "dip",
    "Intimidation": "itm",
    "Medicine": "med",
    "Nature": "nat",
    "Occultism": "occ",
    "Performance": "prf",
    "Religion": "rel",
    "Society": "soc",
    "Stealth": "ste",
    "Survival": "sur",
    "Thievery": "thi",
}

# Foundry PF2e ranks: 0=Untrained, 1=Trained, 2=Expert, 3=Master, 4=Legendary
RANK_LETTER_TO_NUM: Dict[str, int] = {
    "U": 0,
    "T": 1,
    "E": 2,
    "M": 3,
    "L": 4,
}

def export_to_foundry_actor(sheet: CharacterSheet) -> Dict[str, Any]:
    # 1. Attributes & Abilities
    abilities = {
        "str": {"mod": sheet.attributes.strength},
        "dex": {"mod": sheet.attributes.dexterity},
        "con": {"mod": sheet.attributes.constitution},
        "int": {"mod": sheet.attributes.intelligence},
        "wis": {"mod": sheet.attributes.wisdom},
        "cha": {"mod": sheet.attributes.charisma},
    }

    # 2. Skills
    skills_data: Dict[str, Any] = {}
    lore_items: List[Dict[str, Any]] = []

    for sk in sheet.all_skills:
        slug = FOUNDRY_SKILL_SLUGS.get(sk.name)
        rank_val = RANK_LETTER_TO_NUM.get(sk.rank_letter, 0)
        if slug:
            skills_data[slug] = {"rank": rank_val}
        elif sk.name.startswith("Lore:"):
            lore_name = sk.name.replace("Lore:", "").strip()
            lore_items.append({
                "name": f"Lore ({lore_name})",
                "type": "lore",
                "system": {
                    "proficient": {"value": rank_val},
                    "mod": {"value": sk.modifier}
                }
            })

    # 3. Saves & Perception
    saves = {
        "fortitude": {"rank": RANK_LETTER_TO_NUM.get(sheet.defenses.fortitude.rank_letter, 1)},
        "reflex": {"rank": RANK_LETTER_TO_NUM.get(sheet.defenses.reflex.rank_letter, 1)},
        "will": {"rank": RANK_LETTER_TO_NUM.get(sheet.defenses.will.rank_letter, 1)},
    }

    # 4. Embedded Items (Weapons, Armor, Feats, Spells)
    items: List[Dict[str, Any]] = list(lore_items)

    # Armor
    if sheet.equipment.armor:
        items.append({
            "name": sheet.equipment.armor.name,
            "type": "armor",
            "system": {
                "category": "armor",
                "equipped": {"value": True, "carryType": "worn"},
                "quantity": 1,
                "bulk": {"value": sheet.equipment.armor.bulk}
            }
        })

    # Shield
    if sheet.equipment.shield:
        items.append({
            "name": sheet.equipment.shield.name,
            "type": "shield",
            "system": {
                "equipped": {"value": True, "carryType": "heldInBothHands"},
                "quantity": 1,
                "bulk": {"value": sheet.equipment.shield.bulk}
            }
        })

    # Weapons / Strikes
    for w in sheet.equipment.weapons:
        traits_list = []
        matching_strike = next((s for s in sheet.equipment.strikes if s.name == w.name), None)
        if matching_strike:
            traits_list = matching_strike.traits

        items.append({
            "name": w.name,
            "type": "weapon",
            "system": {
                "category": "simple",
                "equipped": {"value": True, "carryType": "heldInOneHand"},
                "quantity": 1,
                "bulk": {"value": w.bulk},
                "traits": {"value": traits_list}
            }
        })

    # Feats
    for f in sheet.feats:
        items.append({
            "name": f.name,
            "type": "feat",
            "system": {
                "category": f.category,
                "actionType": {"value": "passive" if not f.action_cost else "action"},
                "actions": {"value": f.action_cost},
                "traits": {"value": f.traits},
                "description": {"value": f.description}
            }
        })

    # Spells (if spellcaster)
    if sheet.spellcasting:
        for sp in sheet.spellcasting.cantrips + sheet.spellcasting.rank_1_spells:
            items.append({
                "name": sp.name,
                "type": "spell",
                "system": {
                    "traits": {"value": sp.traits, "traditions": [sheet.spellcasting.tradition.lower()]},
                    "level": {"value": sp.rank},
                    "time": {"value": sp.actions},
                    "range": {"value": sp.range},
                    "target": {"value": sp.targets or ""},
                    "defense": {"save": {"statistic": sp.defense.lower() if sp.defense and sp.defense != "None" else None}},
                    "description": {"value": sp.description}
                }
            })

    # 5. Currency Items
    coins = {
        "pp": 0,
        "gp": sheet.equipment.money.gp,
        "sp": sheet.equipment.money.sp,
        "cp": sheet.equipment.money.cp
    }

    # Complete Foundry VTT PF2e Actor JSON structure
    actor_document = {
        "name": sheet.name,
        "type": "character",
        "system": {
            "details": {
                "level": {"value": sheet.level},
                "ancestry": {"name": sheet.ancestry},
                "heritage": None,
                "class": {"name": sheet.character_class},
                "background": {"name": sheet.background}
            },
            "abilities": abilities,
            "attributes": {
                "hp": {"value": sheet.defenses.hp, "max": sheet.defenses.hp},
                "speed": {"value": sheet.speed, "otherSpeeds": []},
                "perception": {"rank": RANK_LETTER_TO_NUM.get(sheet.perception.rank_letter, 1)}
            },
            "skills": skills_data,
            "saves": saves,
            "currency": coins,
            "traits": {
                "size": {"value": sheet.size},
                "traits": {"value": sheet.traits}
            }
        },
        "items": items
    }

    return actor_document
