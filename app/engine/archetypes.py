import json
from pathlib import Path
import random
from typing import Dict, Any, List, Optional

# --- GRAFT MODIFICATIONS ---
WING_GRAFT_ITEM = {
    "name": "Wing Graft (Beast Graft)",
    "type": "equipment",
    "level": 2,
    "traits": ["Invested", "Magical", "Transmutation"],
    "price": "35 gp",
    "invested": True,
    "description": (
        "Surgically attached or magically fused beast wings grafted to your shoulders or back. "
        "Grants permanent physical wings required for the Winged Warrior dedication."
    ),
    "grants_wings": True,
}

# --- FEAT POOLS ---
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

# --- ARCHETYPES CATALOG ---
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
    "winged-warrior": {
        "name": "Winged Warrior",
        "level_2_dedication": {
            "id": "winged-warrior-dedication",
            "name": "Winged Warrior Dedication",
            "traits": ["archetype", "dedication"],
            "action_cost": None,
            "description": "You leverage permanent wings in combat. Leap distance increases by 10 feet horizontally (capped at land Speed), and any fly Speed from permanent wings increases by +5 feet."
        },
        "level_4_feats": [
            {
                "id": "wing-deflection",
                "name": "Wing Deflection",
                "traits": ["archetype", "reaction"],
                "action_cost": None,
                "description": "Trigger: An attacker hits you with a ranged physical attack. Reaction: Interpose your wings to gain a +2 circumstance bonus to AC against the triggering attack."
            },
            {
                "id": "wing-buffet",
                "name": "Wing Buffet",
                "traits": ["archetype"],
                "action_cost": 1,
                "description": "Make an agile, finesse unarmed melee Strike with your wings dealing 1d6 bludgeoning damage."
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
                "description": "You gain the Sneak Attack class feature, dealing an extra 1d6 precision damage to off-guard targets."
            }
        ]
    }
}


# Prerequisite checks and granted proficiencies for Dedications
ARCHETYPE_RULES: Dict[str, Dict[str, Any]] = {
    "acrobat": {
        "req_skills": {"Acrobatics": 2},
        "req_attrs": {},
        "grants_skill": "Acrobatics",
        "grants_rank": 4  # Auto-expert
    },
    "medic": {
        "req_skills": {"Medicine": 2},
        "req_attrs": {},
        "grants_skill": "Medicine",
        "grants_rank": 4  # Expert at 2
    },
    "wrestler": {
        "req_skills": {"Athletics": 2},
        "req_attrs": {},
        "grants_skill": "Athletics",
        "grants_rank": 4  # Expert at 2
    },
    "scout": {
        "req_skills": {},
        "req_attrs": {},
        "grants_skill": "Stealth",
        "grants_rank": 2
    },
    "marshal": {
        "req_any_skill": [{"Diplomacy": 2}, {"Intimidation": 2}],
        "req_attrs": {},
        "grants_skill": "Diplomacy",
        "grants_rank": 4
    },
    "winged-warrior": {
        "req_skills": {},
        "req_attrs": {},
        "grants_skill": "Acrobatics",
        "grants_rank": 2,
        "requires_wings": True  # Evaluated or fulfilled via Graft Investment
    },
    "champion-multiclass": {
        "req_skills": {},
        "req_attrs": {"str": 2, "cha": 2},
        "grants_skill": "Religion",
        "grants_rank": 2
    },
    "rogue-multiclass": {
        "req_skills": {},
        "req_attrs": {"dex": 2},
        "grants_skill": "Stealth",
        "grants_rank": 2
    },
    "beastmaster": {
        "req_skills": {},
        "req_attrs": {},
        "grants_skill": "Nature",
        "grants_rank": 2
    },
    "undead-master": {
        "req_skills": {},
        "req_attrs": {},
        "grants_skill": "Religion",
        "grants_rank": 2
    }
}


def is_archetype_eligible(
    arch_key: str,
    skill_ranks: Dict[str, int],
    mods: Dict[str, int],
    excluded_class: str
) -> bool:
    if arch_key.startswith(excluded_class.lower()):
        return False
    
    rule = ARCHETYPE_RULES.get(arch_key)
    if not rule:
        return True

    # 1. Attribute requirements (e.g. 14 = +2 mod)
    for attr, min_mod in rule.get("req_attrs", {}).items():
        if mods.get(attr, 0) < min_mod:
            return False

    # 2. Strict skill rank requirements
    for sk, min_rank in rule.get("req_skills", {}).items():
        if skill_ranks.get(sk, 0) < min_rank:
            return False

    # 3. Any-skill requirements (e.g. Diplomacy OR Intimidation)
    if "req_any_skill" in rule:
        satisfied = False
        for option in rule["req_any_skill"]:
            if all(skill_ranks.get(sk, 0) >= rank for sk, rank in option.items()):
                satisfied = True
                break
        if not satisfied:
            return False

    return True


def pick_archetype(
    excluded_class: str,
    skill_ranks: Dict[str, int] = None,
    mods: Dict[str, int] = None,
    all_feats: List[Dict[str, Any]] = None
) -> Dict[str, Any]:
    exc = excluded_class.lower()
    skill_ranks = skill_ranks or {}
    mods = mods or {}

    # If feats compendium is provided, sample from all valid dedications
    if all_feats:
        candidate_names = []
        for f in all_feats:
            fname = f.get("name", "")
            ftraits = [t.lower() for t in f.get("traits", [])]
            if "dedication" in fname.lower() or "dedication" in ftraits:
                arch_clean = fname.replace(" Dedication", "").strip()
                if arch_clean.lower() == exc or arch_clean.lower().startswith(exc):
                    continue
                candidate_names.append(arch_clean)

        random.shuffle(candidate_names)
        for cand in candidate_names:
            arch_obj = resolve_dynamic_archetype(cand, all_feats)
            if arch_obj:
                return arch_obj

    # Fallback to curated catalog
    eligible = [
        k for k in ARCHETYPES_CATALOG.keys()
        if is_archetype_eligible(k, skill_ranks, mods, exc)
    ]
    if not eligible:
        eligible = [k for k in ARCHETYPES_CATALOG.keys() if not k.startswith(exc)]

    chosen_key = random.choice(eligible)
    arch = dict(ARCHETYPES_CATALOG[chosen_key])
    arch["key"] = chosen_key
    if chosen_key == "champion-multiclass":
        arch["level_4_feats"] = list(CHAMPION_FEATS_POOL) + arch["level_4_feats"]
    elif chosen_key == "rogue-multiclass":
        arch["level_4_feats"] = list(ROGUE_FEATS_POOL) + arch["level_4_feats"]

    return arch


# --- DYNAMIC COMPENDIUM ARCHETYPES ---
DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"


def get_all_archetype_names() -> List[str]:
    feats_file = DATA_DIR / "feats.json"
    names = set()
    # Add hardcoded catalog names first
    for arch in ARCHETYPES_CATALOG.values():
        names.add(arch["name"])
    
    if feats_file.exists():
        with open(feats_file, "r", encoding="utf-8") as f:
            feats = json.load(f)
        for ft in feats:
            traits = [t.lower() for t in ft.get("traits", [])]
            name = ft.get("name", "")
            if "dedication" in traits or "Dedication" in name:
                clean_name = name.replace(" Dedication", "").strip()
                if clean_name:
                    names.add(clean_name)
    return sorted(list(names))


def resolve_dynamic_archetype(archetype_name: str, feats_list: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Builds an archetype definition on the fly from feats.json if not in ARCHETYPES_CATALOG.
    """
    target = archetype_name.strip().lower()
    # Check curated catalog first
    for k, v in ARCHETYPES_CATALOG.items():
        if k.lower() == target or v["name"].lower() == target:
            return v

    # Find the Dedication feat
    dedication_feat = None
    target_trait = target.replace("-", " ").replace(" multiclass", "").strip()
    for ft in feats_list:
        ft_name = ft.get("name", "")
        traits = [t.lower() for t in ft.get("traits", [])]
        if "dedication" in traits or "Dedication" in ft_name:
            clean_name = ft_name.replace(" Dedication", "").strip().lower()
            if clean_name == target or clean_name == target_trait or f"{clean_name} multiclass" == target:
                dedication_feat = ft
                break

    if not dedication_feat:
        return None

    # Find matching level 4 feats that carry the archetype trait
    lvl4_feats = []
    for ft in feats_list:
        traits = [t.lower() for t in ft.get("traits", [])]
        if target_trait in traits and ft.get("level") in (2, 4) and ft.get("id") != dedication_feat.get("id"):
            lvl4_feats.append(ft)

    if not lvl4_feats:
        # Fallback if no specific lvl4 feat trait match
        lvl4_feats = [dedication_feat]

    return {
        "id": dedication_feat["id"],
        "name": dedication_feat["name"].replace(" Dedication", "").strip(),
        "level_2_dedication": dedication_feat,
        "level_4_feats": lvl4_feats
    }
