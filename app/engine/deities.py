from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional


_REPO_ROOT = Path(__file__).resolve().parents[2]
_DEITIES_DIR = _REPO_ROOT / "source_data" / "packs" / "pf2e" / "deities"
_DOMAINS_JOURNAL = _REPO_ROOT / "source_data" / "packs" / "pf2e" / "journals" / "domains.json"
_FOCUS_SPELLS_DIR = _REPO_ROOT / "source_data" / "packs" / "pf2e" / "spells" / "focus"


def _strip_markup(raw: str) -> str:
    if not raw:
        return ""
    text = re.sub(r"@UUID\[[^\]]*\.Item\.([^\]]+)\](?:\{([^}]+)\})?", lambda m: m.group(2) or m.group(1), raw)
    text = re.sub(r"@(?:Check|Damage|Template|Actor)\[[^\]]*\](?:\{([^}]+)\})?", lambda m: m.group(1) or "", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _slug_to_title(slug: str) -> str:
    cleaned = slug.replace("-", " ").replace("_", " ").strip()
    return " ".join(w.capitalize() if w.lower() not in {"of", "the", "and", "in", "to"} else w.lower() for w in cleaned.split()) or cleaned


def _load_focus_spell_index() -> Dict[str, Dict[str, Any]]:
    index: Dict[str, Dict[str, Any]] = {}
    if not _FOCUS_SPELLS_DIR.exists():
        return index
    for fp in _FOCUS_SPELLS_DIR.glob("*.json"):
        try:
            data = json.loads(fp.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(data, dict):
            continue
        name = str(data.get("name") or "").strip()
        if not name:
            continue
        sys_d = data.get("system") if isinstance(data.get("system"), dict) else {}
        rank_val = sys_d.get("level", {}).get("value") if isinstance(sys_d.get("level"), dict) else 1
        time_val = sys_d.get("time", {}).get("value") if isinstance(sys_d.get("time"), dict) else ""
        desc_val = _strip_markup(str(sys_d.get("description", {}).get("value") or ""))
        entry = {
            "name": name,
            "rank": int(rank_val) if isinstance(rank_val, (int, float)) else 1,
            "casting_time": str(time_val or ""),
            "description": desc_val,
        }
        index[name.lower()] = entry
        index[fp.stem.lower()] = entry
    return index


def _parse_domain_spells(focus_index: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    domains_map: Dict[str, Dict[str, Any]] = {}
    if not _DOMAINS_JOURNAL.exists():
        return domains_map
    try:
        journal = json.loads(_DOMAINS_JOURNAL.read_text(encoding="utf-8"))
    except Exception:
        return domains_map

    pages = journal.get("pages") if isinstance(journal, dict) else []
    if not isinstance(pages, list):
        return domains_map

    for page in pages:
        if not isinstance(page, dict):
            continue
        raw_name = str(page.get("name") or "").strip()
        if not raw_name or raw_name.lower() == "domains":
            continue
        domain_name = re.sub(r"\s+Domain$", "", raw_name, flags=re.IGNORECASE).strip().title()
        html = str((page.get("text") or {}).get("content") or "")
        summary_match = re.search(r"<p>(.*?)</p>", html, flags=re.DOTALL)
        summary = _strip_markup(summary_match.group(1)) if summary_match else ""

        def _extract_spell(label_pattern: str) -> Optional[Dict[str, Any]]:
            m = re.search(
                rf"{label_pattern}.*?@UUID\[[^\]]*\.Item\.([^\]]+)\](?:\{{([^}}]+)\}})?",
                html,
                flags=re.IGNORECASE | re.DOTALL,
            )
            if not m:
                return None
            spell_name = (m.group(2) or m.group(1) or "").strip()
            matched = focus_index.get(spell_name.lower())
            if matched:
                return dict(matched)
            return {
                "name": spell_name,
                "rank": 1,
                "casting_time": "",
                "description": "",
            }

        initial_spell = _extract_spell(r"<strong>\s*Domain Spell\s*</strong>")
        advanced_spell = _extract_spell(r"<strong>\s*Advanced Domain Spell\s*</strong>")

        domains_map[domain_name.lower()] = {
            "name": domain_name,
            "summary": summary,
            "domain_spell": initial_spell,
            "advanced_domain_spell": advanced_spell,
        }

    return domains_map


def _load_deities() -> Dict[str, Dict[str, Any]]:
    deities_by_key: Dict[str, Dict[str, Any]] = {}
    if not _DEITIES_DIR.exists():
        return deities_by_key

    for fp in sorted(_DEITIES_DIR.rglob("*.json")):
        if fp.name.startswith("_"):
            continue
        try:
            raw = json.loads(fp.read_text(encoding="utf-8"))
        except Exception:
            continue
        items = raw if isinstance(raw, list) else [raw]
        for item in items:
            if not isinstance(item, dict) or item.get("type") != "deity":
                continue
            name = str(item.get("name") or "").strip()
            if not name:
                continue
            sys_d = item.get("system") if isinstance(item.get("system"), dict) else {}

            raw_attrs = sys_d.get("attribute")
            attrs = [str(a).strip().upper() for a in raw_attrs if a] if isinstance(raw_attrs, list) else []

            raw_sanct = sys_d.get("sanctification") if isinstance(sys_d.get("sanctification"), dict) else {}
            sanct_modal = str(raw_sanct.get("modal") or "").strip().lower()
            sanct_what = [str(w).strip().capitalize() for w in (raw_sanct.get("what") or []) if w]

            raw_doms = sys_d.get("domains") if isinstance(sys_d.get("domains"), dict) else {}
            primary_doms = [str(d).strip().title() for d in (raw_doms.get("primary") or []) if d]
            alt_doms = [str(d).strip().title() for d in (raw_doms.get("alternate") or []) if d]

            raw_font = [str(f).strip().capitalize() for f in (sys_d.get("font") or []) if f]
            raw_weapons = [_slug_to_title(str(w)) for w in (sys_d.get("weapons") or []) if w]
            raw_skills = [str(s).strip().title() for s in (sys_d.get("skill") or []) if s]

            raw_spells = sys_d.get("spells") if isinstance(sys_d.get("spells"), dict) else {}
            deity_spells: Dict[str, str] = {}
            for rank_k, spell_ref in raw_spells.items():
                cleaned_spell = _strip_markup(str(spell_ref or "")).split(".")[-1]
                if cleaned_spell:
                    deity_spells[str(rank_k)] = cleaned_spell

            cat_val = ""
            if isinstance(sys_d.get("category"), dict):
                cat_val = str(sys_d["category"].get("value") or "").strip()
            elif isinstance(sys_d.get("category"), str):
                cat_val = sys_d["category"].strip()

            entry = {
                "name": name,
                "category": cat_val or fp.parent.name.replace("-", " ").title(),
                "description": _strip_markup(str((sys_d.get("description") or {}).get("value") or "")),
                "attributes": attrs,
                "sanctification": {
                    "modal": sanct_modal,
                    "what": sanct_what,
                },
                "domains": {
                    "primary": primary_doms,
                    "alternate": alt_doms,
                },
                "font": raw_font,
                "favored_weapon": raw_weapons[0] if raw_weapons else None,
                "weapons": raw_weapons,
                "skill": raw_skills[0] if raw_skills else None,
                "skills": raw_skills,
                "spells": deity_spells,
            }
            deities_by_key[name.lower()] = entry

    return deities_by_key


_BUNDLED_DEITIES_DOMAINS = _REPO_ROOT / "data" / "deities_domains.json"
_FOCUS_INDEX: Dict[str, Dict[str, Any]] = _load_focus_spell_index()
_DOMAIN_SPELLS: Dict[str, Dict[str, Any]] = _parse_domain_spells(_FOCUS_INDEX)
_DEITIES: Dict[str, Dict[str, Any]] = _load_deities()

if (not _DEITIES or not _DOMAIN_SPELLS) and _BUNDLED_DEITIES_DOMAINS.exists():
    try:
        _bundled_raw = json.loads(_BUNDLED_DEITIES_DOMAINS.read_text(encoding="utf-8"))
        if not _DEITIES and isinstance(_bundled_raw.get("deities"), dict):
            _DEITIES = _bundled_raw["deities"]
        if not _DOMAIN_SPELLS and isinstance(_bundled_raw.get("domain_spells"), dict):
            _DOMAIN_SPELLS = _bundled_raw["domain_spells"]
    except Exception:
        pass


def get_all_deities() -> List[Dict[str, Any]]:
    return [_DEITIES[k] for k in sorted(_DEITIES.keys())]


def list_deity_names() -> List[str]:
    return [d["name"] for d in get_all_deities()]


def get_deity(name: Optional[str]) -> Optional[Dict[str, Any]]:
    if not name:
        return None
    key = name.strip().lower()
    if key in _DEITIES:
        return _DEITIES[key]
    for k, v in _DEITIES.items():
        if key in k or k in key:
            return v
    return None


def get_deity_domains(deity_name: Optional[str], include_alternate: bool = True) -> List[str]:
    deity = get_deity(deity_name)
    if not deity:
        return []
    doms = list(deity.get("domains", {}).get("primary") or [])
    if include_alternate:
        for alt in deity.get("domains", {}).get("alternate") or []:
            if alt not in doms:
                doms.append(alt)
    return doms


def get_domain_info(domain_name: str) -> Dict[str, Any]:
    clean = re.sub(r"\s+Domain$", "", domain_name.strip(), flags=re.IGNORECASE).strip()
    found = _DOMAIN_SPELLS.get(clean.lower())
    if found:
        return dict(found)
    return {
        "name": clean.title(),
        "summary": "",
        "domain_spell": None,
        "advanced_domain_spell": None,
    }


def list_all_domains() -> List[str]:
    names = {v["name"] for v in _DOMAIN_SPELLS.values() if v.get("name")}
    for d in _DEITIES.values():
        for dom in (d.get("domains", {}).get("primary") or []) + (d.get("domains", {}).get("alternate") or []):
            if dom:
                names.add(dom)
    return sorted(names)


import random


_ANCESTRY_DEITY_HINTS: Dict[str, List[str]] = {
    "dwarf": ["torag", "angradd", "folgrit", "grundinnar", "kols", "trudd"],
    "elf": ["findeladlara", "ketephys", "yuelral", "desna", "calistria"],
    "gnome": ["nivi rhombodazzle", "shelyn", "desna", "barbatos"],
    "goblin": ["zogmugot", "zarongel", "venkelvore", "hadregash"],
    "halfling": ["chaldira", "thamir", "desna", "abadar"],
    "orc": ["gorum", "dretha", "lanishra", "nulgreth", "rull", "sezelrian", "varg"],
    "kitsune": ["daikitsu", "shizuru", "tsukiyo", "lady nanbyo"],
    "tengu": ["hei feng", "shizuru", "desna"],
    "leshy": ["gozreh", "erastil", "desna"],
    "ratfolk": ["shyka", "abadar", "calistria"],
    "kobold": ["aupmahoz", "draconic", "asmodeus"],
    "fetchling": ["zon-kuthon", "desna", "shyka"],
    "iruxi": ["angradd", "gozreh", "pharasma"],
}

_CLASS_DOMAIN_HINTS: Dict[str, List[str]] = {
    "cleric": ["healing", "protection", "zeal", "sun", "knowledge", "family", "duty"],
    "champion": ["protection", "zeal", "might", "duty", "freedom", "redemption", "sun"],
    "druid": ["nature", "earth", "air", "water", "fire", "plant", "wood", "lightning", "moon"],
    "animist": ["nature", "soul", "repose", "earth", "water", "air", "fire", "moon"],
    "ranger": ["nature", "hunt", "travel", "air", "earth", "moon", "wood"],
    "barbarian": ["might", "zeal", "destruction", "earth", "fire", "lightning", "rage"],
    "fighter": ["might", "zeal", "duty", "protection", "air"],
    "commander": ["duty", "might", "protection", "zeal", "truth"],
    "rogue": ["trickery", "luck", "secrecy", "moon", "shadow", "freedom"],
    "bard": ["charm", "luck", "moon", "travel", "dreams", "creation", "perfection"],
    "wizard": ["knowledge", "magic", "arcane", "time", "fate", "secrecy"],
    "witch": ["secrecy", "moon", "fate", "soul", "nature", "nightmares", "repose"],
    "sorcerer": ["magic", "fate", "moon", "fire", "air", "earth", "water", "soul"],
    "psychic": ["dreams", "knowledge", "mind", "nightmares", "fate", "star"],
    "oracle": ["fate", "time", "soul", "sun", "moon", "repose", "death"],
    "thaumaturge": ["secrecy", "knowledge", "soul", "luck", "protection"],
    "investigator": ["knowledge", "truth", "secrecy", "luck", "fate"],
    "monk": ["perfection", "air", "earth", "fire", "water", "truth", "duty"],
    "swashbuckler": ["freedom", "luck", "charm", "air", "travel"],
    "alchemist": ["creation", "knowledge", "earth", "fire", "nature"],
    "inventor": ["creation", "knowledge", "earth", "fire", "truth"],
    "magus": ["knowledge", "might", "magic", "zeal", "lightning"],
    "summoner": ["soul", "creation", "nature", "fate", "moon"],
    "kineticist": ["earth", "air", "water", "fire", "wood", "metal", "nature"],
    "gunslinger": ["luck", "freedom", "travel", "fire", "air"],
    "exemplar": ["might", "zeal", "sun", "moon", "freedom", "protection"],
}


def select_deity(
    deity_name: Optional[str] = None,
    class_name: Optional[str] = None,
    background_name: Optional[str] = None,
    ancestry_name: Optional[str] = None,
    subclass_name: Optional[str] = None,
    domain_name: Optional[str] = None,
    concept_text: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    if deity_name and deity_name.strip().lower() not in ("", "any", "any deity", "none"):
        explicit = get_deity(deity_name)
        if explicit:
            return explicit

    all_deities = get_all_deities()
    if not all_deities:
        return None

    clean_domain = ""
    if domain_name and domain_name.strip().lower() not in ("", "any", "any domain", "none"):
        clean_domain = re.sub(r"\s*\(alternate\)$", "", domain_name.strip(), flags=re.IGNORECASE).strip().lower()

    cls_low = (class_name or "").strip().lower()
    sub_low = (subclass_name or "").strip().lower()
    bg_low = (background_name or "").strip().lower()
    anc_low = (ancestry_name or "").strip().lower()
    concept_low = (concept_text or "").strip().lower()

    domain_hints = set(_CLASS_DOMAIN_HINTS.get(cls_low, []))
    for kw, doms in (
        ("nature", ["nature", "earth", "water", "air", "fire", "plant", "wood"]),
        ("fire", ["fire", "sun", "lightning"]),
        ("water", ["water", "travel", "moon"]),
        ("earth", ["earth", "metal", "protection"]),
        ("air", ["air", "travel", "lightning"]),
        ("wood", ["wood", "plant", "nature"]),
        ("metal", ["metal", "earth", "creation"]),
        ("enigma", ["knowledge", "secrecy", "fate"]),
        ("shadow", ["shadow", "nightmares", "moon", "secrecy"]),
        ("death", ["death", "repose", "undeath", "soul"]),
        ("war", ["might", "zeal", "duty", "protection"]),
        ("trick", ["trickery", "luck", "freedom"]),
        ("dream", ["dreams", "moon", "nightmares"]),
        ("star", ["star", "travel", "fate", "moon"]),
        ("undead", ["death", "undeath", "repose"]),
    ):
        if kw in sub_low or kw in concept_low or kw in bg_low:
            domain_hints.update(doms)

    anc_hints = set(_ANCESTRY_DEITY_HINTS.get(anc_low, []))

    scored: List[tuple[float, Dict[str, Any]]] = []
    for d in all_deities:
        d_name_low = str(d.get("name") or "").lower()
        dom_block = d.get("domains") if isinstance(d.get("domains"), dict) else {}
        prim_low = {str(x).lower() for x in (dom_block.get("primary") or []) if x}
        alt_low = {str(x).lower() for x in (dom_block.get("alternate") or []) if x}
        all_d_doms = prim_low | alt_low

        score = 1.0

        # Selected domain is a primary driver when specified
        if clean_domain:
            if clean_domain in prim_low:
                score += 120.0
            elif clean_domain in alt_low:
                score += 85.0
            else:
                score -= 40.0

        # Ancestry deity & pantheon affinity
        if d_name_low in anc_hints:
            score += 18.0
        elif anc_low and any(tok in d_name_low for tok in anc_low.split()):
            score += 6.0

        # Class & subclass domain alignment
        if domain_hints:
            prim_matches = len(prim_low & domain_hints)
            alt_matches = len(alt_low & domain_hints)
            score += prim_matches * 7.0 + alt_matches * 3.5

        # Favored weapon alignment with concept text (handles "great axe" -> "greataxe")
        fav_wep = str(d.get("favored_weapon") or "").strip().lower()
        if fav_wep and concept_low:
            norm_concept = re.sub(r"[\s\-]+", "", concept_low)
            norm_wep = re.sub(r"[\s\-]+", "", fav_wep)
            if fav_wep in concept_low or (len(norm_wep) >= 4 and norm_wep in norm_concept):
                score += 65.0

        # Background / concept keyword overlap with deity name, skills, or description
        desc_low = str(d.get("description") or "").lower()
        skills_low = {str(s).lower() for s in (d.get("skills") or []) if s}
        for token in set(f"{bg_low} {sub_low} {concept_low}".split()):
            if len(token) < 4 or token in {"with", "from", "into", "that", "this", "your", "have"}:
                continue
            if token in skills_low:
                score += 6.0
            if token in d_name_low:
                score += 8.0
            elif token in desc_low:
                score += 1.5

        scored.append((max(0.1, score), d))

    scored.sort(key=lambda pair: pair[0], reverse=True)
    top_score = scored[0][0]

    # Pick among top-tier candidates so results feel varied yet well-matched
    if clean_domain:
        candidates = [(sc, item) for sc, item in scored if sc >= top_score - 15.0][:8]
    else:
        candidates = [(sc, item) for sc, item in scored if sc >= top_score - 8.0][:10]

    if not candidates:
        return scored[0][1]

    weights = [sc for sc, _ in candidates]
    chosen = random.choices([item for _, item in candidates], weights=weights, k=1)[0]
    return chosen
