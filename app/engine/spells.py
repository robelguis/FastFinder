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
        ],
        "rank_6": [
            {"name": "Chain Lightning", "actions": "2 actions", "traits": ["Arcane", "Electricity"], "range": "500 feet", "defense": "Basic Reflex", "description": "An arc of lightning deals 8d12 electricity damage and leaps from target to target."},
            {"name": "Disintegrate", "actions": "2 actions", "traits": ["Arcane", "Attack"], "range": "120 feet", "defense": "Fortitude", "description": "A green ray deals 12d10 damage and turns slain targets to fine dust."},
            {"name": "True Seeing", "actions": "2 actions", "traits": ["Arcane", "Revelation"], "range": "Self", "defense": "None", "description": "You see things as they actually are, piercing illusions and transmutations."}
        ],
        "rank_7": [
            {"name": "Contingency", "actions": "10 minutes", "traits": ["Arcane"], "range": "Self", "defense": "None", "description": "You prepare a spell to trigger automatically when a specified condition occurs."},
            {"name": "Eclipse Burst", "actions": "2 actions", "traits": ["Arcane", "Cold", "Darkness", "Void"], "range": "500 feet", "defense": "Basic Reflex", "description": "A 60-foot burst of freezing shadow deals 8d10 cold and 8d4 void damage."},
            {"name": "Prismatic Spray", "actions": "2 actions", "traits": ["Arcane", "Light"], "range": "30-foot cone", "defense": "Varies", "description": "Seven brilliant beams of light strike creatures with varied chromatic effects."}
        ],
        "rank_8": [
            {"name": "Polar Ray", "actions": "2 actions", "traits": ["Arcane", "Attack", "Cold"], "range": "120 feet", "defense": "AC", "description": "A blue-white ray deals 10d8 cold damage and inflicts drained 2."},
            {"name": "Maze", "actions": "2 actions", "traits": ["Arcane", "Extradimensional", "Teleportation"], "range": "30 feet", "defense": "None", "description": "Banishes a target into an extradimensional labyrinth from which it must escape."},
            {"name": "Undermine Reality", "actions": "2 actions", "traits": ["Arcane", "Illusion"], "range": "60 feet", "defense": "Will", "description": "Makes the target's attacks and spells feel unreal, reducing their damage and imposing stupefied."}
        ],
        "rank_9": [
            {"name": "Falling Stars", "actions": "2 actions", "traits": ["Arcane", "Fire"], "range": "500 feet", "defense": "Basic Reflex", "description": "Calls down four meteors that explode in 40-foot bursts for 6d10 bludgeoning and 14d6 fire damage."},
            {"name": "Foresight", "actions": "2 actions", "traits": ["Arcane", "Mental", "Prediction"], "range": "Touch", "defense": "None", "description": "Grants a sixth sense warning of danger, giving a +2 status bonus to initiative and reactions."},
            {"name": "Weird", "actions": "2 actions", "traits": ["Arcane", "Death", "Fear", "Illusion", "Mental"], "range": "120 feet", "defense": "Will", "description": "Conjures each foe's worst nightmare, dealing 16d6 mental damage and frightening targets."}
        ],
        "rank_10": [
            {"name": "Time Stop", "actions": "3 actions", "traits": ["Arcane"], "range": "Self", "defense": "None", "description": "You temporarily halt time for everyone else, gaining 3 free turns to act."},
            {"name": "Wish", "actions": "3 actions", "traits": ["Arcane"], "range": "Varies", "defense": "Varies", "description": "You alter reality itself to duplicate spells or produce extraordinary effects."},
            {"name": "Cataclysm", "actions": "2 actions", "traits": ["Arcane", "Air", "Cold", "Earth", "Fire", "Water"], "range": "1,000 feet", "defense": "Basic Reflex", "description": "Unleashes acid rain, earthquakes, lightning, and tsunami waves in a 60-foot burst."}
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
        ],
        "rank_4": [
            {"name": "Divine Wrath", "actions": "2 actions", "traits": ["Divine", "Sanctified"], "range": "100 feet", "defense": "Basic Fortitude", "description": "You channel righteous fury, dealing 4d10 spirit damage in a 20-foot burst and sickening foes."},
            {"name": "Vital Beacon", "actions": "2 actions", "traits": ["Divine", "Healing", "Vitality"], "range": "Self", "defense": "None", "description": "You radiate restorative energy that you or an ally can tap into as an action to heal HP."},
            {"name": "Air Walk", "actions": "2 actions", "traits": ["Air", "Divine"], "range": "Touch", "defense": "None", "description": "The target can walk on air as if it were solid ground for 5 minutes."}
        ],
        "rank_5": [
            {"name": "Breath of Life", "actions": "Reaction", "traits": ["Divine", "Healing"], "range": "60 feet", "defense": "None", "description": "Trigger: An ally within 60 ft would die. You restore 4d8 HP to prevent their death."},
            {"name": "Divine Immolation", "actions": "2 actions", "traits": ["Divine", "Fire", "Sanctified"], "range": "120 feet", "defense": "Basic Reflex", "description": "Holy fire bursts in a 20-foot area dealing 6d10 fire damage plus 2d6 persistent spirit damage."},
            {"name": "Cleanse Curse", "actions": "2 actions", "traits": ["Divine", "Healing"], "range": "Touch", "defense": "None", "description": "You attempt a counteract check against a curse or affliction afflicting the target."}
        ],
        "rank_6": [
            {"name": "Blade Barrier", "actions": "3 actions", "traits": ["Divine", "Force"], "range": "120 feet", "defense": "Basic Reflex", "description": "A 120-foot wall of whirling force blades deals 7d8 force damage to creatures passing through."},
            {"name": "Field of Life", "actions": "2 actions", "traits": ["Divine", "Healing", "Vitality"], "range": "30 feet", "defense": "None", "description": "A 20-foot burst of positive energy restores 1d8 HP each round to living creatures inside."},
            {"name": "Spirit Blast", "actions": "2 actions", "traits": ["Divine", "Force"], "range": "30 feet", "defense": "Basic Fortitude", "description": "Damages a creature's spiritual essence directly for 16d6 force damage."}
        ],
        "rank_7": [
            {"name": "Sunburst", "actions": "2 actions", "traits": ["Divine", "Fire", "Light", "Vitality"], "range": "500 feet", "defense": "Basic Reflex", "description": "A globe of searing sunlight deals 8d10 fire and 8d10 vitality damage to undead in a 60-foot burst."},
            {"name": "Regenerate", "actions": "2 actions", "traits": ["Divine", "Healing", "Vitality"], "range": "Touch", "defense": "None", "description": "Grants regeneration 15 for 1 minute, reattaching severed limbs and preventing death."},
            {"name": "Divine Decree", "actions": "2 actions", "traits": ["Divine", "Sanctified"], "range": "40-foot emanation", "defense": "Fortitude", "description": "Utters a sacred word dealing 7d10 spirit damage and enfeebling or paralyzing foes."}
        ],
        "rank_8": [
            {"name": "Divine Aura", "actions": "2 actions", "traits": ["Divine", "Sanctified"], "range": "10-foot emanation", "defense": "None", "description": "Grants allies within 10 feet a +1 status bonus to AC and saves and resistance 10 to unholy/holy damage."},
            {"name": "Moment of Renewal", "actions": "2 actions", "traits": ["Divine", "Healing"], "range": "Touch", "defense": "None", "description": "Up to 6 targets immediately gain the benefits of a full 8-hour night's rest."},
            {"name": "Canticle of Everlasting Grief", "actions": "2 actions", "traits": ["Curse", "Divine", "Emotion", "Mental"], "range": "120 feet", "defense": "Will", "description": "Deals 10d6 mental damage and strips the target of all status bonuses."}
        ],
        "rank_9": [
            {"name": "Foresight", "actions": "2 actions", "traits": ["Divine", "Mental", "Prediction"], "range": "Touch", "defense": "None", "description": "Grants a +2 status bonus to initiative and defensive reactions for 1 hour."},
            {"name": "Overwhelming Presence", "actions": "2 actions", "traits": ["Auditory", "Divine", "Emotion", "Mental", "Visual"], "range": "40-foot burst", "defense": "Will", "description": "Reveals divine majesty, forcing foes to bow in awe and become stunned."},
            {"name": "Massacre", "actions": "2 actions", "traits": ["Death", "Divine", "Void"], "range": "60-foot line", "defense": "Fortitude", "description": "A wave of necromantic entropy slays weaker creatures outright and deals 9d6 void damage."}
        ],
        "rank_10": [
            {"name": "Miracle", "actions": "3 actions", "traits": ["Divine"], "range": "Varies", "defense": "Varies", "description": "Channels your deity's supreme power to duplicate spells or reshape fate."},
            {"name": "Avatar", "actions": "2 actions", "traits": ["Divine", "Polymorph"], "range": "Self", "defense": "None", "description": "Transforms you into a towering battle avatar of your deity with fly Speed and devastating strikes."},
            {"name": "Revival", "actions": "2 actions", "traits": ["Divine", "Healing", "Vitality"], "range": "30 feet", "defense": "None", "description": "Restores 10d8+40 HP to all allies in a 30-foot burst and returns recently slain allies to life."}
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
        ],
        "rank_4": [
            {"name": "Hydraulic Torrent", "actions": "2 actions", "traits": ["Primal", "Water"], "range": "60-foot line", "defense": "Basic Fortitude", "description": "A raging blast of water deals 8d6 bludgeoning damage and pushes creatures back."},
            {"name": "Fly", "actions": "2 actions", "traits": ["Primal", "Transmutation"], "range": "Touch", "defense": "None", "description": "The target gains a fly Speed of 40 feet for 5 minutes."},
            {"name": "Solid Fog", "actions": "3 actions", "traits": ["Cold", "Primal", "Water"], "range": "120 feet", "defense": "None", "description": "Creates a 20-foot burst of dense mist that is greater difficult terrain and grants concealment."}
        ],
        "rank_5": [
            {"name": "Howling Blizzard", "actions": "2 actions", "traits": ["Cold", "Primal"], "range": "120 feet", "defense": "Basic Reflex", "description": "A fierce tempest deals 10d6 cold damage in a 20-foot burst and creates heavy difficult terrain."},
            {"name": "Grasping Spire", "actions": "2 actions", "traits": ["Earth", "Primal"], "range": "120 feet", "defense": "Reflex", "description": "A spire of stone erupts dealing 6d8 piercing damage and immobilizing the target on a hit."},
            {"name": "Heal", "actions": "1 to 3 actions", "traits": ["Healing", "Primal", "Vitality"], "range": "Varies", "defense": "None", "description": "Heightened to Rank 5: Restores 5d8 HP per action spent, or a 30-foot burst of 5d8 HP."}
        ],
        "rank_6": [
            {"name": "Chain Lightning", "actions": "2 actions", "traits": ["Electricity", "Primal"], "range": "500 feet", "defense": "Basic Reflex", "description": "An arc of lightning deals 8d12 electricity damage and jumps across multiple foes."},
            {"name": "Tangling Creepers", "actions": "3 actions", "traits": ["Plant", "Primal"], "range": "500 feet", "defense": "Reflex", "description": "Dense vines fill a 40-foot burst, lashing out to grab and immobilize enemies."},
            {"name": "Dragon Form", "actions": "2 actions", "traits": ["Polymorph", "Primal"], "range": "Self", "defense": "None", "description": "Transforms you into a fierce Large dragon with breath weapon, jaws, claws, and 100-ft fly Speed."}
        ],
        "rank_7": [
            {"name": "Sunburst", "actions": "2 actions", "traits": ["Fire", "Light", "Primal", "Vitality"], "range": "500 feet", "defense": "Basic Reflex", "description": "A blinding sphere of solar fire deals 8d10 fire damage in a 60-foot burst."},
            {"name": "Volcanic Eruption", "actions": "2 actions", "traits": ["Earth", "Fire", "Primal"], "range": "120 feet", "defense": "Basic Reflex", "description": "Magma erupts in a 5-foot-radius, 80-foot-tall cylinder dealing 14d6 fire damage and encasing foes in lava."},
            {"name": "Regenerate", "actions": "2 actions", "traits": ["Healing", "Primal", "Vitality"], "range": "Touch", "defense": "None", "description": "Grants regeneration 15 for 1 minute, rapidly knitting wounds and preventing death."}
        ],
        "rank_8": [
            {"name": "Earthquake", "actions": "2 actions", "traits": ["Earth", "Primal"], "range": "500 feet", "defense": "Reflex", "description": "Shakes a 60-foot burst violently, collapsing structures, opening fissures, and knocking foes prone."},
            {"name": "Polar Ray", "actions": "2 actions", "traits": ["Attack", "Cold", "Primal"], "range": "120 feet", "defense": "AC", "description": "Fires an arctic beam dealing 10d8 cold damage and inflicting drained 2."},
            {"name": "Monstrosity Form", "actions": "2 actions", "traits": ["Polymorph", "Primal"], "range": "Self", "defense": "None", "description": "Transforms you into a Gargantuan behemoth such as a phoenix, purple worm, or sea serpent."}
        ],
        "rank_9": [
            {"name": "Falling Stars", "actions": "2 actions", "traits": ["Fire", "Primal"], "range": "500 feet", "defense": "Basic Reflex", "description": "Calls down four blazing meteors dealing 6d10 bludgeoning and 14d6 fire damage."},
            {"name": "Storm of Vengeance", "actions": "3 actions", "traits": ["Air", "Electricity", "Primal"], "range": "800 feet", "defense": "Basic Reflex", "description": "Conjures a massive storm cloud unleashing acid rain, hail, gale winds, and lightning bolts."},
            {"name": "Nature's Enmity", "actions": "2 actions", "traits": ["Plant", "Primal"], "range": "120 feet", "defense": "Will", "description": "Turns the natural world hostile against up to 5 targets, imposing clumsy and slowed."}
        ],
        "rank_10": [
            {"name": "Primal Phenomenon", "actions": "3 actions", "traits": ["Primal"], "range": "Varies", "defense": "Varies", "description": "Commands the raw forces of nature to duplicate spells or reshape the environment."},
            {"name": "Cataclysm", "actions": "2 actions", "traits": ["Air", "Cold", "Earth", "Fire", "Primal", "Water"], "range": "1,000 feet", "defense": "Basic Reflex", "description": "Unleashes combined elemental disasters across a 60-foot burst."},
            {"name": "Nature Incarnate", "actions": "2 actions", "traits": ["Polymorph", "Primal"], "range": "Self", "defense": "None", "description": "Transforms you into a towering Green Man or Kaiju avatar of primeval nature."}
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
        ],
        "rank_4": [
            {"name": "Phantasmal Killer", "actions": "2 actions", "traits": ["Emotion", "Fear", "Illusion", "Mental", "Occult"], "range": "120 feet", "defense": "Will", "description": "Creates an illusion of fearsome doom dealing 8d6 mental damage and fleeing on a failure."},
            {"name": "Fly", "actions": "2 actions", "traits": ["Occult", "Transmutation"], "range": "Touch", "defense": "None", "description": "The target gains a fly Speed of 40 feet for 5 minutes."},
            {"name": "Vision of Death", "actions": "2 actions", "traits": ["Death", "Mental", "Occult"], "range": "30 feet", "defense": "Will", "description": "Forces a terrifying vision dealing 8d6 mental damage; critical failure causes instant death if below HP."}
        ],
        "rank_5": [
            {"name": "Synaptic Pulse", "actions": "2 actions", "traits": ["Mental", "Occult", "Stun"], "range": "30-foot emanation", "defense": "Will", "description": "A telepathic wave pulses outward, stunning enemies for 1 round on a failed save."},
            {"name": "Shadow Siphon", "actions": "Reaction", "traits": ["Illusion", "Occult", "Shadow"], "range": "60 feet", "defense": "None", "description": "Trigger: You or an ally would take energy damage. You weave shadows to reduce the damage by 5d8."},
            {"name": "Soothe", "actions": "2 actions", "traits": ["Emotion", "Healing", "Mental", "Occult"], "range": "30 feet", "defense": "None", "description": "Heightened to Rank 5: Restores 5d10+20 HP to an ally and grants +2 status bonus vs mental effects."}
        ],
        "rank_6": [
            {"name": "Phantasmal Calamity", "actions": "2 actions", "traits": ["Illusion", "Mental", "Occult"], "range": "500 feet", "defense": "Will", "description": "Creates an apocalyptic psychic illusion in a 30-foot burst dealing 11d6 mental damage and stunning foes."},
            {"name": "True Seeing", "actions": "2 actions", "traits": ["Occult", "Revelation"], "range": "Self", "defense": "None", "description": "Pierces illusions, invisibility, and transmutations within your line of sight."},
            {"name": "Spirit Blast", "actions": "2 actions", "traits": ["Force", "Occult"], "range": "30 feet", "defense": "Basic Fortitude", "description": "Launches concentrated ectoplasmic force dealing 16d6 force damage."}
        ],
        "rank_7": [
            {"name": "Warp Mind", "actions": "2 actions", "traits": ["Emotion", "Incapacitation", "Mental", "Occult"], "range": "120 feet", "defense": "Will", "description": "Shatters the target's psyche, inflicting severe confusion on a failed Will save."},
            {"name": "Visions of Danger", "actions": "3 actions", "traits": ["Auditory", "Illusion", "Mental", "Occult", "Visual"], "range": "500 feet", "defense": "Basic Will", "description": "Fills a 30-foot burst with phantom horrors dealing 8d8 mental damage each round."},
            {"name": "Plane Shift", "actions": "10 minutes", "traits": ["Occult", "Teleportation"], "range": "Touch", "defense": "Will", "description": "Transports you and up to 8 willing allies across planar boundaries."}
        ],
        "rank_8": [
            {"name": "Uncontrollable Dance", "actions": "2 actions", "traits": ["Emotion", "Incapacitation", "Mental", "Occult"], "range": "Touch", "defense": "Will", "description": "Forces the target into an irresistible dance, making it off-guard and unable to use reactions."},
            {"name": "Maze", "actions": "2 actions", "traits": ["Extradimensional", "Occult", "Teleportation"], "range": "30 feet", "defense": "None", "description": "Traps a foe inside an extradimensional labyrinth."},
            {"name": "Spirit Song", "actions": "2 actions", "traits": ["Force", "Occult"], "range": "60-foot cone", "defense": "Basic Fortitude", "description": "A resonant psychic chord deals 18d6 force damage to creatures in a 60-foot cone."}
        ],
        "rank_9": [
            {"name": "Weird", "actions": "2 actions", "traits": ["Death", "Fear", "Illusion", "Mental", "Occult"], "range": "120 feet", "defense": "Will", "description": "Manifests each creature's mortal dread in a 30-foot burst for 16d6 mental damage."},
            {"name": "Foresight", "actions": "2 actions", "traits": ["Mental", "Occult", "Prediction"], "range": "Touch", "defense": "None", "description": "Grants a +2 status bonus to initiative and reactions for 1 hour."},
            {"name": "Wail of the Banshee", "actions": "2 actions", "traits": ["Auditory", "Death", "Occult", "Void"], "range": "40-foot emanation", "defense": "Fortitude", "description": "Unleashes a soul-rending shriek dealing 8d10 void damage and inflicting drained."}
        ],
        "rank_10": [
            {"name": "Alter Reality", "actions": "3 actions", "traits": ["Occult"], "range": "Varies", "defense": "Varies", "description": "Reshapes the fabric of existence to duplicate spells or rewrite reality."},
            {"name": "Time Stop", "actions": "3 actions", "traits": ["Occult"], "range": "Self", "defense": "None", "description": "Halts the flow of time around you, granting 3 uninterrupted turns."},
            {"name": "Fabricated Truth", "actions": "3 actions", "traits": ["Incapacitation", "Mental", "Occult"], "range": "100 feet", "defense": "Will", "description": "Implants an unshakeable belief in up to 5 targets' minds."}
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
        rank_6 = [SpellSummary(rank=6, **s) for s in cat_data.get("rank_6", [])] if low_rank <= 6 <= top_rank else []
        rank_7 = [SpellSummary(rank=7, **s) for s in cat_data.get("rank_7", [])] if low_rank <= 7 <= top_rank else []
        rank_8 = [SpellSummary(rank=8, **s) for s in cat_data.get("rank_8", [])] if low_rank <= 8 <= top_rank else []
        rank_9 = [SpellSummary(rank=9, **s) for s in cat_data.get("rank_9", [])] if low_rank <= 9 <= top_rank else []
        rank_10 = [SpellSummary(rank=10, **s) for s in cat_data.get("rank_10", [])] if low_rank <= 10 <= top_rank else []

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
            rank_6_spells=rank_6,
            rank_7_spells=rank_7,
            rank_8_spells=rank_8,
            rank_9_spells=rank_9,
            rank_10_spells=rank_10,
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
        rank_6 = [SpellSummary(rank=6, **s) for s in cat_data.get("rank_6", [])] if low_rank <= 6 <= top_rank else []
        rank_7 = [SpellSummary(rank=7, **s) for s in cat_data.get("rank_7", [])] if low_rank <= 7 <= top_rank else []
        rank_8 = [SpellSummary(rank=8, **s) for s in cat_data.get("rank_8", [])] if low_rank <= 8 <= top_rank else []
        rank_9 = [SpellSummary(rank=9, **s) for s in cat_data.get("rank_9", [])] if low_rank <= 9 <= top_rank else []
        rank_10 = [SpellSummary(rank=10, **s) for s in cat_data.get("rank_10", [])] if low_rank <= 10 <= top_rank else []

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
            rank_6_spells=rank_6,
            rank_7_spells=rank_7,
            rank_8_spells=rank_8,
            rank_9_spells=rank_9,
            rank_10_spells=rank_10,
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
    rank_6 = [SpellSummary(rank=6, **s) for s in cat_data.get("rank_6", [])] if level >= 11 else []
    rank_7 = [SpellSummary(rank=7, **s) for s in cat_data.get("rank_7", [])] if level >= 13 else []
    rank_8 = [SpellSummary(rank=8, **s) for s in cat_data.get("rank_8", [])] if level >= 15 else []
    rank_9 = [SpellSummary(rank=9, **s) for s in cat_data.get("rank_9", [])] if level >= 17 else []
    rank_10 = [SpellSummary(rank=10, **s) for s in cat_data.get("rank_10", [])] if level >= 19 else []

    slots = [SpellSlotTracker(rank=1, max_slots=3 if level >= 3 else 2)]
    if level >= 3:
        slots.append(SpellSlotTracker(rank=2, max_slots=3 if level >= 5 else 2))
    if level >= 5:
        slots.append(SpellSlotTracker(rank=3, max_slots=3 if level >= 7 else 2))
    if level >= 7:
        slots.append(SpellSlotTracker(rank=4, max_slots=3 if level >= 9 else 2))
    if level >= 9:
        slots.append(SpellSlotTracker(rank=5, max_slots=3 if level >= 11 else 2))
    if level >= 11:
        slots.append(SpellSlotTracker(rank=6, max_slots=3 if level >= 13 else 2))
    if level >= 13:
        slots.append(SpellSlotTracker(rank=7, max_slots=3 if level >= 15 else 2))
    if level >= 15:
        slots.append(SpellSlotTracker(rank=8, max_slots=3 if level >= 17 else 2))
    if level >= 17:
        slots.append(SpellSlotTracker(rank=9, max_slots=3 if level >= 19 else 2))
    if level >= 19:
        slots.append(SpellSlotTracker(rank=10, max_slots=2 if level >= 20 else 1))

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
        rank_6_spells=rank_6,
        rank_7_spells=rank_7,
        rank_8_spells=rank_8,
        rank_9_spells=rank_9,
        rank_10_spells=rank_10,
        slots=slots
    )
