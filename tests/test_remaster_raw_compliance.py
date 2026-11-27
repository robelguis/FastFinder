"""Ground-truth Pathfinder 2e Remaster Level 1 RAW compliance tests.

Unlike regression tests that validate against FastFinder's own JSON files,
this suite asserts generated characters directly against hardcoded Paizo
Remaster (Player Core, Player Core 2, War of Immortals, Rage of Elements,
Guns & Gears, Dark Archive, Secrets of Magic) Level 1 rules.

Expect failures until underlying data files (classes.json, heritages.py,
skills.py, equipment.py, generator.py) are brought into RAW alignment.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Set, Tuple

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

# ---------------------------------------------------------------------------
# Hardcoded Paizo PF2e Remaster Level 1 Ground Truth
# ---------------------------------------------------------------------------
# Format: class_name -> (fort, ref, will, perception, class_hp, base_std_skills, mandatory_skills)
# - base_std_skills = total standard (non-Lore) skills granted by the class at L1 BEFORE +INT and +1 background.
#   (Includes mandatory skills + subclass/deity/racket skill + "X + INT" free choices.)
# - mandatory_skills = exact skills the class MUST be trained in at L1 regardless of subclass.
RAW_CLASS_L1: Dict[str, Tuple[str, str, str, str, int, int, Tuple[str, ...]]] = {
    "Alchemist":     ("E", "E", "T", "T",  8, 4, ("Crafting",)),
    "Animist":       ("T", "T", "E", "T",  8, 3, ("Religion",)),
    "Barbarian":     ("E", "T", "E", "E", 12, 4, ("Athletics",)),
    "Bard":          ("T", "T", "E", "E",  8, 6, ("Occultism", "Performance")),
    "Champion":      ("E", "T", "E", "T", 10, 4, ("Religion",)),
    "Cleric":        ("T", "T", "E", "T",  8, 4, ("Religion",)),
    "Druid":         ("T", "T", "E", "T",  8, 4, ("Nature",)),
    "Exemplar":      ("E", "T", "E", "T", 10, 4, ("Religion",)),
    "Fighter":       ("E", "E", "T", "E", 10, 4, ()),  # Acrobatics OR Athletics + 3 + INT
    "Gunslinger":    ("E", "E", "T", "E",  8, 4, ()),  # Way skill + 3 + INT
    "Inventor":      ("E", "T", "E", "T",  8, 4, ("Crafting",)),
    "Investigator":  ("T", "E", "E", "E",  8, 6, ("Society",)),
    "Kineticist":    ("E", "E", "T", "T",  8, 4, ("Nature",)),
    "Magus":         ("E", "T", "E", "T",  8, 3, ("Arcana",)),
    "Monk":          ("E", "E", "E", "T", 10, 4, ()),  # Only class with E/E/E saves at L1
    "Oracle":        ("T", "T", "E", "T",  8, 5, ("Religion",)),
    "Psychic":       ("T", "T", "E", "T",  6, 4, ("Occultism",)),
    "Ranger":        ("E", "E", "T", "E", 10, 6, ("Nature", "Survival")),
    "Rogue":         ("T", "E", "E", "E",  8, 9, ("Stealth",)),
    "Sorcerer":      ("T", "T", "E", "T",  6, 4, ()),  # 2 bloodline skills + 2 + INT
    "Summoner":      ("E", "T", "E", "T", 10, 4, ()),  # 1 tradition skill + 3 + INT
    "Swashbuckler":  ("T", "E", "E", "E", 10, 6, ("Acrobatics",)),
    "Thaumaturge":   ("E", "T", "E", "E",  8, 7, ("Arcana", "Nature", "Occultism", "Religion")),
    "Witch":         ("T", "T", "E", "T",  6, 4, ()),  # 1 patron skill + 3 + INT
    "Wizard":        ("T", "T", "E", "T",  6, 3, ("Arcana",)),
}

RANK_BONUS = {"U": 0, "T": 2, "E": 4, "M": 6, "L": 8}

OFFICIAL_AZARKETI_HERITAGES: Set[str] = {
    "ancient scale",
    "benthic",
    "inured",
    "mistbreath",
    "murkeyed",
    "river",
    "spined",
    "tactile",
    "thalassic",
}

OFFICIAL_VERSATILE_HERITAGES: Set[str] = {
    "aiuvarin",
    "ardande",
    "beastkin",
    "changeling",
    "dhampir",
    "dragonblood",
    "dromaar",
    "duskwalker",
    "ganzi",
    "ifrit",
    "mixed ancestry",
    "nephilim",
    "oread",
    "reflection",
    "suli",
    "sylph",
    "talos",
    "tiefling",
    "aasimar",
    "undine",
    "aphoris",
    "aphorite",
}

# Standard PF2e Remaster Level 1 item prices in copper pieces (1 gp = 100 cp, 1 sp = 10 cp)
COMMON_ITEM_PRICES_CP: Dict[str, int] = {
    # Armor
    "explorer's clothing": 10,
    "padded armor": 20,
    "leather": 200,
    "leather armor": 200,
    "studded leather": 300,
    "studded leather armor": 300,
    "chain shirt": 500,
    "hide": 200,
    "hide armor": 200,
    "scale mail": 400,
    "chain mail": 600,
    "breastplate": 800,
    "splint mail": 1300,
    "half plate": 1800,
    "full plate": 3000,
    # Shields
    "buckler": 100,
    "wooden shield": 100,
    "steel shield": 200,
    "tower shield": 1000,
    # Common Weapons
    "dagger": 20,
    "club": 0,
    "staff": 0,
    "sling": 0,
    "spear": 10,
    "mace": 100,
    "morningstar": 100,
    "shortsword": 90,
    "longsword": 100,
    "rapier": 200,
    "scimitar": 100,
    "bastard sword": 400,
    "greatsword": 200,
    "greataxe": 200,
    "battle axe": 100,
    "warhammer": 100,
    "maul": 300,
    "glaive": 100,
    "halberd": 200,
    "guisarme": 200,
    "longspear": 50,
    "shortbow": 300,
    "longbow": 600,
    "composite shortbow": 1400,
    "composite longbow": 2000,
    "crossbow": 300,
    "heavy crossbow": 400,
    "hand crossbow": 300,
    "flail": 80,
    "war flail": 200,
    "whip": 10,
    "starknife": 200,
    "katana": 200,
    "scourge": 10,
    "sickle": 20,
    "trident": 100,
    # Consumables & Packs
    "minor healing potion": 400,
    "minor elixir of life": 300,
    "adventurer's pack": 150,
}

_RE_COIN = re.compile(r"(\d+)\s*(pp|gp|sp|cp)", re.IGNORECASE)
_RE_QTY = re.compile(r"(?:qty|x)\s*[:=]?\s*(\d+)", re.IGNORECASE)


def _generate_l1(class_name: str, ancestry: str = "Human", **extra: Any) -> Dict[str, Any]:
    params = {"class_name": class_name, "ancestry": ancestry, "level": 1}
    params.update(extra)
    resp = client.get("/api/generate", params=params)
    assert resp.status_code == 200, f"/api/generate failed for {params}: {resp.text}"
    return resp.json()


def _parse_coins_to_cp(text: Any) -> int:
    if text is None:
        return 0
    if isinstance(text, (int, float)):
        return int(text) * 100  # assume GP if numeric
    s = str(text)
    mult = {"pp": 1000, "gp": 100, "sp": 10, "cp": 1}
    total = 0
    for amount, unit in _RE_COIN.findall(s):
        total += int(amount) * mult[unit.lower()]
    return total


def _estimate_l1_wealth_cp(sheet: Dict[str, Any]) -> Tuple[int, List[str]]:
    """Returns a conservative lower-bound estimate (in cp) of total Level 1 wealth on the sheet."""
    eq = sheet.get("equipment") or {}
    total_cp = 0
    breakdown: List[str] = []

    # 1. Remaining coins
    for coin_key in ("currency", "coins", "remaining_gold", "gold", "wealth"):
        if coin_key in eq and eq[coin_key]:
            c_cp = _parse_coins_to_cp(eq[coin_key])
            if c_cp:
                total_cp += c_cp
                breakdown.append(f"coins({eq[coin_key]})={c_cp}cp")
                break

    # 2. Armor
    armor = eq.get("armor")
    armor_name = (armor.get("name") if isinstance(armor, dict) else str(armor or "")).strip().lower()
    for k, price in COMMON_ITEM_PRICES_CP.items():
        if armor_name == k or (k in armor_name and len(k) > 4):
            total_cp += price
            breakdown.append(f"armor({armor_name})={price}cp")
            break

    # 3. Weapons (deduped by base name)
    seen_weapons: Set[str] = set()
    for w in (eq.get("weapons") or []):
        w_name = (w.get("name") if isinstance(w, dict) else str(w or "")).strip().lower()
        if not w_name or w_name in seen_weapons:
            continue
        seen_weapons.add(w_name)
        if w_name in COMMON_ITEM_PRICES_CP:
            price = COMMON_ITEM_PRICES_CP[w_name]
            total_cp += price
            breakdown.append(f"weapon({w_name})={price}cp")

    # 4. Gear & Consumables
    for list_key in ("gear", "consumables", "items"):
        for item in (eq.get(list_key) or []):
            if isinstance(item, dict):
                name = str(item.get("name") or "").strip().lower()
                qty = int(item.get("quantity") or item.get("qty") or 1)
            else:
                raw = str(item or "").strip()
                name = raw.lower()
                m_q = _RE_QTY.search(raw)
                qty = int(m_q.group(1)) if m_q else 1
            for k, price in COMMON_ITEM_PRICES_CP.items():
                if k in name:
                    cost = price * qty
                    total_cp += cost
                    breakdown.append(f"{list_key}({name} x{qty})={cost}cp")
                    break

    return total_cp, breakdown


# ---------------------------------------------------------------------------
# 1. Level 1 Saving Throws & Perception (All 25 Classes)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("class_name,spec", list(RAW_CLASS_L1.items()))
def test_level1_saves_and_perception_raw(class_name: str, spec: Tuple[Any, ...]):
    exp_fort, exp_ref, exp_will, exp_perc, _hp, _skills, _mand = spec
    sheet = _generate_l1(class_name)

    attrs = sheet["attributes"]
    defs = sheet["defenses"]
    perc = sheet["perception"]

    checks = [
        ("Fortitude", defs["fortitude"], exp_fort, int(attrs["con"])),
        ("Reflex", defs["reflex"], exp_ref, int(attrs["dex"])),
        ("Will", defs["will"], exp_will, int(attrs["wis"])),
        ("Perception", perc, exp_perc, int(attrs["wis"])),
    ]
    for label, prof_obj, exp_rank, attr_mod in checks:
        got_rank = str(prof_obj.get("rank_letter") or "").upper()
        got_mod = int(prof_obj.get("modifier"))
        exp_mod = 1 + RANK_BONUS[exp_rank] + attr_mod
        assert got_rank == exp_rank, (
            f"[{class_name} L1] {label} rank is {got_rank}, expected RAW {exp_rank}"
        )
        assert got_mod == exp_mod, (
            f"[{class_name} L1] {label} modifier is +{got_mod}, expected RAW +{exp_mod} "
            f"(level 1 + {exp_rank}({RANK_BONUS[exp_rank]}) + attr {attr_mod:+d})"
        )


# ---------------------------------------------------------------------------
# 2. Level 1 Mandatory Skills & Minimum Trained Skill Count
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("class_name,spec", list(RAW_CLASS_L1.items()))
def test_level1_skills_and_mandatory_training_raw(class_name: str, spec: Tuple[Any, ...]):
    _f, _r, _w, _p, _hp, base_std_skills, mandatory_skills = spec
    sheet = _generate_l1(class_name)
    attrs = sheet["attributes"]
    int_mod = int(attrs.get("int", 0))

    skills = sheet.get("all_skills") or []
    trained_by_name = {
        str(s.get("name") or "").strip().lower(): s
        for s in skills
        if str(s.get("rank_letter") or "U").upper() != "U"
    }

    for req_skill in mandatory_skills:
        assert req_skill.lower() in trained_by_name, (
            f"[{class_name} L1] Missing mandatory RAW trained skill: {req_skill}"
        )

    trained_std = [
        name for name in trained_by_name
        if "lore" not in name
    ]
    trained_lores = [
        name for name in trained_by_name
        if "lore" in name
    ]

    # RAW: class base skills + 1 from background + INT modifier (minimum +0 if negative INT? Wait: negative INT reduces free skills by 1, clamped at 0)
    expected_min_std = max(1, base_std_skills + 1 + int_mod)
    assert len(trained_std) >= expected_min_std, (
        f"[{class_name} L1] Only {len(trained_std)} trained standard skills ({sorted(trained_std)}); "
        f"RAW requires at least {expected_min_std} (class {base_std_skills} + bg 1 + INT {int_mod:+d})"
    )
    assert len(trained_lores) >= 1, (
        f"[{class_name} L1] Missing trained background Lore skill"
    )


# ---------------------------------------------------------------------------
# 3. Level 1 Attribute Budget (+9 net, caps) & HP Formula
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("class_name", ["Exemplar", "Fighter", "Wizard", "Rogue", "Cleric", "Monk"])
def test_level1_attributes_and_hp_raw(class_name: str):
    sheet = _generate_l1(class_name, ancestry="Human")
    attrs = sheet["attributes"]
    vals = [int(attrs[k]) for k in ("str", "dex", "con", "int", "wis", "cha")]

    assert sum(vals) == 9, f"[{class_name} L1] Attribute sum is {sum(vals)}, expected RAW +9 ({attrs})"
    assert max(vals) <= 4, f"[{class_name} L1] Attribute exceeds Level 1 cap +4 ({attrs})"
    assert min(vals) >= -1, f"[{class_name} L1] Attribute below Level 1 floor -1 ({attrs})"

    class_hp = RAW_CLASS_L1[class_name][4]
    human_hp = 8
    has_toughness = any("toughness" in (f.get("name") or "").lower() for f in (sheet.get("feats") or []))
    expected_hp = human_hp + class_hp + int(attrs["con"]) + (1 if has_toughness else 0)
    assert int(sheet["defenses"]["hp"]) == expected_hp, (
        f"[{class_name} L1] HP is {sheet['defenses']['hp']}, expected RAW {expected_hp}"
    )


# ---------------------------------------------------------------------------
# 4. Level 1 Starting Wealth Cap (15 gp = 1500 cp)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("class_name", ["Exemplar", "Fighter", "Ranger", "Cleric", "Rogue", "Wizard"])
def test_level1_starting_wealth_cap_raw(class_name: str):
    sheet = _generate_l1(class_name)
    total_cp, breakdown = _estimate_l1_wealth_cp(sheet)
    assert total_cp <= 1500, (
        f"[{class_name} L1] Starting wealth estimate is {total_cp / 100:.2f} gp "
        f"(exceeds RAW 15.00 gp cap): {', '.join(breakdown)}"
    )


# ---------------------------------------------------------------------------
# 5. Ondos Trench-Guard Regression (Azarketi Exemplar / Aiudara Seeker L1)
# ---------------------------------------------------------------------------
def test_ondos_azarketi_exemplar_raw_legality():
    sheet = _generate_l1(
        class_name="Exemplar",
        ancestry="Azarketi",
        background="Aiudara Seeker",
    )

    # 5a. Heritage must be an official Azarketi or Versatile heritage
    heritage = str(sheet.get("heritage") or "").strip().lower()
    is_official_heritage = any(
        h in heritage for h in (OFFICIAL_AZARKETI_HERITAGES | OFFICIAL_VERSATILE_HERITAGES)
    )
    assert is_official_heritage, (
        f"Azarketi received non-official/homebrew heritage: {sheet.get('heritage')!r}"
    )

    # 5b. Exemplar L1 saves & Perception: E Fort, T Ref, E Will, T Perception
    assert sheet["defenses"]["fortitude"]["rank_letter"] == "E"
    assert sheet["defenses"]["reflex"]["rank_letter"] == "T", (
        f"Exemplar L1 Reflex should be Trained (T), got {sheet['defenses']['reflex']}"
    )
    assert sheet["defenses"]["will"]["rank_letter"] == "E"
    assert sheet["perception"]["rank_letter"] == "T", (
        f"Exemplar L1 Perception should be Trained (T), got {sheet['perception']}"
    )

    # 5c. Mandatory skills: Religion (Exemplar) + Arcana & Portal Lore (Aiudara Seeker)
    trained = {
        str(s.get("name") or "").strip().lower()
        for s in (sheet.get("all_skills") or [])
        if str(s.get("rank_letter") or "U").upper() != "U"
    }
    assert "religion" in trained, "Exemplar L1 must be trained in Religion"
    assert "arcana" in trained, "Aiudara Seeker must be trained in Arcana"
    assert "portal lore" in trained, "Aiudara Seeker must be trained in Portal Lore"

    int_mod = int(sheet["attributes"]["int"])
    trained_std = [n for n in trained if "lore" not in n]
    assert len(trained_std) >= 5 + int_mod, (
        f"Exemplar + Aiudara Seeker (INT {int_mod:+d}) needs at least {5 + int_mod} trained standard skills, "
        f"got {len(trained_std)}: {sorted(trained_std)}"
    )

    # 5d. Mandatory Exemplar L1 class features (Shield Block + 3 Ikons)
    feat_names_low = {(f.get("name") or "").lower() for f in (sheet.get("feats") or [])}
    assert "shield block" in feat_names_low, (
        "Exemplar L1 must receive Shield Block as a mandatory class feature"
    )

    # 5e. No phantom melee Venomous Strike unless granted by an official feat/heritage
    strikes = (sheet.get("equipment") or {}).get("strikes") or []
    for st in strikes:
        st_name = str(st.get("name") or "").lower()
        if "venomous strike" in st_name:
            pytest.fail(
                f"Illegal/untraceable unarmed strike found on Azarketi Exemplar: {st}"
            )

    # 5f. Starting wealth <= 15 gp
    total_cp, breakdown = _estimate_l1_wealth_cp(sheet)
    assert total_cp <= 1500, (
        f"Azarketi Exemplar L1 wealth is {total_cp / 100:.2f} gp (> 15.00 gp): {', '.join(breakdown)}"
    )
