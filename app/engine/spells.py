import random
from typing import Dict, Any, List, Optional
from app.engine.models import SpellSummary, SpellSlotTracker, SpellcastingData

SPELL_CATALOG: Dict[str, Dict[str, List[Dict[str, Any]]]] = {
    "arcane": {
        "cantrips": [
            {"name": "Ignition", "actions": "2 actions", "traits": ["Arcane", "Attack", "Concentrate", "Fire", "Manipulate"], "range": "30 feet", "defense": "AC", "description": "You ignite a flame in your hand and hurl it at a foe for 2d4 fire damage (critical hit deals persistent fire)."},
            {"name": "Telekinetic Projectile", "actions": "2 actions", "traits": ["Arcane", "Attack", "Concentrate", "Manipulate"], "range": "30 feet", "defense": "AC", "description": "You hurl a loose object at a target for 2d6 bludgeoning, piercing, or slashing damage."},
            {"name": "Shield", "actions": "1 action", "traits": ["Arcane", "Cantrip", "Concentrate", "Force"], "range": "Self", "defense": "None", "description": "You raise a magical shield granting a +1 circumstance bonus to AC and the Shield Block reaction."},
            {"name": "Light", "actions": "2 actions", "traits": ["Arcane", "Cantrip", "Concentrate", "Light", "Manipulate"], "range": "Touch", "defense": "None", "description": "An object sheds bright light in a 20-foot radius for 1 hour."}
        ],
        "rank_1": [
            {"name": "Force Barrage", "actions": "1 to 3 actions", "traits": ["Arcane", "Force"], "range": "120 feet", "defense": "None", "description": "You fire unerring darts of magical force dealing 1d4+1 force damage per shard."},
            {"name": "Breathe Fire", "actions": "2 actions", "traits": ["Arcane", "Fire"], "range": "15-foot cone", "defense": "Basic Reflex", "description": "A torrent of flame deals 2d6 fire damage to all creatures in the area."},
            {"name": "Runic Weapon", "actions": "2 actions", "traits": ["Arcane", "Manipulate"], "range": "Touch", "defense": "None", "description": "A weapon becomes a +1 striking weapon (+1 attack, extra weapon damage die)."}
        ],
        "rank_2": [
            {"name": "Mist", "actions": "2 actions", "traits": ["Arcane", "Water"], "range": "120 feet", "defense": "None", "description": "A 20-foot burst of vapor grants concealment to all creatures within."},
            {"name": "Acid Grip", "actions": "2 actions", "traits": ["Arcane", "Acid"], "range": "30 feet", "defense": "Basic Reflex", "description": "Acidic claws grapple a target dealing 2d8 acid damage and moving them up to 20 feet."},
            {"name": "Laughing Fit", "actions": "2 actions", "traits": ["Arcane", "Emotion", "Mental"], "range": "30 feet", "defense": "Will", "description": "The target laughs uncontrollably, becoming clumsy 1 and unable to use reactions."}
        ],
        "rank_3": [
            {"name": "Fireball", "actions": "2 actions", "traits": ["Arcane", "Fire"], "range": "500 feet", "defense": "Basic Reflex", "description": "A roaring blast of flame erupts in a 20-foot burst, dealing 6d6 fire damage."},
            {"name": "Slow", "actions": "2 actions", "traits": ["Arcane", "Transmutation"], "range": "30 feet", "defense": "Fortitude", "description": "Dilates time around the target. On a failure, the target is slowed 1 for 1 minute; on a critical failure, slowed 2."},
            {"name": "Lightning Bolt", "actions": "2 actions", "traits": ["Arcane", "Electricity"], "range": "120-foot line", "defense": "Basic Reflex", "description": "A bolt of lightning arcs in a line dealing 4d12 electricity damage."}
        ],
        "rank_4": [
            {"name": "Fly", "actions": "2 actions", "traits": ["Arcane", "Transmutation"], "range": "Touch", "defense": "None", "description": "Target gains a fly Speed equal to its Speed (or 40 feet)."},
            {"name": "Fire Shield", "actions": "2 actions", "traits": ["Arcane", "Fire"], "range": "Self", "defense": "None", "description": "Flames wreath you, granting cold resistance 10 and damaging melee attackers."},
            {"name": "Resilient Sphere", "actions": "2 actions", "traits": ["Arcane", "Force"], "range": "30 feet", "defense": "Reflex", "description": "A sphere of force traps a creature or shields an ally."}
        ],
        "rank_5": [
            {"name": "Cone of Cold", "actions": "2 actions", "traits": ["Arcane", "Cold"], "range": "60-foot cone", "defense": "Basic Reflex", "description": "Freezing air deals 12d6 cold damage to creatures in the cone."},
            {"name": "Wall of Stone", "actions": "3 actions", "traits": ["Arcane", "Earth", "Structure"], "range": "120 feet", "defense": "None", "description": "You shape a solid wall of stone blocking passage and line of effect."},
            {"name": "Synaptic Pulse", "actions": "2 actions", "traits": ["Arcane", "Mental", "Stun"], "range": "30-foot emanation", "defense": "Will", "description": "A psychic shockwave pulses outward, leaving enemies stunned."}
        ]
    },
    "divine": {
        "cantrips": [
            {"name": "Divine Lance", "actions": "2 actions", "traits": ["Attack", "Divine", "Holy"], "range": "30 feet", "defense": "AC", "description": "You launch a beam of sanctified divine energy dealing 2d4 spirit damage."},
            {"name": "Guidance", "actions": "1 action", "traits": ["Cantrip", "Concentrate", "Divine"], "range": "30 feet", "defense": "None", "description": "Grants a +1 status bonus to one attack roll, Perception check, saving throw, or skill check."},
            {"name": "Forbidding Ward", "actions": "2 actions", "traits": ["Cantrip", "Concentrate", "Divine"], "range": "30 feet", "defense": "None", "description": "Target ally gains a +1 status bonus to AC and saves against attacks from a designated enemy."},
            {"name": "Vitality Lash", "actions": "2 actions", "traits": ["Cantrip", "Concentrate", "Divine", "Vitality"], "range": "30 feet", "defense": "Basic Fortitude", "description": "A lash of radiant energy deals 2d6 vitality damage to an undead target."}
        ],
        "rank_1": [
            {"name": "Heal", "actions": "1 to 3 actions", "traits": ["Divine", "Healing", "Vitality"], "range": "Varies", "defense": "None", "description": "Channels positive energy to heal living creatures or harm undead (1d8 HP per action/rank)."},
            {"name": "Sanctuary", "actions": "2 actions", "traits": ["Divine", "Abjuration"], "range": "Touch", "defense": "Will", "description": "Wards a creature. Foes attempting to attack the target must succeed at a Will save."},
            {"name": "Bless", "actions": "2 actions", "traits": ["Divine", "Concentrate"], "range": "15-foot emanation", "defense": "None", "description": "You and allies in the area gain a +1 status bonus to attack rolls. Can be sustained to expand."}
        ],
        "rank_2": [
            {"name": "Cleanse Affliction", "actions": "2 actions", "traits": ["Divine", "Healing"], "range": "Touch", "defense": "None", "description": "Attempt a counteract check to remove a poison, disease, or curse affecting the target."},
            {"name": "Spiritual Armament", "actions": "2 actions", "traits": ["Divine", "Force"], "range": "120 feet", "defense": "AC", "description": "Summons a glowing ghostly weapon of your deity dealing 2d8 damage on command."},
            {"name": "Warrior's Regret", "actions": "2 actions", "traits": ["Divine", "Emotion", "Mental"], "range": "30 feet", "defense": "Will", "description": "Striking the target forces it to feel psychic remorse, taking damage whenever it attacks."}
        ],
        "rank_3": [
            {"name": "Heroism", "actions": "2 actions", "traits": ["Divine", "Mental"], "range": "Touch", "defense": "None", "description": "A willingness to face danger infuses the target, granting a +1 status bonus to attack rolls, Perception, saving throws, and skill checks for 10 minutes."},
            {"name": "Crisis of Faith", "actions": "2 actions", "traits": ["Divine", "Mental"], "range": "30 feet", "defense": "Will", "description": "You assault the target's convictions, dealing 6d6 mental damage and stupefying them."},
            {"name": "Vampiric Feast", "actions": "2 actions", "traits": ["Divine", "Void"], "range": "Touch", "defense": "Basic Fortitude", "description": "You drink vitality from a foe, dealing 6d6 void damage and gaining temporary HP equal to half."}
        ]
    },
    "primal": {
        "cantrips": [
            {"name": "Gale Blast", "actions": "2 actions", "traits": ["Air", "Cantrip", "Primal"], "range": "5-foot emanation", "defense": "Fortitude", "description": "A burst of wind pushes adjacent enemies back 5 feet and deals 2d6 bludgeoning damage."},
            {"name": "Frostbite", "actions": "2 actions", "traits": ["Cantrip", "Cold", "Primal"], "range": "60 feet", "defense": "Basic Fortitude", "description": "Bitter cold deals 2d4 cold damage (fatigued on a critical failure)."},
            {"name": "Tangle Vine", "actions": "2 actions", "traits": ["Attack", "Cantrip", "Plant", "Primal"], "range": "30 feet", "defense": "AC", "description": "Vines entangle the target, imposing a -10 foot circumstance penalty to Speeds."},
            {"name": "Guidance", "actions": "1 action", "traits": ["Cantrip", "Concentrate", "Primal"], "range": "30 feet", "defense": "None", "description": "Grants a +1 status bonus to an attack roll, save, or skill check."}
        ],
        "rank_1": [
            {"name": "Heal", "actions": "1 to 3 actions", "traits": ["Healing", "Primal", "Vitality"], "range": "Varies", "defense": "None", "description": "Channels vital energy restoring 1d8 HP per action/rank."},
            {"name": "Thunderstrike", "actions": "2 actions", "traits": ["Electricity", "Primal", "Sonic"], "range": "120 feet", "defense": "Basic Reflex", "description": "A thunderous bolt calls down 1d12 electricity and 1d4 sonic damage."},
            {"name": "Pummeling Rubble", "actions": "2 actions", "traits": ["Earth", "Primal"], "range": "15-foot cone", "defense": "Basic Reflex", "description": "A spray of dirt and stone deals 2d4 bludgeoning damage and pushes targets back."}
        ],
        "rank_2": [
            {"name": "Entangling Flora", "actions": "2 actions", "traits": ["Plant", "Primal"], "range": "120 feet", "defense": "Reflex", "description": "Plants burst forth in a 20-foot burst, turning the area into difficult terrain and immobilizing foes."},
            {"name": "Blazing Dive", "actions": "2 actions", "traits": ["Fire", "Primal"], "range": "Fly up to Speed", "defense": "Basic Reflex", "description": "You fly in a blazing trail and detonate on impact for 3d4 fire damage."},
            {"name": "Mist", "actions": "2 actions", "traits": ["Primal", "Water"], "range": "120 feet", "defense": "None", "description": "Creates a thick cloud of fog granting concealment to creatures inside."}
        ],
        "rank_3": [
            {"name": "Lightning Bolt", "actions": "2 actions", "traits": ["Electricity", "Primal"], "range": "120-foot line", "defense": "Basic Reflex", "description": "A bolt of lightning arcs in a line dealing 4d12 electricity damage."},
            {"name": "Wall of Thorns", "actions": "3 actions", "traits": ["Plant", "Primal"], "range": "60 feet", "defense": "None", "description": "You create a dense barrier of briars. Creatures pushing through take 3d4 piercing damage."},
            {"name": "Cave Fangs", "actions": "2 actions", "traits": ["Earth", "Primal"], "range": "30 feet", "defense": "Basic Reflex", "description": "Stalagmites burst from the ground dealing 6d6 piercing damage and creating difficult terrain."}
        ]
    },
    "occult": {
        "cantrips": [
            {"name": "Daze", "actions": "2 actions", "traits": ["Cantrip", "Mental", "Occult"], "range": "60 feet", "defense": "Will", "description": "Jolts the target's mind with mental feedback dealing 2d6 mental damage (stupefied 1 on crit fail)."},
            {"name": "Telekinetic Projectile", "actions": "2 actions", "traits": ["Attack", "Cantrip", "Manipulate", "Occult"], "range": "30 feet", "defense": "AC", "description": "Hurls a loose object dealing 2d6 damage."},
            {"name": "Shield", "actions": "1 action", "traits": ["Cantrip", "Concentrate", "Force", "Occult"], "range": "Self", "defense": "None", "description": "Grants +1 circumstance bonus to AC and Shield Block."},
            {"name": "Void Warp", "actions": "2 actions", "traits": ["Cantrip", "Concentrate", "Occult", "Void"], "range": "30 feet", "defense": "Basic Fortitude", "description": "Assaults the target with entropic void energy dealing 2d4 void damage."}
        ],
        "rank_1": [
            {"name": "Soothe", "actions": "2 actions", "traits": ["Emotion", "Healing", "Mental", "Occult"], "range": "30 feet", "defense": "None", "description": "Soothes the mind to restore 1d10+4 HP and grant +2 status bonus to saves vs mental effects."},
            {"name": "Phantasmal Minion", "actions": "3 actions", "traits": ["Illusion", "Occult"], "range": "60 feet", "defense": "None", "description": "Creates an illusory servant capable of simple physical tasks."},
            {"name": "Sure Strike", "actions": "1 action", "traits": ["Concentrate", "Fortune", "Occult"], "range": "Self", "defense": "None", "description": "Roll twice on your next attack roll this turn and take the better result."}
        ],
        "rank_2": [
            {"name": "Invisibility", "actions": "2 actions", "traits": ["Illusion", "Occult"], "range": "Touch", "defense": "None", "description": "The target becomes invisible until it makes an attack or hostile action."},
            {"name": "Paranoia", "actions": "2 actions", "traits": ["Emotion", "Mental", "Occult"], "range": "30 feet", "defense": "Will", "description": "Target believes all creatures are its mortal enemies, treating everyone as foes."},
            {"name": "Sound Burst", "actions": "2 actions", "traits": ["Occult", "Sonic"], "range": "30 feet", "defense": "Fortitude", "description": "A cacophony deals 2d10 sonic damage in a 10-foot burst (deafened on failure)."}
        ],
        "rank_3": [
            {"name": "Heroism", "actions": "2 actions", "traits": ["Mental", "Occult"], "range": "Touch", "defense": "None", "description": "Infuses target with confidence, granting +1 status bonus to attacks, Perception, saves, and skills for 10 minutes."},
            {"name": "Slow", "actions": "2 actions", "traits": ["Occult", "Transmutation"], "range": "30 feet", "defense": "Fortitude", "description": "Target becomes slowed 1 for 1 minute on a failed Fortitude save."},
            {"name": "Vampiric Feast", "actions": "2 actions", "traits": ["Occult", "Void"], "range": "Touch", "defense": "Basic Fortitude", "description": "Deals 6d6 void damage and grants temporary HP equal to half."}
        ]
    }
}

CLASS_TRADITION_MAP = {
    "wizard": {"tradition": "Arcane", "attr": "int", "catalog": "arcane"},
    "sorcerer": {"tradition": "Primal", "attr": "cha", "catalog": "primal"},
    "druid": {"tradition": "Primal", "attr": "wis", "catalog": "primal"},
    "cleric": {"tradition": "Divine", "attr": "wis", "catalog": "divine"},
    "bard": {"tradition": "Occult", "attr": "cha", "catalog": "occult"},
    "witch": {"tradition": "Occult", "attr": "int", "catalog": "occult"},
    "oracle": {"tradition": "Divine", "attr": "cha", "catalog": "divine"},
    "animist": {"tradition": "Divine", "attr": "wis", "catalog": "divine"},
    "psychic": {"tradition": "Occult", "attr": "int", "catalog": "occult"},
    "magus": {"tradition": "Arcane", "attr": "int", "catalog": "arcane"}
}

def resolve_spellcasting(
    class_name: str,
    attribute_mods: Dict[str, int],
    level: int = 1,
    subclass_name: Optional[str] = None
) -> Optional[SpellcastingData]:
    cls_key = class_name.lower()
    if cls_key == "magus":
        trad_name, cat_key = "Arcane", "arcane"
        attr_mod = attribute_mods.get("int", 3)
        prof_bonus = 2 + level
        spell_dc = 10 + prof_bonus + attr_mod
        spell_attack = prof_bonus + attr_mod
        cat_data = SPELL_CATALOG["arcane"]
        cantrips = [SpellSummary(rank=0, **s) for s in cat_data["cantrips"]]

        # PF2e Bounded Spellcasting slot progression
        top_rank = (level + 1) // 2
        low_rank = max(1, top_rank - 1)
        
        if level <= 2:
            slots = [SpellSlotTracker(rank=1, max_slots=1 if level == 1 else 2)]
        elif top_rank == low_rank:
            slots = [SpellSlotTracker(rank=top_rank, max_slots=2)]
        else:
            slots = [
                SpellSlotTracker(rank=low_rank, max_slots=2),
                SpellSlotTracker(rank=top_rank, max_slots=2)
            ]

        rank_1 = [SpellSummary(rank=1, **s) for s in cat_data.get("rank_1", [])] if low_rank <= 1 else []
        rank_2 = [SpellSummary(rank=2, **s) for s in cat_data.get("rank_2", [])] if low_rank <= 2 <= top_rank else []
        rank_3 = [SpellSummary(rank=3, **s) for s in cat_data.get("rank_3", [])] if low_rank <= 3 <= top_rank else []
        rank_4 = [SpellSummary(rank=4, **s) for s in cat_data.get("rank_4", [])] if low_rank <= 4 <= top_rank else []
        rank_5 = [SpellSummary(rank=5, **s) for s in cat_data.get("rank_5", [])] if low_rank <= 5 <= top_rank else []

        return SpellcastingData(
            tradition=trad_name,
            casting_attribute="INT",
            spell_dc=spell_dc,
            spell_attack=spell_attack,
            cantrips=cantrips,
            rank_1_spells=rank_1,
            rank_2_spells=rank_2,
            rank_3_spells=rank_3,
            rank_4_spells=rank_4,
            rank_5_spells=rank_5,
            slots=slots
        )

    if cls_key == "summoner":
        sub_lower = (subclass_name or "").lower()
        if any(w in sub_lower for w in ["dragon", "construct"]):
            trad_name, cat_key = "Arcane", "arcane"
        elif any(w in sub_lower for w in ["angel", "demon", "devil", "psychopomp", "undead"]):
            trad_name, cat_key = "Divine", "divine"
        elif any(w in sub_lower for w in ["beast", "elemental", "plant"]):
            trad_name, cat_key = "Primal", "primal"
        else:
            trad_name, cat_key = "Occult", "occult"

        attr_mod = attribute_mods.get("cha", 3)
        prof_bonus = 2 + level
        spell_dc = 10 + prof_bonus + attr_mod
        spell_attack = prof_bonus + attr_mod

        cat_data = SPELL_CATALOG.get(cat_key, SPELL_CATALOG["occult"])
        cantrips = [SpellSummary(rank=0, **s) for s in cat_data["cantrips"]]

        # PF2e Bounded Spellcasting slot progression
        top_rank = (level + 1) // 2
        low_rank = max(1, top_rank - 1)
        
        if level <= 2:
            slots = [SpellSlotTracker(rank=1, max_slots=1 if level == 1 else 2)]
        elif top_rank == low_rank:
            slots = [SpellSlotTracker(rank=top_rank, max_slots=2)]
        else:
            slots = [
                SpellSlotTracker(rank=low_rank, max_slots=2),
                SpellSlotTracker(rank=top_rank, max_slots=2)
            ]

        rank_1 = [SpellSummary(rank=1, **s) for s in cat_data.get("rank_1", [])] if low_rank <= 1 else []
        rank_2 = [SpellSummary(rank=2, **s) for s in cat_data.get("rank_2", [])] if low_rank <= 2 <= top_rank else []
        rank_3 = [SpellSummary(rank=3, **s) for s in cat_data.get("rank_3", [])] if low_rank <= 3 <= top_rank else []
        rank_4 = [SpellSummary(rank=4, **s) for s in cat_data.get("rank_4", [])] if low_rank <= 4 <= top_rank else []
        rank_5 = [SpellSummary(rank=5, **s) for s in cat_data.get("rank_5", [])] if low_rank <= 5 <= top_rank else []

        return SpellcastingData(
            tradition=trad_name,
            casting_attribute="CHA",
            spell_dc=spell_dc,
            spell_attack=spell_attack,
            cantrips=cantrips,
            rank_1_spells=rank_1,
            rank_2_spells=rank_2,
            rank_3_spells=rank_3,
            rank_4_spells=rank_4,
            rank_5_spells=rank_5,
            slots=slots
        )

    if cls_key not in CLASS_TRADITION_MAP:
        return None

    cfg = CLASS_TRADITION_MAP[cls_key]
    trad_key = cfg["catalog"]
    attr_key = cfg["attr"]

    attr_mod = attribute_mods.get(attr_key, 0)
    prof_bonus = 2 + level
    spell_dc = 10 + prof_bonus + attr_mod
    spell_attack = prof_bonus + attr_mod

    cat_data = SPELL_CATALOG[trad_key]

    cantrips = [SpellSummary(rank=0, **s) for s in cat_data["cantrips"]]
    rank_1 = [SpellSummary(rank=1, **s) for s in cat_data["rank_1"]]
    rank_2 = [SpellSummary(rank=2, **s) for s in cat_data.get("rank_2", [])] if level >= 3 else []
    rank_3 = [SpellSummary(rank=3, **s) for s in cat_data.get("rank_3", [])] if level >= 5 else []
    rank_4 = [SpellSummary(rank=4, **s) for s in cat_data.get("rank_4", [])] if level >= 7 else []
    rank_5 = [SpellSummary(rank=5, **s) for s in cat_data.get("rank_5", [])] if level >= 9 else []

    slots = [SpellSlotTracker(rank=1, max_slots=3 if level >= 3 else 2)]
    if level >= 3:
        slots.append(SpellSlotTracker(rank=2, max_slots=3 if level >= 5 else 2))
    if level >= 5:
        slots.append(SpellSlotTracker(rank=3, max_slots=3 if level >= 7 else 2))
    if level >= 7:
        slots.append(SpellSlotTracker(rank=4, max_slots=3 if level >= 9 else 2))
    if level >= 9:
        slots.append(SpellSlotTracker(rank=5, max_slots=2))

    return SpellcastingData(
        tradition=cfg["tradition"],
        casting_attribute=attr_key.upper(),
        spell_dc=spell_dc,
        spell_attack=spell_attack,
        cantrips=cantrips,
        rank_1_spells=rank_1,
        rank_2_spells=rank_2,
        rank_3_spells=rank_3,
        rank_4_spells=rank_4,
        rank_5_spells=rank_5,
        slots=slots
    )
