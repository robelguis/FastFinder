import random
from typing import Dict, List, Optional, Tuple
from app.engine.models import SpellEntry, SpellcastingLoadout

SPELL_COMPENDIUM: Dict[str, Dict[str, List[Dict]]] = {
    "Arcane": {
        "cantrips": [
            {"name": "Ignition", "actions": "2 actions", "range": "30 feet", "summary": "Fire attack dealing 2d4 fire damage (1d10 in melee).", "traits": ["attack", "fire", "cantrip"]},
            {"name": "Frostbite", "actions": "2 actions", "range": "60 feet", "summary": "Target takes 2d4 cold damage with Fortitude save against clumsy 1.", "traits": ["cold", "cantrip"]},
            {"name": "Telekinetic Projectile", "actions": "2 actions", "range": "30 feet", "summary": "Hurl an object dealing 2d6 bludgeoning, piercing, or slashing damage.", "traits": ["attack", "cantrip"]},
            {"name": "Shield", "actions": "1 action", "range": "Self", "summary": "+1 circumstance bonus to AC; can Shield Block for Hardness 5.", "traits": ["force", "cantrip"]},
            {"name": "Light", "actions": "2 actions", "range": "Touch", "summary": "Object sheds bright light in a 20-foot radius.", "traits": ["light", "cantrip"]},
            {"name": "Detect Magic", "actions": "2 actions", "range": "30-foot emanation", "summary": "Detect the presence of magic and active effects.", "traits": ["detection", "cantrip"]},
            {"name": "Prestidigitation", "actions": "2 actions", "range": "10 feet", "summary": "Perform minor magical tricks and sensory effects.", "traits": ["cantrip"]}
        ],
        "rank_1": [
            {"name": "Force Barrage", "actions": "1 to 3 actions", "range": "120 feet", "summary": "Fire 1 to 3 unerring darts of force dealing 1d4+1 damage each.", "traits": ["force"]},
            {"name": "Breathe Fire", "actions": "2 actions", "range": "15-foot cone", "summary": "Exhale a fan of flames dealing 2d6 fire damage (basic Reflex save).", "traits": ["fire", "area"]},
            {"name": "Thunderstrike", "actions": "2 actions", "range": "120 feet", "summary": "Call lightning and thunder dealing 1d12 electricity + 1d4 sonic damage.", "traits": ["electricity", "sonic"]},
            {"name": "Runic Weapon", "actions": "2 actions", "range": "Touch", "summary": "Target weapon becomes +1 striking (+1 attack, extra weapon die).", "traits": ["transmutation"]},
            {"name": "Grease", "actions": "2 actions", "range": "30 feet", "summary": "Slick surface makes targets prone on failed Reflex save.", "traits": ["area"]}
        ]
    },
    "Divine": {
        "cantrips": [
            {"name": "Divine Lance", "actions": "2 actions", "range": "30 feet", "summary": "Beam of divine force dealing 2d4 spirit damage.", "traits": ["attack", "spirit", "cantrip"]},
            {"name": "Vitality Lash", "actions": "2 actions", "range": "30 feet", "summary": "Lash undead with vital energy dealing 2d6 vitality damage.", "traits": ["vitality", "cantrip"]},
            {"name": "Forbidding Ward", "actions": "2 actions", "range": "30 feet", "summary": "Grant ally +1 status bonus to AC and saves against one foe.", "traits": ["abjuration", "cantrip"]},
            {"name": "Guidance", "actions": "1 action", "range": "30 feet", "summary": "+1 status bonus to one attack, check, or saving throw.", "traits": ["cantrip"]},
            {"name": "Light", "actions": "2 actions", "range": "Touch", "summary": "Object sheds bright light in a 20-foot radius.", "traits": ["light", "cantrip"]},
            {"name": "Shield", "actions": "1 action", "range": "Self", "summary": "+1 circumstance bonus to AC; can Shield Block.", "traits": ["force", "cantrip"]}
        ],
        "rank_1": [
            {"name": "Heal", "actions": "1 to 3 actions", "range": "Touch / 30ft", "summary": "Restore 1d8 vitality to living target or damage undead.", "traits": ["healing", "vitality"]},
            {"name": "Harm", "actions": "1 to 3 actions", "range": "Touch / 30ft", "summary": "Inflict 1d8 void damage to living target or heal undead.", "traits": ["void"]},
            {"name": "Bless", "actions": "2 actions", "range": "15-foot emanation", "summary": "+1 status bonus to attack rolls for you and allies.", "traits": ["aura"]},
            {"name": "Sanctuary", "actions": "2 actions", "range": "Touch", "summary": "Creatures must pass Will save to target the protected creature.", "traits": ["abjuration"]},
            {"name": "Command", "actions": "2 actions", "range": "30 feet", "summary": "Command target to drop prone, approach, flee, or release item.", "traits": ["mental"]}
        ]
    },
    "Occult": {
        "cantrips": [
            {"name": "Daze", "actions": "2 actions", "range": "60 feet", "summary": "Mental shock dealing Will mod stun/mental damage with Will save.", "traits": ["mental", "cantrip"]},
            {"name": "Telekinetic Projectile", "actions": "2 actions", "range": "30 feet", "summary": "Fling debris dealing 2d6 bludgeoning, piercing, or slashing damage.", "traits": ["attack", "cantrip"]},
            {"name": "Shield", "actions": "1 action", "range": "Self", "summary": "+1 circumstance bonus to AC; can Shield Block.", "traits": ["force", "cantrip"]},
            {"name": "Guidance", "actions": "1 action", "range": "30 feet", "summary": "+1 status bonus to a d20 roll.", "traits": ["cantrip"]},
            {"name": "Prestidigitation", "actions": "2 actions", "range": "10 feet", "summary": "Minor magic tricks and sensory effects.", "traits": ["cantrip"]},
            {"name": "Message", "actions": "1 action", "range": "120 feet", "summary": "Whisper a silent message that only the recipient can hear.", "traits": ["auditory", "cantrip"]}
        ],
        "rank_1": [
            {"name": "Soothe", "actions": "2 actions", "range": "30 feet", "summary": "Restore 1d10+4 HP and grant +2 status bonus against mental effects.", "traits": ["emotion", "healing", "mental"]},
            {"name": "Phantom Pain", "actions": "2 actions", "range": "30 feet", "summary": "2d4 mental damage and 1 persistent bleed + sickened 1.", "traits": ["illusion", "mental", "nonlethal"]},
            {"name": "Grim Trophy", "actions": "2 actions", "range": "30 feet", "summary": "Horrific illusion frightens targets with Will save.", "traits": ["fear", "mental"]},
            {"name": "Color Spray", "actions": "2 actions", "range": "15-foot cone", "summary": "Swirling colors blind, dazzle, or stun foes on Will save.", "traits": ["illusion", "visual"]},
            {"name": "Command", "actions": "2 actions", "range": "30 feet", "summary": "Compel target to follow a 1-word order.", "traits": ["mental"]}
        ]
    },
    "Primal": {
        "cantrips": [
            {"name": "Ignition", "actions": "2 actions", "range": "30 feet", "summary": "Hurl flame dealing 2d4 fire damage (1d10 melee).", "traits": ["attack", "fire", "cantrip"]},
            {"name": "Frostbite", "actions": "2 actions", "range": "60 feet", "summary": "Chill foe for 2d4 cold damage; clumsy 1 on critical failure.", "traits": ["cold", "cantrip"]},
            {"name": "Gale Blast", "actions": "1 action", "range": "5-foot emanation", "summary": "Wind gusts push enemies back and deal 1d6 bludgeoning damage.", "traits": ["air", "cantrip"]},
            {"name": "Guidance", "actions": "1 action", "range": "30 feet", "summary": "+1 status bonus to attack, check, or save.", "traits": ["cantrip"]},
            {"name": "Light", "actions": "2 actions", "range": "Touch", "summary": "Object sheds bright light.", "traits": ["light", "cantrip"]},
            {"name": "Tangle Vine", "actions": "2 actions", "range": "30 feet", "summary": "Vines grasp target giving 10-foot circumstance penalty to Speed.", "traits": ["attack", "plant", "cantrip"]}
        ],
        "rank_1": [
            {"name": "Heal", "actions": "1 to 3 actions", "range": "Touch / 30ft", "summary": "Heal 1d8 vitality to living target.", "traits": ["healing", "vitality"]},
            {"name": "Thunderstrike", "actions": "2 actions", "range": "120 feet", "summary": "1d12 electricity + 1d4 sonic damage.", "traits": ["electricity", "sonic"]},
            {"name": "Breathe Fire", "actions": "2 actions", "range": "15-foot cone", "summary": "2d6 fire damage to creatures in cone.", "traits": ["fire", "area"]},
            {"name": "Hydraulic Push", "actions": "2 actions", "range": "60 feet", "summary": "3d6 bludgeoning damage and pushes target up to 10 feet back.", "traits": ["attack", "water"]},
            {"name": "Runic Weapon", "actions": "2 actions", "range": "Touch", "summary": "+1 striking bonus to chosen weapon.", "traits": ["transmutation"]}
        ]
    }
}

CASTER_CONFIGS: Dict[str, Tuple[str, str, int, int]] = {
    "wizard": ("Arcane", "int", 5, 3),
    "cleric": ("Divine", "wis", 5, 2),
    "druid": ("Primal", "wis", 5, 2),
    "bard": ("Occult", "cha", 5, 2),
    "sorcerer": ("Arcane", "cha", 5, 3),
    "witch": ("Occult", "int", 5, 2),
}

def resolve_spellcasting(
    class_name: str,
    attribute_mods: Dict[str, int],
    level: int = 1
) -> Optional[SpellcastingLoadout]:
    cls_key = class_name.lower()
    if cls_key not in CASTER_CONFIGS:
        return None

    tradition, cast_attr, num_cantrips, num_rank1 = CASTER_CONFIGS[cls_key]
    cast_mod = attribute_mods.get(cast_attr, 0)

    trained_rank = 2
    spell_attack = trained_rank + level + cast_mod
    spell_dc = 10 + trained_rank + level + cast_mod

    tradition_data = SPELL_COMPENDIUM.get(tradition, SPELL_COMPENDIUM["Arcane"])

    avail_cantrips = list(tradition_data.get("cantrips", []))
    random.shuffle(avail_cantrips)
    chosen_cantrips = [
        SpellEntry(
            name=c["name"],
            rank=0,
            actions=c.get("actions", "2 actions"),
            range=c.get("range", "30 feet"),
            summary=c.get("summary", ""),
            traits=c.get("traits", [])
        )
        for c in avail_cantrips[:num_cantrips]
    ]

    avail_rank1 = list(tradition_data.get("rank_1", []))
    random.shuffle(avail_rank1)
    chosen_rank1 = [
        SpellEntry(
            name=s["name"],
            rank=1,
            actions=s.get("actions", "2 actions"),
            range=s.get("range", "30 feet"),
            summary=s.get("summary", ""),
            traits=s.get("traits", [])
        )
        for s in avail_rank1[:num_rank1]
    ]

    return SpellcastingLoadout(
        tradition=tradition,
        casting_attribute=cast_attr.upper(),
        spell_dc=spell_dc,
        spell_attack=spell_attack,
        cantrips=chosen_cantrips,
        rank_1_spells=chosen_rank1
    )
