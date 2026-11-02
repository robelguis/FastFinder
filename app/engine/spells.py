import random
from typing import Dict, List, Optional, Tuple
from app.engine.models import SpellEntry, SpellcastingLoadout

SPELL_COMPENDIUM: Dict[str, Dict[str, List[Dict]]] = {
    "Arcane": {
        "cantrips": [
            {
                "name": "Ignition",
                "actions": "2 actions",
                "range": "30 feet (or touch)",
                "targets": "1 creature",
                "defense": "AC",
                "traits": ["attack", "cantrip", "concentrate", "fire", "manipulate"],
                "description": "You ignite a burst of magical flame. Make a spell attack roll against the target's AC. On a hit, you deal 2d4 fire damage. If you make a melee attack, increase the damage dice to 1d10s. Critical Hit: Double damage plus 1d4 persistent fire damage."
            },
            {
                "name": "Frostbite",
                "actions": "2 actions",
                "range": "60 feet",
                "targets": "1 creature",
                "defense": "Fortitude",
                "traits": ["cantrip", "cold", "concentrate", "manipulate"],
                "description": "You freeze the air around the target. The target takes 2d4 cold damage with a basic Fortitude save. Critical Success: No effect. Success: Half damage. Failure: Full damage. Critical Failure: Double damage and clumsy 1 until the start of your next turn."
            },
            {
                "name": "Telekinetic Projectile",
                "actions": "2 actions",
                "range": "30 feet",
                "targets": "1 creature",
                "defense": "AC",
                "traits": ["attack", "cantrip", "concentrate", "manipulate"],
                "description": "You hurl a loose, unattended object at the target. Make a spell attack roll against the target's AC. On a hit, deal 2d6 bludgeoning, piercing, or slashing damage (appropriate to the object). Critical Hit: Double damage."
            },
            {
                "name": "Shield",
                "actions": "1 action",
                "range": "Self",
                "targets": "You",
                "defense": "None",
                "traits": ["cantrip", "concentrate", "force"],
                "description": "You raise a magical barrier of pure force. You gain a +1 circumstance bonus to AC until the start of your next turn. While the shield is up, you can use the Shield Block reaction to absorb damage with Hardness 5. If you block, the spell ends and cannot be recast for 10 minutes."
            },
            {
                "name": "Light",
                "actions": "2 actions",
                "range": "Touch",
                "targets": "1 object",
                "defense": "None",
                "traits": ["cantrip", "concentrate", "light", "manipulate"],
                "description": "The target object sheds bright light in a 20-foot radius (and dim light to the next 20 feet) for 1 hour. If cast on an object held by an unwilling creature, the target can attempt a Reflex save to avoid the effect."
            },
            {
                "name": "Detect Magic",
                "actions": "2 actions",
                "range": "30-foot emanation",
                "targets": "Area",
                "defense": "None",
                "traits": ["cantrip", "concentrate", "detection", "manipulate"],
                "description": "You send out a pulse that senses the presence of magic. You detect whether magic is present in the area, and whether any item or effect within the area is of a higher rank than your cantrip."
            },
            {
                "name": "Prestidigitation",
                "actions": "2 actions",
                "range": "10 feet",
                "targets": "1 object or area",
                "defense": "None",
                "traits": ["cantrip", "concentrate", "manipulate"],
                "description": "You perform minor magical effects: slowly lift 1 pound of material, clean or soil an item up to 1 Bulk, chill, warm, or flavor 1 pound of nonliving material, or craft a temporary crude sensory illusion lasting 1 hour."
            }
        ],
        "rank_1": [
            {
                "name": "Force Barrage",
                "actions": "1 to 3 actions",
                "range": "120 feet",
                "targets": "1 to 3 creatures",
                "defense": "None",
                "traits": ["concentrate", "force", "manipulate"],
                "description": "You fire unerring darts of magical energy. For each action spent casting this spell, fire one dart at any target in range. Each dart automatically hits and deals 1d4+1 force damage. Combine damage against a single target before applying resistances."
            },
            {
                "name": "Breathe Fire",
                "actions": "2 actions",
                "range": "15-foot cone",
                "targets": "All creatures in area",
                "defense": "Reflex",
                "traits": ["area", "concentrate", "fire", "manipulate"],
                "description": "A torrent of flame erupts from your hands. You deal 2d6 fire damage to all creatures within the cone (basic Reflex save). Critical Failure: Double damage plus 1 persistent fire damage."
            },
            {
                "name": "Thunderstrike",
                "actions": "2 actions",
                "range": "120 feet",
                "targets": "1 creature or object",
                "defense": "Reflex",
                "traits": ["concentrate", "electricity", "manipulate", "sonic"],
                "description": "A bolt of lightning strikes from above accompanied by a deafening crack of thunder. The target takes 1d12 electricity damage and 1d4 sonic damage (basic Reflex save). If the target is metal or wearing metal armor, it takes a -1 circumstance penalty to the save."
            },
            {
                "name": "Runic Weapon",
                "actions": "2 actions",
                "range": "Touch",
                "targets": "1 weapon",
                "defense": "None",
                "traits": ["concentrate", "manipulate", "transmutation"],
                "description": "Runic power suffuses the target weapon. For 1 minute, the weapon becomes a +1 striking weapon, granting a +1 item bonus to attack rolls and increasing its damage dice from one die to two (e.g., 1d8 becomes 2d8)."
            },
            {
                "name": "Grease",
                "actions": "2 actions",
                "range": "30 feet",
                "targets": "10-foot square or 1 item",
                "defense": "Reflex",
                "traits": ["area", "concentrate", "manipulate"],
                "description": "Magical slippery grease covers the area. Creatures in the area must succeed at a Reflex save or fall prone. Creatures attempting to move into or through the grease must succeed at an Acrobatics check against your spell DC or fall prone."
            }
        ]
    },
    "Divine": {
        "cantrips": [
            {
                "name": "Divine Lance",
                "actions": "2 actions",
                "range": "30 feet",
                "targets": "1 creature",
                "defense": "AC",
                "traits": ["attack", "cantrip", "concentrate", "manipulate", "spirit"],
                "description": "You unleash a beam of divine power that inflicts 2d4 spirit damage. Make a spell attack roll against the target's AC. Critical Hit: Double damage."
            },
            {
                "name": "Vitality Lash",
                "actions": "2 actions",
                "range": "30 feet",
                "targets": "1 undead creature",
                "defense": "Fortitude",
                "traits": ["cantrip", "concentrate", "manipulate", "vitality"],
                "description": "You lash an undead foe with pure vitality energy, dealing 2d6 vitality damage with a basic Fortitude save. Living creatures are unaffected."
            },
            {
                "name": "Forbidding Ward",
                "actions": "2 actions",
                "range": "30 feet",
                "targets": "1 ally and 1 enemy",
                "defense": "None",
                "traits": ["abjuration", "cantrip", "concentrate", "manipulate"],
                "description": "You erect an abjuration ward shielding your ally from a specific enemy. Your ally gains a +1 status bonus to Armor Class and saving throws against attacks, spells, and abilities originating from the targeted enemy. Sustained up to 1 minute."
            },
            {
                "name": "Guidance",
                "actions": "1 action",
                "range": "30 feet",
                "targets": "1 creature",
                "defense": "None",
                "traits": ["cantrip", "concentrate"],
                "description": "You pray for divine guidance. The target gains a +1 status bonus to one attack roll, Perception check, saving throw, or skill check rolled before the start of your next turn. A target is then immune to Guidance for 1 hour."
            },
            {
                "name": "Light",
                "actions": "2 actions",
                "range": "Touch",
                "targets": "1 object",
                "defense": "None",
                "traits": ["cantrip", "concentrate", "light", "manipulate"],
                "description": "The touched object sheds bright light in a 20-foot radius for 1 hour."
            },
            {
                "name": "Shield",
                "actions": "1 action",
                "range": "Self",
                "targets": "You",
                "defense": "None",
                "traits": ["cantrip", "concentrate", "force"],
                "description": "+1 circumstance bonus to AC until your next turn; can use Shield Block reaction to absorb 5 damage."
            }
        ],
        "rank_1": [
            {
                "name": "Heal",
                "actions": "1 to 3 actions",
                "range": "Touch (1-act) / 30ft (2-act) / 30ft emanation (3-act)",
                "targets": "1 willing living creature or undead",
                "defense": "Fortitude (if damaging undead)",
                "traits": ["concentrate", "healing", "manipulate", "vitality"],
                "description": "You channel positive healing energy. 1 Action: Touch, restores 1d8 HP. 2 Actions: 30 ft range, restores 1d8+8 HP. 3 Actions: 30 ft emanation heals all living creatures 1d8 HP (and harms undead with a basic Fortitude save)."
            },
            {
                "name": "Harm",
                "actions": "1 to 3 actions",
                "range": "Touch / 30ft / 30ft emanation",
                "targets": "1 living creature or undead",
                "defense": "Fortitude (if living)",
                "traits": ["concentrate", "manipulate", "void"],
                "description": "You channel negative void energy. Deals 1d8 void damage to a living creature (Fortitude save) or heals an undead creature for 1d8 HP (or 1d8+8 for 2 actions)."
            },
            {
                "name": "Bless",
                "actions": "2 actions",
                "range": "15-foot emanation",
                "targets": "You and allies in area",
                "defense": "None",
                "traits": ["aura", "concentrate", "manipulate"],
                "description": "Blessing radiates outward from you. You and all allies in the emanation gain a +1 status bonus to attack rolls. Once per turn, you can spend a single action to expand the emanation by 10 feet (up to 60 feet max). Lasts 1 minute."
            },
            {
                "name": "Sanctuary",
                "actions": "2 actions",
                "range": "Touch",
                "targets": "1 creature",
                "defense": "Will",
                "traits": ["abjuration", "concentrate", "manipulate"],
                "description": "Protective wards ward the target. Any creature attempting to attack or cast a hostile spell against the target must attempt a Will save against your spell DC. On a failure, the action is wasted. If the warded target takes a hostile action, Sanctuary ends."
            },
            {
                "name": "Command",
                "actions": "2 actions",
                "range": "30 feet",
                "targets": "1 creature",
                "defense": "Will",
                "traits": ["concentrate", "manipulate", "mental"],
                "description": "You shout a compelling divine order: Approach, Drop Prone, Flee, or Release. Target attempts a Will save. On a Failure, the creature must spend its next turn obeying the chosen command."
            }
        ]
    },
    "Occult": {
        "cantrips": [
            {
                "name": "Daze",
                "actions": "2 actions",
                "range": "60 feet",
                "targets": "1 creature",
                "defense": "Will",
                "traits": ["cantrip", "concentrate", "manipulate", "mental", "nonlethal"],
                "description": "You cloud the target's mind with mental static. Deals mental damage equal to your spellcasting attribute modifier (basic Will save). Critical Failure: Full damage and the target is stunned 1."
            },
            {
                "name": "Telekinetic Projectile",
                "actions": "2 actions",
                "range": "30 feet",
                "targets": "1 creature",
                "defense": "AC",
                "traits": ["attack", "cantrip", "concentrate", "manipulate"],
                "description": "Launch loose debris dealing 2d6 bludgeoning, piercing, or slashing damage on a spell attack roll."
            },
            {
                "name": "Shield",
                "actions": "1 action",
                "range": "Self",
                "targets": "You",
                "defense": "None",
                "traits": ["cantrip", "concentrate", "force"],
                "description": "+1 circumstance bonus to AC; can Shield Block for Hardness 5."
            },
            {
                "name": "Guidance",
                "actions": "1 action",
                "range": "30 feet",
                "targets": "1 creature",
                "defense": "None",
                "traits": ["cantrip", "concentrate"],
                "description": "+1 status bonus to one attack roll, Perception check, save, or skill check."
            },
            {
                "name": "Prestidigitation",
                "actions": "2 actions",
                "range": "10 feet",
                "targets": "1 object or area",
                "defense": "None",
                "traits": ["cantrip", "concentrate", "manipulate"],
                "description": "Perform minor sensory effects, clean/soil objects, or flavor food."
            },
            {
                "name": "Message",
                "actions": "1 action",
                "range": "120 feet",
                "targets": "1 creature",
                "defense": "None",
                "traits": ["auditory", "cantrip", "concentrate", "illusion", "linguistic"],
                "description": "You mouth words that carry invisibly to the target's ear. The target can whisper a reply back to you immediately as a reaction."
            }
        ],
        "rank_1": [
            {
                "name": "Soothe",
                "actions": "2 actions",
                "range": "30 feet",
                "targets": "1 willing creature",
                "defense": "None",
                "traits": ["concentrate", "emotion", "healing", "manipulate", "mental"],
                "description": "You soothe psychic trauma. Restores 1d10+4 Hit Points to the target and grants a +2 status bonus to saving throws against mental effects for 1 minute."
            },
            {
                "name": "Phantom Pain",
                "actions": "2 actions",
                "range": "30 feet",
                "targets": "1 creature",
                "defense": "Will",
                "traits": ["concentrate", "illusion", "manipulate", "mental", "nonlethal"],
                "description": "You inflict illusory agonies. The target takes 2d4 mental damage and 1 persistent bleed damage (basic Will save). Failure: Full damage and sickened 1. Critical Failure: Double damage and sickened 2."
            },
            {
                "name": "Grim Trophy",
                "actions": "2 actions",
                "range": "30 feet",
                "targets": "1 creature",
                "defense": "Will",
                "traits": ["concentrate", "fear", "manipulate", "mental"],
                "description": "An illusory terror appears before the target, inflicting frightened 1 (or frightened 2 on a critical failure)."
            },
            {
                "name": "Color Spray",
                "actions": "2 actions",
                "range": "15-foot cone",
                "targets": "Creatures in area",
                "defense": "Will",
                "traits": ["area", "concentrate", "illusion", "manipulate", "visual"],
                "description": "A dazzling swirl of colored light blinds, dazzles, or stuns foes based on their Will save result."
            },
            {
                "name": "Command",
                "actions": "2 actions",
                "range": "30 feet",
                "targets": "1 creature",
                "defense": "Will",
                "traits": ["concentrate", "manipulate", "mental"],
                "description": "Compel target to follow a 1-word order (Approach, Drop Prone, Flee, or Release) on a failed Will save."
            }
        ]
    },
    "Primal": {
        "cantrips": [
            {
                "name": "Ignition",
                "actions": "2 actions",
                "range": "30 feet",
                "targets": "1 creature",
                "defense": "AC",
                "traits": ["attack", "cantrip", "concentrate", "fire", "manipulate"],
                "description": "Hurl flame dealing 2d4 fire damage (1d10 melee attack) on a spell attack roll."
            },
            {
                "name": "Frostbite",
                "actions": "2 actions",
                "range": "60 feet",
                "targets": "1 creature",
                "defense": "Fortitude",
                "traits": ["cantrip", "cold", "concentrate", "manipulate"],
                "description": "Target takes 2d4 cold damage with a basic Fortitude save; clumsy 1 on a critical failure."
            },
            {
                "name": "Gale Blast",
                "actions": "1 action",
                "range": "5-foot emanation",
                "targets": "All enemies in area",
                "defense": "Fortitude",
                "traits": ["air", "cantrip", "concentrate", "manipulate"],
                "description": "Wind pushes enemies back 5 feet and deals 1d6 bludgeoning damage on a failed Fortitude save."
            },
            {
                "name": "Guidance",
                "actions": "1 action",
                "range": "30 feet",
                "targets": "1 creature",
                "defense": "None",
                "traits": ["cantrip", "concentrate"],
                "description": "+1 status bonus to attack roll, Perception check, save, or skill check."
            },
            {
                "name": "Light",
                "actions": "2 actions",
                "range": "Touch",
                "targets": "1 object",
                "defense": "None",
                "traits": ["cantrip", "concentrate", "light", "manipulate"],
                "description": "Object sheds bright light in a 20-foot radius for 1 hour."
            },
            {
                "name": "Tangle Vine",
                "actions": "2 actions",
                "range": "30 feet",
                "targets": "1 creature",
                "defense": "AC",
                "traits": ["attack", "cantrip", "concentrate", "manipulate", "plant"],
                "description": "Vines wrap around the target. On a hit, the creature takes a 10-foot circumstance penalty to its Speeds for 1 round (immobilized on a critical hit)."
            }
        ],
        "rank_1": [
            {
                "name": "Heal",
                "actions": "1 to 3 actions",
                "range": "Touch / 30ft / 30ft emanation",
                "targets": "1 living creature or undead",
                "defense": "Fortitude (if undead)",
                "traits": ["concentrate", "healing", "manipulate", "vitality"],
                "description": "Channel positive energy to heal living creatures or damage undead."
            },
            {
                "name": "Thunderstrike",
                "actions": "2 actions",
                "range": "120 feet",
                "targets": "1 creature or object",
                "defense": "Reflex",
                "traits": ["concentrate", "electricity", "manipulate", "sonic"],
                "description": "1d12 electricity + 1d4 sonic damage with a basic Reflex save."
            },
            {
                "name": "Breathe Fire",
                "actions": "2 actions",
                "range": "15-foot cone",
                "targets": "Creatures in area",
                "defense": "Reflex",
                "traits": ["area", "concentrate", "fire", "manipulate"],
                "description": "2d6 fire damage in a 15-foot cone with a basic Reflex save."
            },
            {
                "name": "Hydraulic Push",
                "actions": "2 actions",
                "range": "60 feet",
                "targets": "1 creature",
                "defense": "AC",
                "traits": ["attack", "concentrate", "manipulate", "water"],
                "description": "A powerful blast of water strikes the target for 3d6 bludgeoning damage and pushes it 5 feet back (double damage and 10 feet push on a critical hit)."
            },
            {
                "name": "Runic Weapon",
                "actions": "2 actions",
                "range": "Touch",
                "targets": "1 weapon",
                "defense": "None",
                "traits": ["concentrate", "manipulate", "transmutation"],
                "description": "Weapon becomes +1 striking (+1 attack, 2 weapon dice) for 1 minute."
            }
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
            targets=c.get("targets"),
            defense=c.get("defense"),
            description=c.get("description", ""),
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
            targets=s.get("targets"),
            defense=s.get("defense"),
            description=s.get("description", ""),
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
