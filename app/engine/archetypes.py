import random
from typing import Dict, Any, List, Optional

ARCHETYPES_CATALOG: Dict[str, Dict[str, Any]] = {
    "medic": {
        "name": "Medic",
        "level_2_dedication": {
            "id": "medic-dedication",
            "name": "Medic Dedication",
            "traits": ["archetype", "dedication"],
            "action_cost": None,
            "description": "You become an expert in Medicine. When you use Treat Wounds, you can increase the DC to earn higher HP restoration and reduce the cooldown."
        },
        "level_4_feats": [
            {
                "id": "doctors-visitation",
                "name": "Doctor's Visitation",
                "traits": ["archetype", "flourish"],
                "action_cost": 1,
                "description": "Stride and then use Battle Medicine or Treat Wounds on an adjacent ally."
            },
            {
                "id": "treat-condition",
                "name": "Treat Condition",
                "traits": ["archetype"],
                "action_cost": 2,
                "description": "Treat an ally's condition (clumsy, enfeebled, or sickened) to reduce its condition value by 1 on a successful Medicine check."
            }
        ]
    },
    "marshal": {
        "name": "Marshal",
        "level_2_dedication": {
            "id": "marshal-dedication",
            "name": "Marshal Dedication",
            "traits": ["archetype", "dedication"],
            "action_cost": None,
            "description": "You radiate a 10-foot marshal aura that bolsters your allies against fear and enables specialized battle stances."
        },
        "level_4_feats": [
            {
                "id": "inspiring-marshal-stance",
                "name": "Inspiring Marshal Stance",
                "traits": ["archetype", "stance"],
                "action_cost": 1,
                "description": "Enter an inspiring stance. While in the stance, allies in your aura gain a +1 status bonus to attack rolls and saves vs mental effects."
            },
            {
                "id": "dread-marshal-stance",
                "name": "Dread Marshal Stance",
                "traits": ["archetype", "stance"],
                "action_cost": 1,
                "description": "Enter a terrifying stance. While in the stance, allies in your aura deal extra damage and inflict frightened on critical hits."
            }
        ]
    },
    "beastmaster": {
        "name": "Beastmaster",
        "level_2_dedication": {
            "id": "beastmaster-dedication",
            "name": "Beastmaster Dedication",
            "traits": ["archetype", "dedication"],
            "action_cost": None,
            "description": "You gain an animal companion that fights alongside you and follows your commands in battle."
        },
        "level_4_feats": [
            {
                "id": "mature-beastmaster-companion",
                "name": "Mature Beastmaster Companion",
                "traits": ["archetype"],
                "action_cost": None,
                "description": "Your animal companion matures, increasing its size, HP, attribute modifiers, and damage."
            },
            {
                "id": "heal-animal",
                "name": "Heal Animal",
                "traits": ["archetype"],
                "action_cost": 1,
                "description": "You gain the heal animal focus spell and a focus pool of 1 Focus Point to restore your companion's HP."
            }
        ]
    },
    "scout": {
        "name": "Scout",
        "level_2_dedication": {
            "id": "scout-dedication",
            "name": "Scout Dedication",
            "traits": ["archetype", "dedication"],
            "action_cost": None,
            "description": "You become trained in Stealth. When you use the Scout exploration activity, your allies gain a +2 circumstance bonus to initiative."
        },
        "level_4_feats": [
            {
                "id": "scouts-charge",
                "name": "Scout's Charge",
                "traits": ["archetype", "flourish"],
                "action_cost": 2,
                "description": "Stride, make a Strike against an unsuspecting foe, and apply the flat-footed condition."
            },
            {
                "id": "scouts-speed",
                "name": "Scout's Speed",
                "traits": ["archetype"],
                "action_cost": None,
                "description": "Your Speed increases by 10 feet."
            }
        ]
    },
    "acrobat": {
        "name": "Acrobat",
        "level_2_dedication": {
            "id": "acrobat-dedication",
            "name": "Acrobat Dedication",
            "traits": ["archetype", "dedication"],
            "action_cost": None,
            "description": "Your Acrobatics skill automatically increases to expert, and scales to master at 7th and legendary at 15th."
        },
        "level_4_feats": [
            {
                "id": "dodge-away",
                "name": "Dodge Away",
                "traits": ["archetype"],
                "action_cost": None,
                "description": "Trigger: An attacker misses you. Reaction: Step up to 10 feet away from the attacker."
            },
            {
                "id": "contortionist",
                "name": "Contortionist",
                "traits": ["archetype"],
                "action_cost": None,
                "description": "You can Squeeze through tight areas with incredible ease and gain a bonus against Grab."
            }
        ]
    },
    "champion-multiclass": {
        "name": "Champion Multiclass",
        "level_2_dedication": {
            "id": "champion-dedication",
            "name": "Champion Dedication",
            "traits": ["archetype", "dedication", "multiclass"],
            "action_cost": None,
            "description": "You become trained in light, medium, and heavy armor, and trained in Religion. You must follow the champion's code."
        },
        "level_4_feats": [
            {
                "id": "basic-devotion",
                "name": "Basic Devotion",
                "traits": ["archetype"],
                "action_cost": None,
                "description": "You gain a 1st- or 2nd-level champion feat of your choice."
            },
            {
                "id": "healing-touch",
                "name": "Healing Touch",
                "traits": ["archetype"],
                "action_cost": None,
                "description": "You gain the lay on hands focus spell and a focus pool of 1 Focus Point."
            }
        ]
    },
    "rogue-multiclass": {
        "name": "Rogue Multiclass",
        "level_2_dedication": {
            "id": "rogue-dedication",
            "name": "Rogue Dedication",
            "traits": ["archetype", "dedication", "multiclass"],
            "action_cost": None,
            "description": "You become trained in Stealth or Thievery and gain the Surprise Attack feature."
        },
        "level_4_feats": [
            {
                "id": "sneak-attacker",
                "name": "Sneak Attacker",
                "traits": ["archetype"],
                "action_cost": None,
                "description": "You gain the Sneak Attack class feature, dealing 1d4 precision damage to flat-footed targets."
            },
            {
                "id": "basic-trickery",
                "name": "Basic Trickery",
                "traits": ["archetype"],
                "action_cost": None,
                "description": "You gain a 1st- or 2nd-level rogue feat of your choice."
            }
        ]
    }
}

def pick_archetype(excluded_class: str) -> Dict[str, Any]:
    exc = excluded_class.lower()
    valid_keys = [k for k in ARCHETYPES_CATALOG.keys() if not k.startswith(exc)]
    chosen_key = random.choice(valid_keys)
    return ARCHETYPES_CATALOG[chosen_key]
