"""Single source of truth for PF2e Remaster Strike, Unarmed, Bomb, and Elemental Blast math."""

import re
from typing import Any, Dict, List, Optional, Sequence

from app.engine.models import Strike
from app.engine.progression import get_weapon_prof_bonus_delta, get_weapon_spec_bonus

STRIP_RUNE_PREFIX_RE = re.compile(
    r"^(?:\+\d+\s+)?(?:(?:Greater|Major)\s+)?(?:Striking\s+)?",
    re.IGNORECASE,
)

RANGED_WEAPON_KEYWORDS = (
    "bow", "crossbow", "sling", "blowgun", "dart", "javelin", "chakram",
    "boomerang", "shuriken", "starknife", "atlatl", "air repeater",
    "pistol", "musket", "arquebus",
)

NATURAL_STRIKE_MARKERS = (
    "unarmed", "natural", "claw", "jaws", "fang", "horn", "talon",
    "beak", "pincer", "tail", "wing", "hoof", "hooves", "thorn",
    "spines", "fist", "rage strike", "elemental blast",
)

BOMB_NAMES = ("alchemist's fire", "bottled lightning", "acid flask", "frost vial")


def normalize_attr_mods(attrs: Optional[Dict[str, Any]]) -> Dict[str, int]:
    """Normalizes full or short attribute dictionaries to short lowercase keys."""
    raw = attrs or {}
    pairs = (
        ("strength", "str"),
        ("dexterity", "dex"),
        ("constitution", "con"),
        ("intelligence", "int"),
        ("wisdom", "wis"),
        ("charisma", "cha"),
    )
    out: Dict[str, int] = {}
    for full_k, short_k in pairs:
        val = raw[full_k] if full_k in raw else raw.get(short_k, 0)
        try:
            out[short_k] = int(val or 0)
        except (ValueError, TypeError):
            out[short_k] = 0
    return out


def get_fundamental_strike_tiers(level: int) -> Dict[str, Any]:
    """Returns PF2e Remaster weapon/handwrap potency and striking rune tiers for a level."""
    lvl = max(1, min(20, int(level)))
    potency = 3 if lvl >= 16 else (2 if lvl >= 10 else (1 if lvl >= 2 else 0))
    if lvl >= 19:
        striking_label, dice_count = "Major Striking", 4
    elif lvl >= 12:
        striking_label, dice_count = "Greater Striking", 3
    elif lvl >= 4:
        striking_label, dice_count = "Striking", 2
    else:
        striking_label, dice_count = "", 1
    return {
        "potency": potency,
        "striking_label": striking_label,
        "dice_count": dice_count,
    }


def format_runed_strike_name(base_name: str, level: int, *, apply_prefix: bool = True) -> str:
    """Formats a weapon name with fundamental potency and striking rune prefixes."""
    clean = STRIP_RUNE_PREFIX_RE.sub("", (base_name or "").strip()).strip()
    if not apply_prefix:
        return clean
    tiers = get_fundamental_strike_tiers(level)
    parts: List[str] = []
    if tiers["potency"]:
        parts.append(f"+{tiers['potency']}")
    if tiers["striking_label"]:
        parts.append(tiers["striking_label"])
    parts.append(clean)
    return " ".join(parts)


def is_ranged_strike(name: str, traits: Sequence[str], weapon_entry: Optional[Dict[str, Any]] = None) -> bool:
    """Determines whether a weapon or strike entry is ranged."""
    clean_low = STRIP_RUNE_PREFIX_RE.sub("", (name or "").strip()).lower()
    t_low = [str(t).lower() for t in (traits or [])]
    if any(t.startswith(("range", "ranged", "volley", "reload")) for t in t_low):
        return True
    if any(k in clean_low for k in RANGED_WEAPON_KEYWORDS):
        return True
    if isinstance(weapon_entry, dict):
        rng = weapon_entry.get("range")
        if (isinstance(rng, (int, float)) and rng > 0) or (
            isinstance(rng, str) and rng.strip() and rng.strip() not in ("—", "-", "0")
        ):
            return True
        eq_t = [str(t).lower() for t in (weapon_entry.get("traits") or [])]
        if any(t.startswith(("range", "ranged", "volley", "reload")) for t in eq_t):
            return True
    return False


def is_natural_or_unarmed_strike(name: str, traits: Sequence[str]) -> bool:
    """Returns True for unarmed/natural strikes, stances, rage strikes, or blasts."""
    n_low = (name or "").strip().lower()
    t_low = " ".join(str(t).lower() for t in (traits or []))
    return any(m in n_low or m in t_low for m in NATURAL_STRIKE_MARKERS)


def _scale_dice_expression(base_dice: str, dice_count: int) -> str:
    m = re.match(r"^(\d+)(d\d+)", (base_dice or "1d6").strip())
    if m:
        base_n = int(m.group(1))
        die = m.group(2)
        scaled_n = dice_count if base_n == 1 else max(base_n, dice_count)
        return f"{scaled_n}{die}"
    return "1d6"



_TRAIT_EXACT_MAP = {
    "agile": "Agile",
    "finesse": "Finesse",
    "disarm": "Disarm",
    "trip": "Trip",
    "grapple": "Grapple",
    "shove": "Shove",
    "parry": "Parry",
    "reach": "Reach",
    "sweep": "Sweep",
    "forceful": "Forceful",
    "propulsive": "Propulsive",
    "jousting": "Jousting",
    "backstabber": "Backstabber",
    "unarmed": "Unarmed",
    "brawling": "Brawling",
    "monk": "Monk",
    "deadly": "Deadly",
    "fatal": "Fatal",
    "thrown": "Thrown",
    "versatile": "Versatile",
}


def _normalize_weapon_trait(raw_trait: Any) -> str:
    s = str(raw_trait or "").strip()
    if not s:
        return ""
    if ":" in s or "(" in s:
        return s

    m_deadly = re.match(r"^deadly[\s\-]+d?(\d+)$", s, flags=re.IGNORECASE)
    if m_deadly:
        return f"Deadly d{m_deadly.group(1)}"

    m_fatal = re.match(r"^fatal[\s\-]+d?(\d+)$", s, flags=re.IGNORECASE)
    if m_fatal:
        return f"Fatal d{m_fatal.group(1)}"

    m_two_hand = re.match(r"^two[\s\-]+hand[\s\-]+d?(\d+)$", s, flags=re.IGNORECASE)
    if m_two_hand:
        return f"Two-Hand d{m_two_hand.group(1)}"

    m_thrown = re.match(r"^thrown[\s\-]+(\d+)(?:\s*(?:ft|feet))?$", s, flags=re.IGNORECASE)
    if m_thrown:
        return f"Thrown {m_thrown.group(1)} ft"

    m_range = re.match(r"^range[\s\-]+(\d+)(?:\s*(?:ft|feet))?$", s, flags=re.IGNORECASE)
    if m_range:
        return f"Range {m_range.group(1)} ft"

    m_volley = re.match(r"^volley[\s\-]+(\d+)(?:\s*(?:ft|feet))?$", s, flags=re.IGNORECASE)
    if m_volley:
        return f"Volley {m_volley.group(1)} ft"

    m_versatile = re.match(r"^versatile[\s\-]+([bps])$", s, flags=re.IGNORECASE)
    if m_versatile:
        return f"Versatile {m_versatile.group(1).upper()}"

    low = re.sub(r"\s+", " ", s.lower()).strip()
    if low in _TRAIT_EXACT_MAP:
        return _TRAIT_EXACT_MAP[low]

    return s


def _normalize_weapon_traits(traits: Sequence[Any]) -> List[str]:
    out: List[str] = []
    seen: set[str] = set()
    for t in (traits or []):
        norm = _normalize_weapon_trait(t)
        if norm and norm.lower() not in seen:
            seen.add(norm.lower())
            out.append(norm)
    return out


def compute_strike(
    *,
    name: str,
    base_dice: str,
    damage_type: str,
    traits: Sequence[str],
    level: int,
    class_name: str,
    attrs: Dict[str, Any],
    is_unarmed: Optional[bool] = None,
    is_ranged: Optional[bool] = None,
    apply_runes: bool = True,
    weapon_entry: Optional[Dict[str, Any]] = None,
    sneak_attack_dice: Optional[str] = None,
    rage_bonus: Optional[int] = None,
    extra_note: Optional[str] = None,
) -> Strike:
    """
    Pure PF2e Remaster Strike calculation.
    Applies exact weapon proficiency, attribute modifier, fundamental runes (or Handwraps
    for unarmed attacks), MAP (-4/-8 agile or -5/-10), and Weapon Specialization.
    """
    lvl = max(1, min(20, int(level)))
    mods = normalize_attr_mods(attrs)
    trait_list = [str(t) for t in (traits or []) if t]
    traits_low = [t.lower() for t in trait_list]
    unarmed = is_natural_or_unarmed_strike(name, trait_list) if is_unarmed is None else is_unarmed
    ranged = is_ranged_strike(name, trait_list, weapon_entry=weapon_entry) if is_ranged is None else is_ranged

    tiers = get_fundamental_strike_tiers(lvl) if apply_runes else {"potency": 0, "striking_label": "", "dice_count": 1}
    potency = tiers["potency"]
    dice_count = tiers["dice_count"]

    prof_bonus = 2 + get_weapon_prof_bonus_delta(class_name, lvl)
    is_finesse = "finesse" in traits_low
    is_agile = "agile" in traits_low
    is_thrown = any(t.startswith("thrown") for t in traits_low)
    is_propulsive = any(t.startswith("propulsive") for t in traits_low)

    if ranged:
        atk_stat = mods["dex"]
    elif is_finesse:
        atk_stat = max(mods["str"], mods["dex"])
    else:
        atk_stat = mods["str"]

    atk_total = lvl + prof_bonus + atk_stat + potency
    map_step = 4 if is_agile else 5
    map2 = atk_total - map_step
    map3 = atk_total - (2 * map_step)

    if ranged and not is_thrown:
        if is_propulsive:
            stat_dmg = mods["str"] // 2 if mods["str"] >= 0 else mods["str"]
        else:
            stat_dmg = 0
    else:
        stat_dmg = mods["str"]

    spec_bonus = get_weapon_spec_bonus(class_name, lvl)
    total_flat = stat_dmg + spec_bonus
    scaled_dice = _scale_dice_expression(base_dice, dice_count)
    dmg_core = f"{scaled_dice}{total_flat:+d}" if total_flat != 0 else scaled_dice

    dmg_dice_str = dmg_core
    if sneak_attack_dice:
        dmg_dice_str = f"{dmg_dice_str} (+{sneak_attack_dice} precision vs off-guard)"

    dmg_summary = dmg_dice_str
    if rage_bonus:
        dmg_summary = f"{dmg_core} (+{rage_bonus} Rage)"
    if extra_note:
        dmg_summary = f"{dmg_summary} ({extra_note})"

    display_name = format_runed_strike_name(name, lvl, apply_prefix=(apply_runes and not unarmed))

    return Strike(
        name=display_name,
        attack_bonus=f"{atk_total:+d}",
        map_second=f"{map2:+d}",
        map_third=f"{map3:+d}",
        damage=dmg_summary,
        damage_dice=dmg_dice_str,
        damage_type=damage_type or "Slashing",
        traits=_normalize_weapon_traits(trait_list),
    )


def compute_kineticist_blasts(level: int, attrs: Dict[str, Any]) -> List[Strike]:
    """Computes PF2e Remaster Kineticist Melee & Ranged Elemental Blasts."""
    lvl = max(1, min(20, int(level)))
    mods = normalize_attr_mods(attrs)
    imp_prof = 8 if lvl >= 19 else (6 if lvl >= 15 else (4 if lvl >= 7 else 2))
    gate_attenuator = 3 if lvl >= 17 else (2 if lvl >= 11 else (1 if lvl >= 3 else 0))
    atk_bonus = lvl + imp_prof + mods["con"] + gate_attenuator

    dice_count = 1 + (lvl - 1) // 4
    melee_flat = mods["con"] + max(0, mods["str"])
    ranged_flat = mods["con"]

    melee_dmg = f"{dice_count}d8{melee_flat:+d}" if melee_flat != 0 else f"{dice_count}d8"
    ranged_dmg = f"{dice_count}d6{ranged_flat:+d}" if ranged_flat != 0 else f"{dice_count}d6"

    return [
        Strike(
            name="Elemental Blast (Melee)",
            attack_bonus=f"{atk_bonus:+d}",
            map_second=f"{atk_bonus - 5:+d}",
            map_third=f"{atk_bonus - 10:+d}",
            damage=melee_dmg,
            damage_dice=melee_dmg,
            damage_type="Bludgeoning / Piercing / Slashing",
            traits=["Impulse", "Kinetic", "Magical", "Primal"],
        ),
        Strike(
            name="Elemental Blast (Ranged)",
            attack_bonus=f"{atk_bonus:+d}",
            map_second=f"{atk_bonus - 5:+d}",
            map_third=f"{atk_bonus - 10:+d}",
            damage=ranged_dmg,
            damage_dice=ranged_dmg,
            damage_type="Bludgeoning / Piercing / Slashing (60 ft)",
            traits=["Impulse", "Infusion", "Kinetic", "Magical", "Primal"],
        ),
    ]


def compute_alchemical_bomb_strike(
    bomb_spec: Dict[str, Any],
    level: int,
    class_name: str,
    attrs: Dict[str, Any],
) -> Strike:
    """Computes an Alchemical Bomb Strike using exact weapon proficiency + DEX + item bonus."""
    lvl = max(1, min(20, int(level)))
    mods = normalize_attr_mods(attrs)
    prof_bonus = 2 + get_weapon_prof_bonus_delta(class_name, lvl)
    item_bonus = int(bomb_spec.get("item_bonus") or 0)
    atk_bonus = lvl + prof_bonus + mods["dex"] + item_bonus
    dmg_desc = f"{bomb_spec['dice']} + {bomb_spec['persistent']} + {bomb_spec['splash']}"
    return Strike(
        name=bomb_spec["name"],
        attack_bonus=f"{atk_bonus:+d}",
        map_second=f"{atk_bonus - 5:+d}",
        map_third=f"{atk_bonus - 10:+d}",
        damage=dmg_desc,
        damage_dice=dmg_desc,
        damage_type=bomb_spec["type"],
        traits=list(bomb_spec.get("traits") or []),
    )


def dedupe_and_recompute_strikes(
    strikes: Sequence[Any],
    *,
    level: int,
    class_name: str,
    attrs: Dict[str, Any],
    weapon_lookup: Optional[Dict[str, Dict[str, Any]]] = None,
    sneak_attack_dice: Optional[str] = None,
) -> List[Strike]:
    """
    Deduplicates strikes (including Horn vs Horns) and recomputes every non-blast,
    non-bomb, non-rage strike through compute_strike() as a single final pass.
    """
    mods = normalize_attr_mods(attrs)
    w_lookup = weapon_lookup or {}

    deduped: List[Strike] = []
    seen_keys: Dict[str, int] = {}

    for raw_st in (strikes or []):
        st_dict = raw_st if isinstance(raw_st, dict) else raw_st.model_dump()
        raw_name = str(st_dict.get("name") or "").strip()
        if not raw_name:
            continue
        low_name = raw_name.lower()

        if low_name.startswith("elemental blast"):
            continue
        if any(b in low_name for b in BOMB_NAMES):
            # Recompute bomb cleanly if needed
            item_bonus = 3 if "(major)" in low_name else (2 if "(greater)" in low_name else (1 if "(moderate)" in low_name else 0))
            prof_bonus = 2 + get_weapon_prof_bonus_delta(class_name, level)
            atk = level + prof_bonus + mods["dex"] + item_bonus
            rebuilt_bomb = Strike(
                name=raw_name,
                attack_bonus=f"{atk:+d}",
                map_second=f"{atk - 5:+d}",
                map_third=f"{atk - 10:+d}",
                damage=str(st_dict.get("damage") or st_dict.get("damage_dice") or "1d8"),
                damage_dice=str(st_dict.get("damage_dice") or "1d8"),
                damage_type=str(st_dict.get("damage_type") or "Fire"),
                traits=_normalize_weapon_traits(st_dict.get("traits") or []),
            )
            key = low_name
            if key not in seen_keys:
                seen_keys[key] = len(deduped)
                deduped.append(rebuilt_bomb)
            continue

        clean_base = STRIP_RUNE_PREFIX_RE.sub("", raw_name).strip()
        base_key = clean_base.lower()
        # Unify singular/plural "horn" vs "horns"
        canonical_key = "horns" if base_key in ("horn", "horns") else base_key

        traits = list(st_dict.get("traits") or [])
        raw_dmg_dice = str(st_dict.get("damage_dice") or "1d6").strip()
        m_d = re.match(r"^(\d+)(d\d+)", raw_dmg_dice)
        if m_d:
            # If the name has a Striking prefix, strip scaled dice back to 1dX before rescaling
            has_striking_prefix = bool(re.search(r"\b(?:greater\s+|major\s+)?striking\b", low_name))
            base_dice = f"1{m_d.group(2)}" if has_striking_prefix else f"{m_d.group(1)}{m_d.group(2)}"
        else:
            base_dice = "1d6"
        w_entry = w_lookup.get(base_key)
        if w_entry and isinstance(w_entry.get("damage"), dict):
            d_obj = w_entry["damage"]
            d_num = d_obj.get("dice") or 1
            d_die = str(d_obj.get("die") or "d6")
            if not d_die.startswith("d"):
                d_die = f"d{d_die}"
            base_dice = f"{d_num}{d_die}"

        is_rage = "(rage strike)" in low_name
        rage_bonus = (2 if level < 7 else 6) if is_rage else None

        computed = compute_strike(
            name=clean_base,
            base_dice=base_dice,
            damage_type=str(st_dict.get("damage_type") or "Slashing"),
            traits=traits,
            level=level,
            class_name=class_name,
            attrs=mods,
            is_unarmed=is_natural_or_unarmed_strike(clean_base, traits),
            apply_runes=(not is_rage),
            weapon_entry=w_entry,
            sneak_attack_dice=sneak_attack_dice,
            rage_bonus=rage_bonus,
        )

        if canonical_key not in seen_keys:
            seen_keys[canonical_key] = len(deduped)
            deduped.append(computed)
        else:
            # Prefer plural "Horns" or entry with richer traits
            prev = deduped[seen_keys[canonical_key]]
            if base_key == "horns" or len(computed.traits or []) > len(prev.traits or []):
                deduped[seen_keys[canonical_key]] = computed

    if class_name.strip().lower() == "kineticist":
        blasts = compute_kineticist_blasts(level, mods)
        deduped = blasts + deduped

    return deduped
