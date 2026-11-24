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


FEAT_FOCUS_SPELLS = {
    # Monk Ki Spells
    "ki rush": {
        "name": "Ki Rush",
        "actions": "1 action",
        "traits": ["Concentrate", "Divine", "Focus"],
        "range": "Self",
        "defense": "None",
        "description": "Accelerate your body. Stride, Step, or Leap twice. During this movement, you gain concealment against attacks of opportunity / reactive strikes."
    },
    "wholeness of body": {
        "name": "Wholeness of Body",
        "actions": "1 action",
        "traits": ["Concentrate", "Divine", "Focus", "Healing", "Manipulate"],
        "range": "Self",
        "defense": "None",
        "description": "You restore your body with ki. You regain 8 Hit Points per spell rank and cure one poison or disease affecting you."
    },
    "abundant step": {
        "name": "Abundant Step",
        "actions": "1 action",
        "traits": ["Concentrate", "Divine", "Focus", "Teleportation"],
        "range": "Variable",
        "defense": "None",
        "description": "You step through the ethereal membrane, teleporting up to your Speed to a space you can see."
    },
    # Champion Devotion Spells
    "litany against wrath": {
        "name": "Litany Against Wrath",
        "actions": "1 action",
        "traits": ["Concentrate", "Divine", "Focus", "Litany"],
        "range": "30 feet",
        "defense": "Will",
        "description": "Your words condemn anger. Target takes 3d6 spirit damage whenever it attacks a good creature."
    }
}

CLASS_FOCUS_SPELLS: Dict[str, Dict[str, Any]] = {
    "cleric": {
        "tradition": "Divine",
        "attr": "wis",
        "spells": []
    },
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

DRUID_ORDER_FOCUS_SPELLS: Dict[str, Dict[str, Any]] = {
    "wild": {
        "name": "Wild Shape (Untamed Form)",
        "actions": "2 actions",
        "traits": ["Focus", "Manipulate", "Polymorph", "Primal"],
        "range": "Self",
        "defense": "None",
        "description": "You infuse yourself with primal essence and transform into a pest, animal, or battle form (Pest Form, Animal Form, Insect Form, Elemental Form, Plant Form, Dragon Form, or Monstrosity Form as heightened)."
    },
    "untamed": {
        "name": "Wild Shape (Untamed Form)",
        "actions": "2 actions",
        "traits": ["Focus", "Manipulate", "Polymorph", "Primal"],
        "range": "Self",
        "defense": "None",
        "description": "You infuse yourself with primal essence and transform into a pest, animal, or battle form (Pest Form, Animal Form, Insect Form, Elemental Form, Plant Form, Dragon Form, or Monstrosity Form as heightened)."
    },
    "leaf": {
        "name": "Goodberry (Cornucopia)",
        "actions": "2 actions",
        "traits": ["Focus", "Healing", "Manipulate", "Primal", "Vitality"],
        "range": "Touch",
        "defense": "None",
        "description": "You imbue a ripe berry with primal life force; eating it restores 1d6+4 HP (+1d6+4 per spell rank)."
    },
    "storm": {
        "name": "Tempest Surge",
        "actions": "2 actions",
        "traits": ["Air", "Electricity", "Focus", "Manipulate", "Primal"],
        "range": "30 feet",
        "defense": "Basic Reflex",
        "description": "You surround a foe in a spinning vortex of wind and lightning dealing 1d12 electricity damage per rank and imposing clumsy 2 on a failed save."
    },
    "animal": {
        "name": "Heal Animal",
        "actions": "1 action",
        "traits": ["Focus", "Healing", "Manipulate", "Primal", "Vitality"],
        "range": "Touch",
        "defense": "None",
        "description": "You heal your companion animal for 1d8 HP per rank and grant them a +2 status bonus to AC for 1 round."
    },
    "flame": {
        "name": "Wildfire",
        "actions": "2 actions",
        "traits": ["Fire", "Focus", "Manipulate", "Primal"],
        "range": "30 feet",
        "defense": "Basic Reflex",
        "description": "You ignite a 10-foot burst of primal flames dealing 1d6 fire damage plus persistent fire damage."
    },
    "stone": {
        "name": "Crushing Ground",
        "actions": "2 actions",
        "traits": ["Earth", "Focus", "Manipulate", "Primal"],
        "range": "30 feet",
        "defense": "Reflex",
        "description": "Slabs of rock slam into a target dealing 2d6 bludgeoning damage per rank and knocking it prone on a failed save."
    },
    "wave": {
        "name": "Rising Surf",
        "actions": "1 action",
        "traits": ["Focus", "Manipulate", "Primal", "Water"],
        "range": "Self",
        "defense": "None",
        "description": "You ride a cresting wave up to 35 feet across ground or water, ignoring difficult terrain."
    },
}

def _get_druid_order_spell(subclass_name: Optional[str], feats: List[FeatSummary]) -> Dict[str, Any]:
    blob = " ".join([
        subclass_name or "",
        " ".join(f"{getattr(f, 'name', '')} {getattr(f, 'description', '')}" for f in (feats or []))
    ]).lower()
    for order_key, sp in DRUID_ORDER_FOCUS_SPELLS.items():
        if f"{order_key} order" in blob or f"{order_key} instinct" in blob or (order_key in ("wild", "untamed") and ("wild shape" in blob or "untamed form" in blob)):
            return sp
    return DRUID_ORDER_FOCUS_SPELLS["animal"]


def _append_deity_domain_spells(
    spells: List[SpellSummary],
    feats: List[FeatSummary],
    deity_data: Optional[Dict[str, Any]],
    tradition: str,
    curr_rank: int,
) -> None:
    if not deity_data:
        return
    try:
        from app.engine.deities import get_domain_info, get_deity_domains
    except Exception:
        return

    feat_names = [
        (getattr(f, "name", "") if not isinstance(f, dict) else f.get("name", "")) or ""
        for f in (feats or [])
    ]
    domain_feat_markers = (
        "domain initiate",
        "deity's domain",
        "deitys domain",
        "expanded domain initiate",
        "domain acumen",
        "domain fluency",
        "advanced domain",
        "advanced deity's domain",
        "advanced deitys domain",
        "splinter faith",
    )
    has_domain_feat = any(any(m in fn.lower() for m in domain_feat_markers) for fn in feat_names)
    chosen_doms: List[str] = []
    if isinstance(deity_data, dict):
        for d_item in deity_data.get("chosen_domains") or []:
            d_clean = str(d_item).strip().title()
            if d_clean and d_clean not in chosen_doms:
                chosen_doms.append(d_clean)

    for fn in feat_names:
        low = fn.lower()
        if any(m in low for m in domain_feat_markers) and "(" in fn and ")" in fn:
            inside = fn.split("(", 1)[1].rsplit(")", 1)[0]
            for part in inside.split(","):
                d_clean = part.strip().title()
                if d_clean and d_clean not in chosen_doms:
                    chosen_doms.append(d_clean)

    if not chosen_doms and has_domain_feat:
        d_list = get_deity_domains(deity_data.get("name"))
        if d_list:
            chosen_doms.append(d_list[0])

    for dom in chosen_doms:
        info = get_domain_info(dom)
        for key in ("domain_spell", "advanced_domain_spell"):
            sp_info = info.get(key)
            if isinstance(sp_info, dict) and sp_info.get("name"):
                sp_name = str(sp_info["name"]).strip()
                if any(s.name.lower() == sp_name.lower() for s in spells):
                    continue
                traits = ["Domain", "Focus", tradition.split(" ")[0]]
                spells.append(
                    SpellSummary(
                        name=sp_name,
                        rank=max(curr_rank, int(sp_info.get("rank") or 1)),
                        actions=str(sp_info.get("casting_time") or "1 action"),
                        traits=traits,
                        description=str(sp_info.get("description") or f"Granted by the {dom} domain ({deity_data.get('name')})."),
                    )
                )

def resolve_focus_spells(
    class_name: str,
    feats: List[FeatSummary],
    attribute_mods: Dict[str, int],
    subclass_name: Optional[str] = None,
    level: int = 1,
    deity_data: Optional[Dict[str, Any]] = None,
) -> Optional[FocusSpellData]:
    cls_key = class_name.lower()

    if cls_key == "summoner":
        sub_lower = (subclass_name or "").lower()
        if any(w in sub_lower for w in ["dragon", "construct"]):
            trad = "Arcane"
        elif any(w in sub_lower for w in ["angel", "demon", "devil", "psychopomp", "undead"]):
            trad = "Divine"
        elif any(w in sub_lower for w in ["beast", "elemental", "plant"]):
            trad = "Primal"
        else:
            trad = "Occult"

        attr_mod = attribute_mods.get("cha", 3)
        prof_bonus = 2 + level
        spell_dc = 10 + prof_bonus + attr_mod
        spell_attack = prof_bonus + attr_mod
        curr_rank = max(1, (level + 1) // 2)

        spells = [
            SpellSummary(
                name="Evolution Surge",
                rank=curr_rank,
                actions="1 action",
                traits=["Focus", "Manipulate", trad.lower()],
                description="Target eidolon gains your choice of: low-light vision & scent (30 ft), a +20 ft status bonus to Speed, or a swim/climb Speed equal to its land Speed (duration: 1 minute)."
            )
        ]

        if any("reinforce eidolon" in f.name.lower() for f in feats):
            spells.append(
                SpellSummary(
                    name="Reinforce Eidolon",
                    rank=curr_rank,
                    actions="1 action",
                    traits=["Cantrip", "Focus", "Manipulate", trad.lower()],
                    description="You focus your energy to boost your eidolon defenses. Your eidolon gains a +1 status bonus to AC and saving throws until the start of your next turn."
                )
            )

        return FocusSpellData(
            focus_points=1,
            max_focus_points=1,
            tradition=trad,
            casting_attribute="CHA",
            spell_dc=spell_dc,
            spell_attack=spell_attack,
            spells=spells
        )

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

    # Monk Ki Spells handling (Remaster)
    if cls_key == "monk":
        curr_rank = max(1, (level + 1) // 2)
        attr_key = "wis"
        attr_mod = attribute_mods.get(attr_key, 0)
        prof_bonus = 2 + level
        spell_dc = 10 + prof_bonus + attr_mod
        spell_attack = prof_bonus + attr_mod

        ki_spells = []
        feat_names_lower = [f.name.lower() for f in feats]

        # Map feats to Ki spells (supports Remaster & legacy Qi entries)
        ki_map = {
            "ki strike": {
                "name": "Ki Strike",
                "actions": "1 action",
                "traits": ["Concentrate", "Divine", "Focus"],
                "range": "Self",
                "defense": "None",
                "description": "Make an unarmed Strike with a +1 status bonus to hit and extra 1d6 force or elemental damage per rank."
            },
            "qi spells": {
                "name": "Ki Strike",
                "actions": "1 action",
                "traits": ["Concentrate", "Divine", "Focus"],
                "range": "Self",
                "defense": "None",
                "description": "Make an unarmed Strike with a +1 status bonus to hit and extra 1d6 force or elemental damage per rank."
            },
            "ki rush": {
                "name": "Ki Rush",
                "actions": "1 action",
                "traits": ["Concentrate", "Divine", "Focus"],
                "range": "Self",
                "defense": "None",
                "description": "Stride, Step, or Leap twice with concealment during movement."
            },
            "wholeness of body": {
                "name": "Wholeness of Body",
                "actions": "1 action",
                "traits": ["Concentrate", "Divine", "Focus", "Healing", "Manipulate"],
                "range": "Self",
                "defense": "None",
                "description": "Regain 8 HP per spell rank and cure one poison or disease."
            },
            "abundant step": {
                "name": "Abundant Step",
                "actions": "1 action",
                "traits": ["Concentrate", "Divine", "Focus", "Teleportation"],
                "range": "Variable",
                "defense": "None",
                "description": "Teleport up to your land Speed to an unoccupied space you can see."
            },
            "advanced qi spells": {
                "name": "Wholeness of Body",
                "actions": "1 action",
                "traits": ["Concentrate", "Divine", "Focus", "Healing", "Manipulate"],
                "range": "Self",
                "defense": "None",
                "description": "Regain 8 HP per spell rank and cure one poison or disease."
            },
            "ki blast": {
                "name": "Ki Blast",
                "actions": "1 to 3 actions",
                "traits": ["Concentrate", "Divine", "Focus"],
                "range": "Cone or Burst",
                "defense": "Fortitude",
                "description": "Unleash a blast of force dealing 2d6 damage per action spent, heightened +1d6 per rank."
            }
        }

        for feat_key, sp_data in ki_map.items():
            if any(feat_key in fn for fn in feat_names_lower):
                if not any(s.name.lower() == sp_data["name"].lower() for s in ki_spells):
                    ki_spells.append(SpellSummary(rank=curr_rank, **sp_data))

        # If the monk took no Ki feats, they do not have a Focus Pool
        if not ki_spells:
            return None

        pool_points = min(3, len(ki_spells))
        return FocusSpellData(
            focus_points=pool_points,
            max_focus_points=pool_points,
            tradition="Divine",
            casting_attribute="WIS",
            spell_dc=spell_dc,
            spell_attack=spell_attack,
            spells=ki_spells
        )

    # Check Druid Dedication (e.g., Wild Order -> Wild Shape / Untamed Form) for non-focus classes
    has_druid_ded = any("druid dedication" in getattr(f, "name", "").lower() for f in (feats or []))
    if cls_key not in CLASS_FOCUS_SPELLS and has_druid_ded:
        attr_mod = attribute_mods.get("wis", 0)
        prof_bonus = 2 + level
        curr_rank = max(1, (level + 1) // 2)
        order_sp = _get_druid_order_spell(subclass_name, feats)
        return FocusSpellData(
            focus_points=1,
            max_focus_points=1,
            tradition="Primal (Druid Dedication)",
            casting_attribute="WIS",
            spell_dc=10 + prof_bonus + attr_mod,
            spell_attack=prof_bonus + attr_mod,
            spells=[SpellSummary(rank=curr_rank, **order_sp)]
        )

    feat_names_lower = [
        (f.name if hasattr(f, "name") else (f.get("name", "") if isinstance(f, dict) else "")).lower()
        for f in (feats or [])
    ]
    has_time_mage_focus = any("time mage dedication" in fn for fn in feat_names_lower)

    # Standard classes
    has_beastmaster_focus = any("beastmaster dedication" in fn for fn in feat_names_lower)
    has_champion_focus = any("champion dedication" in fn for fn in feat_names_lower)

    if cls_key not in CLASS_FOCUS_SPELLS and (has_beastmaster_focus or has_champion_focus):
        attr_key = "wis" if has_beastmaster_focus else "cha"
        if attr_key not in attribute_mods:
            attr_key = "cha" if "cha" in attribute_mods else ("wis" if "wis" in attribute_mods else "int")
        attr_mod = attribute_mods.get(attr_key, 2)
        prof_bonus = 2 + level
        curr_rank = max(1, (level + 1) // 2)
        ded_spells: List[SpellSummary] = []
        trad_parts: List[str] = []

        if has_beastmaster_focus:
            trad_parts.append("Primal (Beastmaster Dedication)")
            ded_spells.append(SpellSummary(
                rank=curr_rank,
                name="Heal Animal",
                actions="1 action",
                traits=["Focus", "Healing", "Manipulate", "Primal", "Vitality"],
                range="Touch",
                defense="None",
                description="Granted by Beastmaster Dedication: You heal your companion animal for 1d8 HP per rank and grant a +2 status bonus to AC for 1 round."
            ))
        if has_champion_focus:
            trad_parts.append("Divine (Champion Dedication)")
            ded_spells.append(SpellSummary(
                rank=curr_rank,
                name="Lay on Hands",
                actions="1 action",
                traits=["Divine", "Focus", "Healing", "Manipulate", "Vitality"],
                range="Touch",
                defense="None",
                description="Granted by Champion Dedication: Your hands glow with righteous warmth, healing 6 HP per rank and granting +2 status AC for 1 round."
            ))

        pool = min(3, max(1, len(ded_spells)))
        return FocusSpellData(
            focus_points=pool,
            max_focus_points=pool,
            tradition=" / ".join(trad_parts),
            casting_attribute=attr_key.upper(),
            spell_dc=10 + prof_bonus + attr_mod,
            spell_attack=prof_bonus + attr_mod,
            spells=ded_spells,
        )

    if cls_key not in CLASS_FOCUS_SPELLS:
        if has_time_mage_focus:
            attr_key = "int" if attribute_mods.get("int", 0) >= attribute_mods.get("cha", 0) else "cha"
            if attr_key not in attribute_mods:
                attr_key = "wis" if "wis" in attribute_mods else "cha"
            attr_mod = attribute_mods.get(attr_key, 3)
            prof_bonus = 2 + level
            curr_rank = max(1, (level + 1) // 2)
            delay_consequence = SpellSummary(
                rank=curr_rank,
                name="Delay Consequence",
                actions="1 action",
                traits=["Concentrate", "Focus", "Prediction"],
                range="Self",
                defense="None",
                description="Granted by Time Mage Dedication: You defer immediate negative consequences of an effect until later in the encounter."
            )
            return FocusSpellData(
                focus_points=1,
                max_focus_points=1,
                tradition="Occult / Arcane (Time Mage Dedication)",
                casting_attribute=attr_key.upper(),
                spell_dc=10 + prof_bonus + attr_mod,
                spell_attack=prof_bonus + attr_mod,
                spells=[delay_consequence],
            )
        domain_spells_early: List[SpellSummary] = []
        _append_deity_domain_spells(domain_spells_early, feats, deity_data, "Divine", max(1, (level + 1) // 2))
        if domain_spells_early:
            attr_key = "cha" if attribute_mods.get("cha", 0) >= attribute_mods.get("wis", 0) else "wis"
            if attr_key not in attribute_mods:
                attr_key = "int" if "int" in attribute_mods else "cha"
            attr_mod = attribute_mods.get(attr_key, 2)
            prof_bonus = 2 + level
            pool = min(3, len(domain_spells_early))
            return FocusSpellData(
                focus_points=pool,
                max_focus_points=pool,
                tradition="Divine",
                casting_attribute=attr_key.upper(),
                spell_dc=10 + prof_bonus + attr_mod,
                spell_attack=prof_bonus + attr_mod,
                spells=domain_spells_early,
            )
        return None

    cfg = CLASS_FOCUS_SPELLS[cls_key]
    attr_key = cfg["attr"]
    attr_mod = attribute_mods.get(attr_key, 0)

    # Expert proficiency at level 7 for primary casters
    prof_mult = 4 if (level >= 7 and cls_key in ["cleric", "druid", "bard", "sorcerer", "oracle", "witch", "wizard", "psychic"]) else 2
    prof_bonus = prof_mult + level
    spell_dc = 10 + prof_bonus + attr_mod
    spell_attack = prof_bonus + attr_mod

    curr_rank = max(1, (level + 1) // 2)
    if cls_key == "druid":
        spells = [SpellSummary(rank=curr_rank, **_get_druid_order_spell(subclass_name, feats))]
    else:
        spells = [SpellSummary(rank=curr_rank, **s) for s in cfg["spells"]]
        if has_druid_ded:
            d_sp = _get_druid_order_spell(subclass_name, feats)
            if not any(s.name.lower() == d_sp["name"].lower() for s in spells):
                spells.append(SpellSummary(rank=curr_rank, **d_sp))

    # Dynamically discover additional focus spells gained via feats
    feat_names_lower = [f.name.lower() for f in feats]
    for feat_trigger, spell_def in FEAT_FOCUS_SPELLS.items():
        if any(feat_trigger in fn for fn in feat_names_lower):
            if not any(s.name.lower() == spell_def["name"].lower() for s in spells):
                spells.append(SpellSummary(rank=curr_rank, **spell_def))

    _append_deity_domain_spells(spells, feats, deity_data, cfg["tradition"], curr_rank)

    # Remaster rules: 1 Focus Point per known focus spell, capped at 3
    calculated_pool = min(3, max(1, len(spells)))

    return FocusSpellData(
        focus_points=calculated_pool,
        max_focus_points=calculated_pool,
        tradition=cfg["tradition"],
        casting_attribute=attr_key.upper(),
        spell_dc=spell_dc,
        spell_attack=spell_attack,
        spells=spells
    )
