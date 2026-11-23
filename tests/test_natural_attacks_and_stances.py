import pytest

from app.engine.concept_builder import ConceptToSheetBuilder
from app.engine.generator import PF2eGenerator


@pytest.fixture(scope="module")
def builder() -> ConceptToSheetBuilder:
    gen = PF2eGenerator()
    return ConceptToSheetBuilder(gen)


def _feat_names_lower(sheet: dict) -> list[str]:
    return [
        (f.get("name") if isinstance(f, dict) else getattr(f, "name", str(f))).lower()
        for f in (sheet.get("feats") or [])
    ]


def _strike_map(sheet: dict) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for s in ((sheet.get("equipment") or {}).get("strikes") or []):
        if isinstance(s, dict):
            name = str(s.get("name", ""))
            traits = [str(t).lower() for t in (s.get("traits") or [])]
            dice = str(s.get("damage_dice", ""))
            dtype = str(s.get("damage_type", ""))
        else:
            name = str(getattr(s, "name", ""))
            traits = [str(t).lower() for t in (getattr(s, "traits", None) or [])]
            dice = str(getattr(s, "damage_dice", ""))
            dtype = str(getattr(s, "damage_type", ""))
        if name:
            out[name.lower()] = {
                "name": name,
                "traits": traits,
                "damage_dice": dice,
                "damage_type": dtype,
            }
    return out


@pytest.mark.parametrize(
    "prompt,expected_feat,expected_strike_tokens",
    [
        ("A Catfolk fighter with Saber Teeth", "saber teeth", ("fangs", "jaws")),
        ("A level 11 Catfolk fighter with Saber Teeth", "saber teeth", ("fangs", "jaws")),
        ("A Kashrishi fighter with Puncturing Horn", "puncturing horn", ("horn",)),
        ("A level 11 Kashrishi fighter with Puncturing Horn", "puncturing horn", ("horn",)),
        ("A Gnoll fighter with Crunch", "crunch", ("jaws",)),
        ("An Orc fighter with Tusks (Orc)", "tusks (orc)", ("jaws", "tusk")),
        ("An Orc fighter with Tusks", "tusks (orc)", ("jaws", "tusk")),
        ("A Changeling fighter with Hag Claws", "hag claws", ("claw",)),
        ("An Automaton fighter with Powerful Tail", "powerful tail", ("tail",)),
        ("A Kitsune fighter with Retractable Claws", "retractable claws", ("claw",)),
        ("A Ghoran fighter with Hidden Thorn", "hidden thorn", ("thorn",)),
        ("A Goblin fighter with Fang Sharpener", "fang sharpener", ("fangs", "jaws")),
        ("A Goblin fighter with Hard Tail", "hard tail", ("tail",)),
        ("A Ratfolk fighter with Vicious Incisors", "vicious incisors", ("jaws",)),
        ("A Shisk fighter with Spine Stabber", "spine stabber", ("spines",)),
        ("A Centaur fighter with Steelhoof", "steelhoof", ("hoof",)),
        ("A Dhampir fighter with Fangs", "fangs", ("fangs",)),
        ("A Tengu fighter with Long-Nosed Form", "long-nosed form", ("beak",)),
    ],
)
def test_natural_attack_feat_pinning_and_strikes(
    builder: ConceptToSheetBuilder,
    prompt: str,
    expected_feat: str,
    expected_strike_tokens: tuple[str, ...],
):
    sheet = builder.build_lowest_level_sheet(prompt)
    feats = _feat_names_lower(sheet)
    strikes = _strike_map(sheet)

    assert expected_feat in feats, f"Expected feat '{expected_feat}' in {feats} for '{prompt}'"
    assert any(
        any(tok in s_name for tok in expected_strike_tokens) for s_name in strikes
    ), f"Expected strike matching {expected_strike_tokens} in {list(strikes.keys())} for '{prompt}'"


@pytest.mark.parametrize(
    "prompt,expected_feat,expected_strike_name",
    [
        ("A Monk with Wolf Stance", "wolf stance", "wolf jaws"),
        ("A level 11 Monk with Wolf Stance", "wolf stance", "wolf jaws"),
        ("A Monk with Tiger Stance", "tiger stance", "tiger claw"),
        ("A Monk with Gorilla Stance", "gorilla stance", "gorilla slam"),
        ("A Monk with Dragon Stance", "dragon stance", "dragon tail"),
    ],
)
def test_monk_stance_strikes(
    builder: ConceptToSheetBuilder,
    prompt: str,
    expected_feat: str,
    expected_strike_name: str,
):
    sheet = builder.build_lowest_level_sheet(prompt)
    feats = _feat_names_lower(sheet)
    strikes = _strike_map(sheet)

    assert expected_feat in feats
    assert expected_strike_name in strikes


def test_lizardfolk_iruxi_gets_claw_strike(builder: ConceptToSheetBuilder):
    sheet = builder.build_lowest_level_sheet("A Lizardfolk fighter")
    strikes = _strike_map(sheet)
    assert "claw" in strikes
    assert strikes["claw"]["damage_dice"] == "1d4"
    assert strikes["claw"]["damage_type"].lower() == "slashing"


@pytest.mark.parametrize(
    "prompt",
    [
        "An Orc fighter with Iron Fists",
        "A level 11 Orc fighter with Iron Fists",
    ],
)
def test_iron_fists_traits_and_damage(builder: ConceptToSheetBuilder, prompt: str):
    sheet = builder.build_lowest_level_sheet(prompt)
    feats = _feat_names_lower(sheet)
    strikes = _strike_map(sheet)

    assert "iron fists" in feats
    assert "fist" in strikes

    fist = strikes["fist"]
    assert fist["damage_dice"] == "1d4"
    assert fist["damage_type"].lower() == "bludgeoning"
    assert "shove" in fist["traits"]
    assert "nonlethal" not in fist["traits"]
