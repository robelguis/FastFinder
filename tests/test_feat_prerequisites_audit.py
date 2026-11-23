import random
import pytest

from app.engine.generator import PF2eGenerator, load_data
from app.engine.subclasses import CLASS_SUBCLASSES
from app.engine.feat_prereqs import check_feat_prerequisites


ANCESTRIES = [
    "Human", "Dwarf", "Elf", "Gnome", "Goblin", "Halfling",
    "Leshy", "Orc", "Yaoguai", "Tengu", "Kitsune", "Catfolk",
]

ARCHETYPES = [
    "", "Beastmaster", "Bastion", "Sentinel", "Wizard",
    "Medic", "Cavalier", "Blessed One", "Rogue",
]


@pytest.fixture(scope="module")
def generator_and_catalog():
    gen = PF2eGenerator()
    feats_raw = load_data("feats.json")
    feats_list = feats_raw if isinstance(feats_raw, list) else feats_raw.get("feats", [])
    feat_by_id = {
        f.get("id"): f
        for f in feats_list
        if isinstance(f, dict) and f.get("id")
    }
    feat_by_name = {}
    for f in feats_list:
        if isinstance(f, dict) and f.get("name"):
            feat_by_name.setdefault(f["name"].lower(), f)
    return gen, feat_by_id, feat_by_name


def _audit_sheet(sheet, level: int, feat_by_id: dict, feat_by_name: dict) -> list[tuple]:
    data = sheet.model_dump()
    resolved_sub = data.get("subclass")
    sub_label = (
        resolved_sub.get("name")
        if isinstance(resolved_sub, dict)
        else (resolved_sub or "")
    )
    resolved_arch = data.get("archetype")
    arch_label = (
        resolved_arch.get("name")
        if isinstance(resolved_arch, dict)
        else (resolved_arch or "")
    )

    sheet_feats = data.get("feats") or []
    feat_names = [
        f.get("name") if isinstance(f, dict) else getattr(f, "name", str(f))
        for f in sheet_feats
    ]
    owned_set = set(feat_names)

    skill_ranks = {
        sk["name"].title(): int(sk.get("rank") or 0)
        for sk in (data.get("all_skills") or [])
        if isinstance(sk, dict) and sk.get("name")
    }
    raw_mods = data.get("attributes") or {}
    attr_mods = {
        k[:3].lower(): int(v)
        for k, v in raw_mods.items()
        if isinstance(v, (int, float))
    }

    mismatches = []
    for fobj in sheet_feats:
        fn = fobj.get("name") if isinstance(fobj, dict) else getattr(fobj, "name", str(fobj))
        fid = fobj.get("id") if isinstance(fobj, dict) else getattr(fobj, "id", None)
        cat = fobj.get("category") if isinstance(fobj, dict) else getattr(fobj, "category", "")
        base_name = fn.split("(", 1)[0].strip().lower()
        catalog_feat = (
            feat_by_id.get(fid)
            or feat_by_name.get(fn.lower())
            or feat_by_name.get(base_name)
        )
        if not catalog_feat:
            continue

        other_owned = {o for o in owned_set if o.lower() != fn.lower()}
        if not check_feat_prerequisites(
            catalog_feat,
            skill_ranks=skill_ranks,
            owned_feat_names=other_owned,
            attribute_mods=attr_mods,
            character_level=level,
            subclass_name=sub_label,
            archetype_name=arch_label,
        ):
            mismatches.append((fn, cat, catalog_feat.get("prerequisites")))
    return mismatches


def test_100_build_prerequisite_audit(generator_and_catalog):
    """Verifies 0 crashes and 0 feat prerequisite mismatches across 100 builds covering all 24 classes."""
    rng = random.Random(2026)
    gen, feat_by_id, feat_by_name = generator_and_catalog
    all_classes = sorted(CLASS_SUBCLASSES.keys())

    assert len(all_classes) >= 24, f"Expected 24 classes, found {len(all_classes)}"

    crashes = []
    mismatches = []

    for i in range(1, 101):
        cls_key = all_classes[(i - 1) % len(all_classes)]
        cls_title = cls_key.title()
        options = CLASS_SUBCLASSES[cls_key].get("options") or []
        sub_opt = rng.choice(options)["name"] if options else ""
        ancestry = rng.choice(ANCESTRIES)
        level = rng.randint(1, 9)
        arch = rng.choice(ARCHETYPES) if level >= 2 and rng.random() < 0.45 else ""

        try:
            sheet = gen.generate(
                ancestry_name=ancestry,
                class_name=cls_title,
                subclass_name=sub_opt,
                archetype_name=arch,
                use_dedication=bool(arch),
                level=level,
            )
        except Exception as exc:
            crashes.append((i, cls_title, sub_opt, level, arch, f"{type(exc).__name__}: {exc}"))
            continue

        for feat_err in _audit_sheet(sheet, level, feat_by_id, feat_by_name):
            mismatches.append((i, ancestry, cls_title, sub_opt, arch, level, *feat_err))

    assert not crashes, f"Generation crashes encountered ({len(crashes)}): {crashes[:5]}"
    assert not mismatches, f"Prerequisite mismatches encountered ({len(mismatches)}): {mismatches[:10]}"


def test_level_up_prerequisite_audit(generator_and_catalog):
    """Verifies that leveling a character from Level 1 to Level 8 preserves valid feat prerequisites."""
    rng = random.Random(2026)
    gen, feat_by_id, feat_by_name = generator_and_catalog
    all_classes = sorted(CLASS_SUBCLASSES.keys())

    mismatches = []
    for cls_key in all_classes:
        cls_title = cls_key.title()
        options = CLASS_SUBCLASSES[cls_key].get("options") or []
        sub_opt = rng.choice(options)["name"] if options else ""
        ancestry = rng.choice(ANCESTRIES)

        base_sheet = gen.generate(
            ancestry_name=ancestry,
            class_name=cls_title,
            subclass_name=sub_opt,
            level=1,
        )
        leveled_sheet = gen.level_up(base_sheet.model_dump(), target_level=8)
        for feat_err in _audit_sheet(leveled_sheet, 8, feat_by_id, feat_by_name):
            mismatches.append((ancestry, cls_title, sub_opt, *feat_err))

    assert not mismatches, f"Level-up prerequisite mismatches ({len(mismatches)}): {mismatches[:10]}"


def test_2500_build_level_1_to_20_monte_carlo_audit(generator_and_catalog):
    """Stress-tests 2,500 builds across levels 1-20 (including level_up transitions) with zero crashes, mismatches, or fake skills."""
    gen, feat_by_id, feat_by_name = generator_and_catalog
    rng = random.Random(2026)
    all_classes = sorted(CLASS_SUBCLASSES.keys())

    crashes = []
    mismatches = []
    fake_skills = []

    for i in range(1, 2501):
        cls_key = all_classes[(i - 1) % len(all_classes)]
        cls_title = cls_key.title()
        options = CLASS_SUBCLASSES[cls_key].get("options") or []
        sub_opt = rng.choice(options)["name"] if options else ""
        ancestry = rng.choice(ANCESTRIES)
        start_lvl = rng.randint(1, 20)
        arch = rng.choice(ARCHETYPES) if start_lvl >= 2 and rng.random() < 0.45 else ""

        try:
            sheet = gen.generate(
                ancestry_name=ancestry,
                class_name=cls_title,
                subclass_name=sub_opt,
                archetype_name=arch,
                use_dedication=bool(arch),
                level=start_lvl,
            )
            final_lvl = start_lvl
            if i % 5 == 0 and start_lvl < 20:
                target_lvl = rng.randint(start_lvl + 1, 20)
                sheet = gen.level_up(
                    sheet.model_dump(),
                    target_lvl,
                    use_dedication=bool(arch),
                    archetype_name=arch or None,
                )
                final_lvl = target_lvl
        except Exception as exc:
            crashes.append((i, ancestry, cls_title, sub_opt, arch, start_lvl, f"{type(exc).__name__}: {exc}"))
            continue

        for sk in (sheet.all_skills or []):
            sk_low = (sk.name or "").strip().lower()
            if any(bad in sk_low for bad in ("at least one skill", "a skill with", "recall knowledge")):
                fake_skills.append((i, cls_title, final_lvl, sk.name))

        for feat_err in _audit_sheet(sheet, final_lvl, feat_by_id, feat_by_name):
            mismatches.append((i, ancestry, cls_title, sub_opt, arch, final_lvl, *feat_err))

    assert not crashes, f"Encountered {len(crashes)} crashes; first 5: {crashes[:5]}"
    assert not fake_skills, f"Encountered {len(fake_skills)} fake skill entries; first 5: {fake_skills[:5]}"
    assert not mismatches, f"Encountered {len(mismatches)} prerequisite mismatches; first 10: {mismatches[:10]}"
