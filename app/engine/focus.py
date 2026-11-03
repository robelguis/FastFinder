import random
from typing import Dict, Any, List, Optional
from app.engine.models import FocusSpellData, SpellSummary, FeatSummary

ORACLE_MYSTERY_CURSES: Dict[str, Dict[str, Any]] = {
    "cosmos": {
        "curse_name": "Curse of the Sky's Weightlessness",
        "spell": {
            "name": "Spray of Stars",
            "actions": "2 actions",
            "traits": ["Cursebound 1", "Divine", "Focus", "Light"],
            "range": "15-foot cone",
            "defense": "Basic Reflex",
            "description": "You unleash a spray of dazzling starlight dealing 1d4 fire damage per rank and dazzling targets for 1 round (blinded on critical failure)."
        },
        "effects": {
            "Cursebound 1": "Your body feels lighter than air; you take a -2 circumstance penalty to saves and DCs against Shove and Trip.",
            "Cursebound 2": "Gravity begins to slip. You become enfeebled 1.",
            "Cursebound 3": "You float inches off the ground; you become enfeebled 2 and take a -10-foot penalty to your land Speed."
        }
    },
    "flames": {
        "curse_name": "Curse of the Encroaching Cinder",
        "spell": {
            "name": "Incendiary Aura",
            "actions": "2 actions",
            "traits": ["Cursebound 1", "Divine", "Fire", "Focus"],
            "range": "10-foot emanation",
            "defense": "None",
            "description": "Flames wreath around you for 1 minute. Any creature inside the aura that takes fire damage catches fire, taking 2d4 persistent fire damage."
        },
        "effects": {
            "Cursebound 1": "Smoky heat wafts from your pores; all creatures beyond 30 feet are concealed from you.",
            "Cursebound 2": "You gain weakness to cold and water equal to your level. All creatures beyond 15 feet are concealed.",
            "Cursebound 3": "Dense smoke obscures everything; even adjacent creatures are concealed from you."
        }
    },
    "life": {
        "curse_name": "Curse of the Leaking Font",
        "spell": {
            "name": "Life Link",
            "actions": "1 action",
            "traits": ["Cursebound 1", "Divine", "Focus", "Healing"],
            "range": "30 feet",
            "defense": "None",
            "description": "You form a mystical tether to an ally. Whenever that ally takes damage, reduce it by 3 and you take 3 damage instead."
        },
        "effects": {
            "Cursebound 1": "Life energy leaks uncontrolled; your body resists outside healing. You receive only half HP from non-vitality healing.",
            "Cursebound 2": "You take a -1 status penalty to saving throws against void effects.",
            "Cursebound 3": "Your vitality body rejects exterior restoration; you cannot regain HP from any outside healing spells unless cast by yourself."
        }
    },
    "battle": {
        "curse_name": "Curse of the Battered Champion",
        "spell": {
            "name": "Call to Arms",
            "actions": "1 action",
            "traits": ["Cursebound 1", "Divine", "Emotion", "Focus", "Mental"],
            "range": "30-foot emanation",
            "defense": "None",
            "description": "You cry out a warlike rallying shout; you and all allies in the area gain a +2 status bonus to initiative rolls."
        },
        "effects": {
            "Cursebound 1": "Battle urgency demands blood. You take a -1 status penalty to AC and saving throws unless you make a Strike on your turn.",
            "Cursebound 2": "Bruises and fatigue mount; your penalty to AC and saving throws increases to -2 unless you Strike.",
            "Cursebound 3": "You become stuporously battle-weary; you become clumsy 1 and stupefied 1."
        }
    },
    "tempest": {
        "curse_name": "Curse of the Howling Gale",
        "spell": {
            "name": "Tempest Touch",
            "actions": "1 action",
            "traits": ["Cursebound 1", "Cold", "Divine", "Electricity", "Focus"],
            "range": "Touch",
            "defense": "AC",
            "description": "Electrical frost surges through your hands dealing 1d4 cold and 1d4 electricity damage, imposing clumsy 1 on a hit."
        },
        "effects": {
            "Cursebound 1": "Winds whip violently around you; you take a -2 penalty to ranged weapon attacks and Perception checks.",
            "Cursebound 2": "Rain and lightning discharge from you; electrical and water weakness equal to half level.",
            "Cursebound 3": "The squall deafens and buffets you; you become deafened and off-guard to all attacks."
        }
    },
    "lore": {
        "curse_name": "Curse of the Cramped Brain",
        "spell": {
            "name": "Brain Drain",
            "actions": "2 actions",
            "traits": ["Cursebound 1", "Curse", "Divine", "Focus", "Mental"],
            "range": "30 feet",
            "defense": "Will",
            "description": "You probe a foe's psyche dealing 2d8 mental damage and temporarily learning one piece of critical tactical knowledge."
        },
        "effects": {
            "Cursebound 1": "A flood of useless memories fills your mind; you take a -2 penalty to initiative checks.",
            "Cursebound 2": "Mental static clutters your thoughts; you become stupefied 1.",
            "Cursebound 3": "Brain strain overwhelms your sensory filter; you become stupefied 2."
        }
    }
}

CLASS_FOCUS_SPELLS: Dict[str, Dict[str, Any]] = {
    "champion": {
        "tradition": "Divine",
        "attr": "cha",
        "spells": [
            {
                "name": "Lay on Hands",
                "actions": "1 action",
                "traits": ["Divine", "Focus", "Healing", "Manipulate", "Vitality"],
                "range": "Touch",
                "defense": "None",
                "description": "Your hands glow with righteous warmth. Heals an ally for 6 HP per rank and grants a +2 status bonus to AC for 1 round, or deals 1d6 vitality damage per rank to undead (basic Fortitude save)."
            }
        ]
    },
    "monk": {
        "tradition": "Divine",
        "attr": "wis",
        "spells": [
            {
                "name": "Ki Strike",
                "actions": "1 action",
                "traits": ["Concentrate", "Divine", "Focus"],
                "range": "Self",
                "defense": "None",
                "description": "You focus your inner energy into an unarmed strike. Make an unarmed Strike with a +1 status bonus to your attack roll. The strike deals an extra 1d6 force damage per rank."
            }
        ]
    },
    "druid": {
        "tradition": "Primal",
        "attr": "wis",
        "spells": [
            {
                "name": "Heal Animal",
                "actions": "1 action",
                "traits": ["Focus", "Healing", "Manipulate", "Primal", "Vitality"],
                "range": "Touch",
                "defense": "None",
                "description": "You heal your companion animal for 1d8 HP per rank and grant them a +2 status bonus to AC for 1 round."
            }
        ]
    },
    "bard": {
        "tradition": "Occult",
        "attr": "cha",
        "spells": [
            {
                "name": "Courageous Anthem",
                "actions": "1 action",
                "traits": ["Auditory", "Cantrip", "Composition", "Emotion", "Mental", "Occult"],
                "range": "60-foot emanation",
                "defense": "None",
                "description": "Inspires your allies. You and all allies in the emanation gain a +1 status bonus to attack rolls, damage rolls, and saves against fear for 1 round."
            }
        ]
    },
    "psychic": {
        "tradition": "Occult",
        "attr": "int",
        "spells": [
            {
                "name": "Unleash Psyche",
                "actions": "Free Action",
                "traits": ["Concentrate", "Mindshift", "Occult"],
                "range": "Self",
                "defense": "None",
                "description": "You unleash your subconscious psychic potential. Your damaging spells gain a status bonus to damage equal to double the spell rank for 2 rounds."
            }
        ]
    }
}

def resolve_focus_spells(
    class_name: str,
    feats: List[FeatSummary],
    attribute_mods: Dict[str, int],
    subclass_name: Optional[str] = None,
    level: int = 1
) -> Optional[FocusSpellData]:
    cls_key = class_name.lower()

    # Special handling for Oracle Remaster
    if cls_key == "oracle":
        # Resolve Mystery
        mystery_key = "cosmos"
        sub_str = (subclass_name or "").lower()
        for k in ORACLE_MYSTERY_CURSES:
            if k in sub_str:
                mystery_key = k
                break
        else:
            # Fallback to random mystery if not parsed in subclass
            mystery_key = random.choice(list(ORACLE_MYSTERY_CURSES.keys()))

        cfg = ORACLE_MYSTERY_CURSES[mystery_key]
        attr_mod = attribute_mods.get("cha", 3)
        prof_bonus = 2 + level
        spell_dc = 10 + prof_bonus + attr_mod
        spell_attack = prof_bonus + attr_mod

        # Remaster Oracle starts with 2 Focus Points (and up to 3 at lvl 5 if taking feats)
        max_fp = 2 if level < 5 else 3
        curse_limit = max_fp

        sp = SpellSummary(rank=max(1, (level + 1) // 2), **cfg["spell"])

        return FocusSpellData(
            focus_points=max_fp,
            max_focus_points=max_fp,
            tradition="Divine",
            casting_attribute="CHA",
            spell_dc=spell_dc,
            spell_attack=spell_attack,
            spells=[sp],
            cursebound_limit=curse_limit,
            curse_mystery=f"{mystery_key.capitalize()} Mystery ({cfg['curse_name']})",
            cursebound_effects=cfg["effects"]
        )

    # Standard classes
    if cls_key not in CLASS_FOCUS_SPELLS:
        return None

    cfg = CLASS_FOCUS_SPELLS[cls_key]
    attr_key = cfg["attr"]
    attr_mod = attribute_mods.get(attr_key, 0)
    prof_bonus = 2 + level
    spell_dc = 10 + prof_bonus + attr_mod
    spell_attack = prof_bonus + attr_mod

    spells = [SpellSummary(rank=max(1, (level + 1) // 2), **s) for s in cfg["spells"]]

    return FocusSpellData(
        focus_points=1,
        max_focus_points=1,
        tradition=cfg["tradition"],
        casting_attribute=attr_key.upper(),
        spell_dc=spell_dc,
        spell_attack=spell_attack,
        spells=spells
    )
