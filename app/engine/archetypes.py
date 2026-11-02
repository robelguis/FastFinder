import random
from typing import Dict, Any, List

CHAMPION_FEATS_POOL = [
    {
        "id": "ranged-reprisal",
        "name": "Basic Devotion: Ranged Reprisal",
        "action_cost": None,
        "traits": ["archetype", "champion"],
        "description": "You can use your champion reaction with a ranged weapon against foes up to 15 feet away. If the foe is within weapon reach, you can make a melee Strike instead."
    },
    {
        "id": "weight-of-guilt",
        "name": "Basic Devotion: Weight of Guilt",
        "action_cost": None,
        "traits": ["archetype", "champion"],
        "description": "Guilt burdens your foe. In addition to normal reaction effects, the triggering enemy becomes stupefied 1 until the end of its turn."
    },
    {
        "id": "shining-oath",
        "name": "Basic Devotion: Shining Oath",
        "action_cost": None,
        "traits": ["archetype", "champion"],
        "description": "You have sworn to put the undead to rest. Your champion reaction adds extra vitality damage against undead, and you gain resistance against void attacks."
    },
    {
        "id": "desperate-finisher",
        "name": "Basic Devotion: Desperate Finisher",
        "action_cost": None,
        "traits": ["archetype", "champion", "reaction"],
        "description": "Trigger: You miss with a Strike on your turn and have no actions remaining. Reaction: Make a desperate follow-up Strike."
    }
]

ROGUE_FEATS_POOL = [
    {
        "id": "nimble-dodge",
        "name": "Basic Trickery: Nimble Dodge",
        "action_cost": None,
        "traits": ["archetype", "rogue", "reaction"],
        "description": "Trigger: An attacker you can see targets you with a Strike. Reaction: You gain a +2 circumstance bonus to AC against the triggering attack."
    },
    {
        "id": "mobility",
        "name": "Basic Trickery: Mobility",
        "action_cost": None,
        "traits": ["archetype", "rogue"],
        "description": "When you take a Stride action to move half your Speed or less, that movement does not trigger reactions (such as Reactive Strike)."
    },
    {
        "id": "trap-finder",
        "name": "Basic Trickery: Trap Finder",
        "action_cost": None,
        "traits": ["archetype", "rogue"],
        "description": "You gain an intuitive knack for spotting traps. You get a +1 circumstance bonus to Perception checks to notice traps and AC/saves vs traps."
    }
]

ARCHETYPES_CATALOG: Dict[str, Dict[str, Any]] = {
    "undead-master": {
        "name": "Undead Master",
        "level_2_dedication": {
            "id": "undead-master-dedication",
            "name": "Undead Master Dedication",
            "traits": ["archetype", "dedication"],
            "action_cost": None,
            "description": "You call forth an undead servant to do your bidding (Ghost, Skeleton, or Zombie) with void healing and undead immunities."
        },
        "level_4_feats": [
            {
                "id": "mature-undead-companion",
                "name": "Mature Undead Companion",
                "traits": ["archetype"],
                "action_cost": None,
                "description": "Your undead companion grows stronger, gaining +10 HP, +1 to attack rolls, +2 damage, and increased size."
            }
        ]
    },
    "medic": {
        "name": "Medic",
        "level_2_dedication": {
            "id": "medic-dedication",
            "name": "Medic Dedication",
            "traits": ["archetype", "dedication"],
            "action_cost": None,
            "description": "You become an expert in Medicine. When you use Treat Wounds, you can increase the DC to earn higher HP restoration and reduce the cooldown to 1 hour."
        },
        "level_4_feats": [
            {
                "id": "doctors-visitation",
                "name": "Doctor's Visitation",
                "traits": ["archetype", "flourish"],
                "action_cost": 1,
                "description": "Stride and then use Battle Medicine or Treat Wounds on an adjacent ally as a single action."
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
            "description": "You radiate a 10-foot marshal aura that bolsters allies against fear and grants a +1 status bonus to saves vs mental effects."
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
                "description": "Enter a terrifying stance. While in the stance, allies in your aura deal extra weapon damage and inflict frightened on critical hits."
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
            "description": "You gain an animal companion (such as a Wolf, Bear, or Raptor) that fights alongside you and follows your commands in battle."
        },
        "level_4_feats": [
            {
                "id": "mature-beastmaster-companion",
                "name": "Mature Beastmaster Companion",
                "traits": ["archetype"],
                "action_cost": None,
                "description": "Your animal companion matures, increasing in size, hit points, attribute modifiers, and damage dice."
            },
            {
                "id": "heal-animal",
                "name": "Heal Animal",
                "traits": ["archetype", "healing"],
                "action_cost": 1,
                "description": "You gain the heal animal focus spell and a focus pool of 1 Focus Point to rapidly restore your companion's HP."
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
                "description": "Stride, make a Strike against an unsuspecting foe, and apply the off-guard condition."
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
            "description": "Your Acrobatics skill automatically increases to expert, and scales automatically to master at 7th and legendary at 15th."
        },
        "level_4_feats": [
            {
                "id": "dodge-away",
                "name": "Dodge Away",
                "traits": ["archetype", "reaction"],
                "action_cost": None,
                "description": "Trigger: An attacker misses you with a melee attack. Reaction: Step up to 10 feet away from the attacker."
            },
            {
                "id": "contortionist",
                "name": "Contortionist",
                "traits": ["archetype"],
                "action_cost": None,
                "description": "You can Squeeze through tight areas at full speed and gain a +2 circumstance bonus to Escape against Grab."
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
            "description": "You gain trained proficiency in light, medium, and heavy armor, trained proficiency in Religion, and follow the champion's moral code."
        },
        "level_4_feats": [
            {
                "id": "healing-touch",
                "name": "Healing Touch (Lay on Hands)",
                "traits": ["archetype", "healing"],
                "action_cost": 1,
                "description": "You gain the lay on hands focus spell and a focus pool of 1 Focus Point to restore 6 HP per rank and grant +2 status AC."
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
            "description": "You become trained in Stealth or Thievery and gain the Surprise Attack feature to catch foes off-guard on round 1."
        },
        "level_4_feats": [
            {
                "id": "sneak-attacker",
                "name": "Sneak Attacker",
                "traits": ["archetype"],
                "action_cost": None,
                "description": "You gain the Sneak Attack class feature, dealing an extra 1d4 precision damage to off-guard targets."
            }
        ]
    }
}

def pick_archetype(excluded_class: str) -> Dict[str, Any]:
    exc = excluded_class.lower()
    valid_keys = [k for k in ARCHETYPES_CATALOG.keys() if not k.startswith(exc)]
    chosen_key = random.choice(valid_keys)
    arch = dict(ARCHETYPES_CATALOG[chosen_key])
    
    if chosen_key == "champion-multiclass":
        arch["level_4_feats"] = list(CHAMPION_FEATS_POOL) + arch["level_4_feats"]
    elif chosen_key == "rogue-multiclass":
        arch["level_4_feats"] = list(ROGUE_FEATS_POOL) + arch["level_4_feats"]

    return arch
