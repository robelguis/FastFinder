import math
import random

from app.engine.generator import PF2eGenerator

ANCESTRIES = [
    ("Orc", "Hold-Scarred Orc"),
    ("Human", None),
    ("Elf", None),
    ("Dwarf", None),
    ("Gnome", None),
    ("Leshy", "Gourd Leshy"),
    ("Leshy", "Leaf Leshy"),
    ("Goblin", None),
    ("Halfling", None),
    ("Ratfolk", None),
    ("Azarketi", None),
]

CLASSES = [
    ("Necromancer", None),
    ("Fighter", None),
    ("Rogue", None),
    ("Wizard", None),
    ("Cleric", None),
    ("Druid", "Animal"),
    ("Ranger", "Flurry"),
    ("Investigator", "Interrogation"),
    ("Summoner", None),
    ("Champion", None),
    ("Witch", None),
    ("Bard", None),
    ("Exemplar", None),
    ("Kineticist", None),
]

CONCEPTS = [
    "Hold Mark with Defiled Corpse emblem and undead familiar",
    "Hold Mark with Burning Sun emblem diplomatic caster",
    "Hold Mark with Death's Head emblem wilderness tracker",
    "Hold Mark with Empty Hand emblem intimidating bruiser",
    "Orc frontline striker with tusks and heavy armor",
    "",
]


def test_randomized_undead_familiar_save_invariants():
    gen = PF2eGenerator()
    rng = random.Random(20261127)
    failures = []

    for idx in range(250):
        anc, heritage = rng.choice(ANCESTRIES)
        cls_name, sub = rng.choice(CLASSES)
        lvl = rng.randint(1, 20)
        concept = rng.choice(CONCEPTS)

        try:
            sheet = gen.generate(
                ancestry_name=anc,
                heritage_name=heritage,
                class_name=cls_name,
                subclass_name=sub,
                level=lvl,
                concept_text=concept,
            )
        except Exception as exc:
            failures.append(f"#{idx} (L{lvl} {anc}/{cls_name}): raised {type(exc).__name__}: {exc}")
            continue

        if not getattr(sheet, "name", None):
            failures.append(f"#{idx} (L{lvl} {anc}/{cls_name}): missing character name")
        if not getattr(sheet, "all_skills", None):
            failures.append(f"#{idx} (L{lvl} {anc}/{cls_name}): empty all_skills")

        for label, prof_obj in [
            ("fortitude", getattr(sheet.defenses, "fortitude", None)),
            ("reflex", getattr(sheet.defenses, "reflex", None)),
            ("will", getattr(sheet.defenses, "will", None)),
            ("perception", getattr(sheet, "perception", None)),
        ]:
            mod = getattr(prof_obj, "modifier", None)
            if mod is None or (isinstance(mod, float) and math.isnan(mod)):
                failures.append(f"#{idx} (L{lvl} {anc}/{cls_name}): invalid {label} modifier {mod!r}")

        seen_feats = set()
        for feat in (getattr(sheet, "feats", None) or []):
            feat_name = str(getattr(feat, "name", "") or "").strip().lower()
            if feat_name:
                if feat_name in seen_feats:
                    failures.append(f"#{idx} (L{lvl} {anc}/{cls_name}): duplicate feat {feat_name!r}")
                seen_feats.add(feat_name)

        partners = getattr(sheet, "partners", None) or (
            [sheet.companion] if getattr(sheet, "companion", None) else []
        )
        for partner in partners:
            p_traits = {str(t).strip().lower() for t in (getattr(partner, "traits", None) or [])}
            if ("undead" in p_traits or "familiar" in p_traits) and "animal" in p_traits:
                p_name = getattr(partner, "name", "<unnamed>")
                failures.append(
                    f"#{idx} (L{lvl} {anc}/{cls_name}): familiar/undead partner {p_name!r} has 'animal' trait"
                )

    assert not failures, "Stress test failures:\n" + "\n".join(failures[:25])
