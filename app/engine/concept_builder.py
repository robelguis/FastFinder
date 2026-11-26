import os
import re
import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

try:
    from google import genai
    from google.genai import types
except Exception:
    genai = None
    types = None

try:
    from app.engine.archetypes import ARCHETYPE_DATA
except Exception:
    ARCHETYPE_DATA = {}

try:
    from app.engine.spells import SPELL_CATALOG
except Exception:
    SPELL_CATALOG = {}


NATIVE_COMPANION_CLASSES = {"summoner", "witch", "ranger", "druid", "champion", "inventor"}
COMPANION_ARCHETYPES = {
    "beastmaster",
    "familiar master",
    "clockwork reanimator",
    "cavalier",
    "mammoth lord",
    "undead master",
}

SKILL_NAMES = [
    "acrobatics", "arcana", "athletics", "crafting", "deception",
    "diplomacy", "intimidation", "medicine", "nature", "occultism",
    "performance", "religion", "society", "stealth", "survival", "thievery",
]

# --- Druid order detection (deterministic, does not depend on Gemini) ---
DRUID_ORDERS = ("animal", "leaf", "wild", "storm", "untamed")

# If subclasses.py expects "Animal Order" instead of "Animal", set this to " Order".
DRUID_ORDER_SUFFIX = ""


def detect_druid_order(text_lower: str) -> Optional[str]:
    for o in DRUID_ORDERS:
        if re.search(rf"\b{o}\s+order\b|\border\s+of\s+the\s+{o}\b|\b{o}\s+druid\b", text_lower):
            return o.capitalize() + DRUID_ORDER_SUFFIX
    return None


@dataclass
class LevelRequirement:
    reason: str
    min_level: int


@dataclass
class ConceptSpec:
    raw_text: str
    char_name: Optional[str] = None
    ancestry: Optional[str] = None
    heritage: Optional[str] = None
    background: Optional[str] = None
    character_class: Optional[str] = None
    subclass: Optional[str] = None
    archetype: Optional[str] = None
    explicit_level: Optional[int] = None
    requested_feats: List[str] = field(default_factory=list)
    requested_spells: List[str] = field(default_factory=list)
    requested_skills: Dict[str, str] = field(default_factory=dict)  # skill -> rank ("T","E","M","L")
    wants_companion: bool = False
    companion_kind: Optional[str] = None
    wants_secondary_pet: bool = False
    requirements: List[LevelRequirement] = field(default_factory=list)


class ConceptToSheetBuilder:
    """
    Parses natural-language character concepts (via Gemini + deterministic PF2e
    catalog extraction) and computes the lowest legal PF2e Remaster level that
    satisfies every requirement in the prompt.
    """

    def __init__(self, generator: Any):
        self.generator = generator
        self._build_lookup_indexes()

    def _build_lookup_indexes(self) -> None:
        self.ancestry_map: Dict[str, str] = {}
        raw_anc = self.generator.ancestries
        items_anc = raw_anc.values() if isinstance(raw_anc, dict) else raw_anc
        for a in items_anc:
            name = a["name"] if isinstance(a, dict) else str(a)
            self.ancestry_map[name.lower()] = name

        self.class_map: Dict[str, str] = {}
        raw_cls = self.generator.classes
        items_cls = raw_cls.values() if isinstance(raw_cls, dict) else raw_cls
        for c in items_cls:
            name = c["name"] if isinstance(c, dict) else str(c)
            self.class_map[name.lower()] = name

        self.background_map: Dict[str, str] = {}
        raw_bg = getattr(self.generator, "backgrounds", {}) or {}
        items_bg = raw_bg.values() if isinstance(raw_bg, dict) else raw_bg
        for b in items_bg:
            name = b["name"] if isinstance(b, dict) else str(b)
            self.background_map[name.lower()] = name

        self.archetype_map: Dict[str, str] = {k.lower(): k for k in ARCHETYPE_DATA.keys()}
        for cname in self.class_map.values():
            self.archetype_map.setdefault(cname.lower(), cname)

        # Index feat names -> minimum level
        self.feat_level_map: Dict[str, Tuple[str, int]] = {}
        raw_feats = getattr(self.generator, "feats", {}) or {}
        if isinstance(raw_feats, dict):
            feat_iter = []
            for v in raw_feats.values():
                if isinstance(v, list):
                    feat_iter.extend(v)
                elif isinstance(v, dict):
                    feat_iter.append(v)
        else:
            feat_iter = list(raw_feats)

        for ft in feat_iter:
            if not isinstance(ft, dict):
                continue
            fname = (ft.get("name") or "").strip()
            if not fname:
                continue
            flvl = int(ft.get("level") or ft.get("min_level") or 1)
            key = fname.lower()
            if key not in self.feat_level_map or flvl < self.feat_level_map[key][1]:
                self.feat_level_map[key] = (fname, max(1, flvl))

        # Index spell names -> rank
        self.spell_rank_map: Dict[str, Tuple[str, int]] = {}
        for trad_data in SPELL_CATALOG.values():
            if not isinstance(trad_data, dict):
                continue
            for bucket, entries in trad_data.items():
                if not isinstance(entries, list):
                    continue
                default_rank = 0 if "cantrip" in bucket else 1
                m_rank = re.search(r"(\d+)", bucket)
                if m_rank:
                    default_rank = int(m_rank.group(1))
                for sp in entries:
                    if isinstance(sp, dict) and sp.get("name"):
                        sname = sp["name"].strip()
                        srank = int(sp.get("rank", default_rank))
                        self.spell_rank_map[sname.lower()] = (sname, srank)

    def _match_longest_phrase(self, text_lower: str, lookup: Dict[str, str]) -> Optional[str]:
        matches = []
        for k_lower, canonical in lookup.items():
            if len(k_lower) < 3:
                continue
            if re.search(r"\b" + re.escape(k_lower) + r"\b", text_lower):
                matches.append((len(k_lower), canonical))
        if not matches:
            return None
        matches.sort(key=lambda x: x[0], reverse=True)
        return matches[0][1]

    def _parse_with_gemini(self, concept_text: str) -> Dict[str, Any]:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key or genai is None or types is None:
            return {}

        prompt = f"""
Extract Pathfinder 2e Remastered mechanical requirements from the user's character concept.
Return ONLY valid JSON with these exact keys (use null or [] if not mentioned):
{{
  "char_name": string or null,
  "ancestry": string or null,
  "heritage": string or null,
  "background": string or null,
  "character_class": string or null,
  "subclass": string or null,
  "archetype": string or null,
  "explicit_level": integer or null,
  "requested_feats": [string],
  "requested_spells": [string],
  "requested_skills": {{"skill_name": "T|E|M|L"}},
  "wants_companion": boolean,
  "companion_kind": "animal|familiar|eidolon|construct|undead|plant|null"
}}

USER CONCEPT: "{concept_text}"
"""
        for model_name in ("gemini-2.5-flash", "gemini-2.0-flash"):
            try:
                client = genai.Client(api_key=api_key)
                resp = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        temperature=0.1,
                    ),
                )
                if resp and resp.text:
                    raw = resp.text.strip()
                    if raw.startswith("```"):
                        raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.DOTALL)
                    data = json.loads(raw)
                    if isinstance(data, dict):
                        return data
            except Exception:
                continue
        return {}

    def extract_requirements(self, concept_text: str) -> ConceptSpec:
        text = (concept_text or "").strip()
        text_lower = text.lower()
        llm_data = self._parse_with_gemini(text)

        spec = ConceptSpec(raw_text=text)
        if not spec.heritage and "tiefling" in text_lower:
            spec.heritage = "Tiefling"
        if not spec.archetype and "assassin" in text_lower:
            spec.archetype = "Assassin Dedication"
        spec.char_name = llm_data.get("char_name") or None

        # 1. Explicit level extraction ("level 6", "lvl 5", "L4")
        lvl_match = re.search(r"\b(?:level|lvl|l)\s*(\d{1,2})\b", text_lower)
        if lvl_match:
            spec.explicit_level = max(1, min(20, int(lvl_match.group(1))))
        elif isinstance(llm_data.get("explicit_level"), int):
            spec.explicit_level = max(1, min(20, llm_data["explicit_level"]))

        # 2. Ancestry, Heritage, Background, Class, Subclass
        anc_aliases = {
            "yaoguia": "yaoguai",
            "kashiri": "kashrishi",
            "kitsuni": "kitsune",
            "tengu": "tengu",
            "leshi": "leshy",
        }
        norm_text_for_anc = text_lower
        for typo, correct in anc_aliases.items():
            norm_text_for_anc = re.sub(rf"\b{typo}\b", correct, norm_text_for_anc)
        llm_anc = anc_aliases.get((llm_data.get("ancestry") or "").lower(), (llm_data.get("ancestry") or "").lower())
        spec.ancestry = self.ancestry_map.get(llm_anc) or self._match_longest_phrase(norm_text_for_anc, self.ancestry_map)

        spec.heritage = llm_data.get("heritage") or None

        llm_bg = (llm_data.get("background") or "").lower()
        spec.background = self.background_map.get(llm_bg) or self._match_longest_phrase(text_lower, self.background_map)

        llm_cls = (llm_data.get("character_class") or "").lower()
        spec.character_class = self.class_map.get(llm_cls) or self._match_longest_phrase(text_lower, self.class_map)

        spec.subclass = llm_data.get("subclass") or None

        # 2b. Deterministic Champion cause extraction so holy/redeemer/etc. never fall back randomly
        if (spec.character_class or "").lower() == "champion" and not spec.subclass:
            cause_patterns = [
                (r"\bredeemer\b", "Redeemer (Holy)"),
                (r"\bpaladin\b", "Paladin (Holy)"),
                (r"\bliberator\b", "Liberator (Holy)"),
                (r"\btyrant\b", "Tyrant (Unholy)"),
                (r"\bdesecrator\b", "Desecrator (Unholy)"),
                (r"\bantipaladin\b", "Antipaladin (Unholy)"),
                (r"\bholy\b", "Redeemer (Holy)"),
                (r"\bunholy\b", "Desecrator (Unholy)"),
            ]
            for pat, cause_name in cause_patterns:
                if re.search(pat, text_lower):
                    spec.subclass = cause_name
                    break

        # 3. Archetype / Multiclass detection
        llm_arch = (llm_data.get("archetype") or "").lower()
        if llm_arch and llm_arch != "none":
            spec.archetype = self.archetype_map.get(llm_arch) or llm_data.get("archetype")

        if not spec.archetype:
            # Look for "<Archetype> dedication" or "<Archetype> archetype" or "multiclass <Class>"
            arch_pattern = re.search(
                r"\b([a-z][a-z\s'-]{2,28}?)\s+(?:dedication|archetype)\b|\bmulticlass\s+([a-z][a-z\s'-]{2,24}?)\b",
                text_lower,
            )
            if arch_pattern:
                cand = (arch_pattern.group(1) or arch_pattern.group(2) or "").strip()
                spec.archetype = self._match_longest_phrase(cand, self.archetype_map) or cand.title()
            else:
                # Check non-class archetype names directly (e.g., Beastmaster, Familiar Master, Sentinel, Medic)
                non_class_archs = {
                    k: v for k, v in self.archetype_map.items() if k not in self.class_map
                }
                spec.archetype = self._match_longest_phrase(text_lower, non_class_archs)

        # Avoid setting archetype equal to primary class
        if spec.archetype and spec.character_class and spec.archetype.lower() == spec.character_class.lower():
            spec.archetype = None

        # 4. Companion / Familiar / Eidolon detection
        # Word-boundary matching so "pet" doesn't hit "carpet" and "mount" doesn't hit "mountain".
        # "leshy" is intentionally NOT a companion keyword (it is an ancestry).
        companion_keywords = ("companion", "familiar", "eidolon", "mount", "steed", "pet", "horseback")
        CONSTRUCT_WORDS = {"metal", "iron", "steel", "robot", "robotic", "golem", "mechanical", "clockwork", "construct", "brass", "mechanism"}
        UNDEAD_WORDS = {"undead", "skeletal", "zombie", "ghostly", "spectral"}
        PLANT_WORDS = {"plant", "vine", "treant", "wooden", "leafy"}
        COMPANION_ANIMALS = (
            "dog|hound|wolf|bear|cat|panther|tiger|lion|bird|hawk|owl|raven|crow|eagle|"
            "horse|pony|boar|badger|ape|snake|spider|drake|dragon|lizard|fox|beetle|scorpion|rat|bat|frog|toad"
        )
        _all_mod_words = "|".join(sorted(CONSTRUCT_WORDS | UNDEAD_WORDS | PLANT_WORDS))
        m_mod_animal = re.search(rf"\b({_all_mod_words})\s+(?:{COMPANION_ANIMALS})s?\b", text_lower)
        has_mount_term = bool(re.search(r"\b(?:mount|steed|horseback|warhorse)\b", text_lower))
        has_pet_term = bool(re.search(r"\b(?:pet|familiar)\b", text_lower))
        if llm_data.get("wants_companion") or m_mod_animal or any(
            re.search(rf"\b{kw}\b", text_lower) for kw in companion_keywords
        ):
            spec.wants_companion = True
            spec.companion_kind = llm_data.get("companion_kind")
            m_desc = re.search(r"\b([a-z\-]+)\s+(?:animal\s+)?(?:companion|pet)\b", text_lower) or m_mod_animal
            desc = m_desc.group(1) if m_desc else ""

            if desc in CONSTRUCT_WORDS:
                spec.companion_kind = "construct"
            elif desc in UNDEAD_WORDS:
                spec.companion_kind = "undead"
            elif desc in PLANT_WORDS:
                spec.companion_kind = "plant"
            elif not spec.companion_kind:
                if "eidolon" in text_lower:
                    spec.companion_kind = "eidolon"
                elif "construct" in text_lower or "clockwork" in text_lower:
                    spec.companion_kind = "construct"
                elif "undead" in text_lower or "skeleton" in text_lower or "zombie" in text_lower:
                    spec.companion_kind = "undead"
                elif "familiar" in text_lower or "leshy familiar" in text_lower:
                    spec.companion_kind = "familiar"
                else:
                    spec.companion_kind = "animal"
            # Map companion kind to native class or dedication archetype if unspecified
            cls_l = (spec.character_class or "").lower()
            if spec.companion_kind == "eidolon":
                if not spec.character_class and not spec.archetype:
                    spec.character_class = "Summoner"
                elif cls_l != "summoner" and not spec.archetype:
                    spec.archetype = "Summoner"
            # If BOTH a mount/steed AND a separate pet/familiar are requested, unlock the secondary pet via archetype
            if has_mount_term and has_pet_term:
                spec.wants_secondary_pet = True
                if not spec.archetype:
                    spec.archetype = "Familiar Master"
            elif not spec.archetype and cls_l not in NATIVE_COMPANION_CLASSES:
                if spec.companion_kind == "familiar" or has_pet_term:
                    spec.archetype = "Familiar Master"
                elif spec.companion_kind == "construct":
                    spec.archetype = "Clockwork Reanimator"
                elif spec.companion_kind == "undead":
                    spec.archetype = "Undead Master"
                else:
                    spec.archetype = "Beastmaster"

        # 4b. Druid order: explicit text beats Gemini, and Gemini beats random
        if (spec.character_class or "").lower() == "druid":
            explicit_order = detect_druid_order(text_lower)
            if explicit_order:
                spec.subclass = explicit_order
            elif spec.subclass:
                cleaned = re.sub(r"\s*order\s*$", "", spec.subclass, flags=re.I).strip().title()
                spec.subclass = cleaned + DRUID_ORDER_SUFFIX
            elif re.search(r"\banimal companion\b", text_lower):
                spec.subclass = "Animal" + DRUID_ORDER_SUFFIX

        # 5. Requested Feats & Spell Rank / Spell Name matching
        raw_req_feats = list(llm_data.get("requested_feats") or [])
        for fname_l, (canonical_f, _) in self.feat_level_map.items():
            base_fname = re.sub(r"\s*\([^)]*\)$", "", fname_l).strip()
            matched = False
            if len(fname_l) >= 5:
                if fname_l.endswith(")"):
                    matched = bool(re.search(r"\b" + re.escape(fname_l[:-1]) + r"\)", text_lower))
                else:
                    matched = bool(re.search(r"\b" + re.escape(fname_l) + r"\b", text_lower))
            if not matched and len(base_fname) >= 5 and re.search(r"\b" + re.escape(base_fname) + r"\b", text_lower):
                matched = True
            if matched and canonical_f not in raw_req_feats:
                raw_req_feats.append(canonical_f)
        spec.requested_feats = raw_req_feats

        raw_req_spells = list(llm_data.get("requested_spells") or [])
        for sname_l, (canonical_s, _) in self.spell_rank_map.items():
            if len(sname_l) >= 4 and re.search(r"\b" + re.escape(sname_l) + r"\b", text_lower):
                if canonical_s not in raw_req_spells:
                    raw_req_spells.append(canonical_s)
        spec.requested_spells = raw_req_spells

        # 6. Skill proficiency rank mentions ("master in stealth", "expert medicine", "legendary athletics")
        if isinstance(llm_data.get("requested_skills"), dict):
            for sk, rk in llm_data["requested_skills"].items():
                if sk.lower() in SKILL_NAMES and str(rk).upper() in ("T", "E", "M", "L"):
                    spec.requested_skills[sk.lower()] = str(rk).upper()

        for sk in SKILL_NAMES:
            m_sk = re.search(
                rf"\b(trained|expert|master|legendary)\s+(?:in\s+)?{sk}\b|\b{sk}\s*\((trained|expert|master|legendary)\)",
                text_lower,
            )
            if m_sk:
                word = (m_sk.group(1) or m_sk.group(2) or "").lower()
                spec.requested_skills[sk] = word[0].upper()

        return spec

    def compute_minimum_level(self, spec: ConceptSpec) -> Tuple[int, List[LevelRequirement]]:
        reqs: List[LevelRequirement] = [LevelRequirement("Base PF2e Remaster character", 1)]

        if spec.explicit_level:
            reqs.append(LevelRequirement(f"Explicitly requested Level {spec.explicit_level}", spec.explicit_level))

        if spec.archetype:
            reqs.append(LevelRequirement(f"{spec.archetype} Dedication feat slot", 2))

        if spec.wants_companion:
            cls_l = (spec.character_class or "").lower()
            arch_l = (spec.archetype or "").lower()
            if spec.wants_secondary_pet and cls_l in NATIVE_COMPANION_CLASSES:
                reqs.append(LevelRequirement(f"Native {spec.character_class} mount/steed", 1))
                reqs.append(LevelRequirement("Secondary pet/familiar (Familiar Master Dedication)", 2))
            elif cls_l in NATIVE_COMPANION_CLASSES and not any(a in arch_l for a in COMPANION_ARCHETYPES):
                reqs.append(LevelRequirement(f"Native {spec.character_class} {spec.companion_kind or 'companion'}", 1))
            else:
                reqs.append(LevelRequirement(f"Archetype {spec.companion_kind or 'companion'} dedication", 2))

            if "mature" in spec.raw_text.lower():
                reqs.append(LevelRequirement("Mature Animal Companion feat", 4))
            if "incredible" in spec.raw_text.lower():
                reqs.append(LevelRequirement("Incredible Companion feat", 8))
            if "specialized" in spec.raw_text.lower():
                reqs.append(LevelRequirement("Specialized Companion feat", 14))

        # Skill proficiency rank floors
        rank_floors = {"T": 1, "E": 3, "M": 7, "L": 15}
        rank_labels = {"T": "Trained", "E": "Expert", "M": "Master", "L": "Legendary"}
        for sk, rk in spec.requested_skills.items():
            floor = rank_floors.get(rk, 1)
            if floor > 1:
                reqs.append(LevelRequirement(f"{rank_labels[rk]} proficiency in {sk.title()}", floor))

        # Named feat prerequisites
        for feat_name in spec.requested_feats:
            hit = self.feat_level_map.get(feat_name.lower())
            if hit:
                canonical_f, flvl = hit
                if "dedication" in canonical_f.lower():
                    flvl = max(2, flvl)
                reqs.append(LevelRequirement(f"Feat prerequisite: {canonical_f} (Level {flvl})", flvl))

        # Explicit spell rank mentions ("3rd-rank spells", "rank 4 spell", "5th level spells")
        for m in re.finditer(r"\b(\d{1,2})(?:st|nd|rd|th)?[- ]rank\s+spell|\brank\s+(\d{1,2})\s+spell", spec.raw_text.lower()):
            rank = int(m.group(1) or m.group(2))
            if 1 <= rank <= 10:
                min_lvl = max(1, (rank * 2) - 1)
                reqs.append(LevelRequirement(f"Cast Rank {rank} spells", min_lvl))

        # Named spells
        for sp_name in spec.requested_spells:
            hit = self.spell_rank_map.get(sp_name.lower())
            if hit:
                canonical_s, srank = hit
                min_lvl = 1 if srank == 0 else max(1, (srank * 2) - 1)
                reqs.append(LevelRequirement(f"Spell '{canonical_s}' (Rank {srank})", min_lvl))

        min_level = max(1, min(20, max(r.min_level for r in reqs)))
        spec.requirements = reqs
        return min_level, reqs

    def build_lowest_level_sheet(self, concept_text: str) -> Dict[str, Any]:
        spec = self.extract_requirements(concept_text)
        min_level, reqs = self.compute_minimum_level(spec)

        # Sanitize archetype name if it picked up compound phrases or companion types
        archetype_to_use = spec.archetype
        if spec.requested_feats:
            for feat in spec.requested_feats:
                if "dedication" in feat.lower():
                    archetype_to_use = feat
                    break
        elif archetype_to_use and not any(k in archetype_to_use.lower() for k in ["dedication", "archetype"]):
            # If it's a raw phrase like "Vigilante" or "Beastmaster", ensure it's formatted cleanly
            archetype_to_use = archetype_to_use.title()
            if not archetype_to_use.endswith("Dedication") and archetype_to_use not in ["Familiar Master", "Clockwork Reanimator", "Undead Master"]:
                archetype_to_use += " Dedication"

        # NOTE: generator.generate() must accept \`concept_text\` and forward it to resolve_companion().
        sheet = self.generator.generate(
            ancestry_name=spec.ancestry,
            class_name=spec.character_class,
            background_name=spec.background,
            archetype_name=archetype_to_use if min_level >= 2 else None,
            char_name=spec.char_name,
            level=min_level,
            use_dedication=bool(archetype_to_use) and min_level >= 2,
            heritage_name=spec.heritage,
            subclass_name=spec.subclass,
            concept_text=spec.raw_text,
            requested_feats=spec.requested_feats,
        )

        # Verify companion requirement was satisfied; bump to Level 2 if needed
        if spec.wants_companion and sheet.companion is None and min_level < 2:
            min_level = 2
            reqs.append(LevelRequirement("Archetype companion unlock", 2))
            sheet = self.generator.generate(
                ancestry_name=spec.ancestry,
                class_name=spec.character_class,
                background_name=spec.background,
                archetype_name=spec.archetype or "Beastmaster",
                char_name=spec.char_name,
                level=min_level,
                use_dedication=True,
                heritage_name=spec.heritage,
                subclass_name=spec.subclass,
                concept_text=spec.raw_text,
            )

        # Honor explicit attribute priority hints ("strong", "agile", "tough", "smart", "wise", "charismatic")
        t_low = spec.raw_text.lower()
        attr_hints = [
            (["strong", "mighty", "muscular", "brawny", "heavy"], "strength"),
            (["agile", "nimble", "quick", "swift", "acrobatic", "stealthy"], "dexterity"),
            (["tough", "sturdy", "hardy", "resilient", "rugged"], "constitution"),
            (["smart", "clever", "scholarly", "brilliant", "arcane"], "intelligence"),
            (["wise", "perceptive", "insightful", "intuitive"], "wisdom"),
            (["charismatic", "charming", "persuasive", "inspiring"], "charisma"),
        ]
        preferred_attr = None
        for kws, attr_field in attr_hints:
            if any(re.search(r"\b" + re.escape(k) + r"\b", t_low) for k in kws):
                preferred_attr = attr_field
                break

        if preferred_attr:
            attrs = sheet.attributes
            all_attr_names = ["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"]
            cur_val = getattr(attrs, preferred_attr)
            # Determine max legal cap at this level (+4 at L1-9, +5 at L10-19, +6 at L20)
            max_cap = 4 if sheet.level < 10 else (5 if sheet.level < 20 else 6)
            # If preferred_attr isn't the highest stat, non-key cap at L1 is +3 (+4 if key attr)
            highest_other = max(getattr(attrs, a) for a in all_attr_names if a != preferred_attr)
            target_val = min(max_cap, max(3, highest_other))
            # If class key stat is already +4 and different from preferred_attr, non-key L1 cap is +3
            if sheet.level < 5 and highest_other >= 4 and cur_val < 4:
                target_val = 3

            while getattr(attrs, preferred_attr) < target_val:
                # Donate 1 boost from the highest non-key, non-preferred attribute (> 0)
                donors = [
                    a for a in all_attr_names
                    if a != preferred_attr and getattr(attrs, a) >= 2
                ]
                if not donors:
                    break
                # Prefer donating from stats that aren't the sole +4 key stat
                non_key_donors = [a for a in donors if getattr(attrs, a) < 4] or donors
                donor = max(non_key_donors, key=lambda a: getattr(attrs, a))
                old_d = getattr(attrs, donor)
                setattr(attrs, donor, old_d - 1)
                setattr(attrs, preferred_attr, getattr(attrs, preferred_attr) + 1)

                # Update dependent skill & defense modifiers for the shifted point
                attr_short = {"strength": "str", "dexterity": "dex", "constitution": "con", "intelligence": "int", "wisdom": "wis", "charisma": "cha"}
                sk_map = {
                    "athletics": "strength", "acrobatics": "dexterity", "stealth": "dexterity", "thievery": "dexterity",
                    "arcana": "intelligence", "crafting": "intelligence", "occultism": "intelligence", "society": "intelligence",
                    "medicine": "wisdom", "nature": "wisdom", "religion": "wisdom", "survival": "wisdom",
                    "deception": "charisma", "diplomacy": "charisma", "intimidation": "charisma", "performance": "charisma",
                }
                for sk in (sheet.all_skills or []):
                    mapped = sk_map.get((sk.name or "").lower())
                    if mapped == preferred_attr:
                        sk.modifier += 1
                    elif mapped == donor:
                        sk.modifier -= 1
                if donor == "constitution":
                    sheet.defenses.hp = max(1, sheet.defenses.hp - sheet.level)
                    sheet.defenses.fortitude.modifier -= 1
                elif preferred_attr == "constitution":
                    sheet.defenses.hp += sheet.level
                    sheet.defenses.fortitude.modifier += 1
                if donor == "wisdom":
                    sheet.defenses.will.modifier -= 1
                    sheet.perception.modifier -= 1
                elif preferred_attr == "wisdom":
                    sheet.defenses.will.modifier += 1
                    sheet.perception.modifier += 1
                if donor == "dexterity":
                    sheet.defenses.reflex.modifier -= 1
                elif preferred_attr == "dexterity":
                    sheet.defenses.reflex.modifier += 1

        # Honor explicit weapon/shield mentions in concept text and override random default weapons within PF2e rules
        martial_capable_classes = {
            "alchemist", "animist", "barbarian", "bard", "champion", "commander",
            "exemplar", "fighter", "gunslinger", "inventor", "investigator",
            "kineticist", "magus", "monk", "ranger", "rogue", "summoner",
            "swashbuckler", "thaumaturge", "vindicator",
        }
        cls_key_eq = (spec.character_class or sheet.character_class or "").strip().lower()
        arch_key_eq = (spec.archetype or "").strip().lower()
        has_martial_prof = cls_key_eq in martial_capable_classes or any(
            m in arch_key_eq for m in ("fighter", "ranger", "barbarian", "champion", "monk", "rogue", "swashbuckler", "gunslinger", "archer", "mauler")
        )

        weapon_presets = [
            ("glaive", "Glaive", "1d8", "Slashing", ["Deadly d8", "Forceful", "Reach"], True),
            ("laive", "Glaive", "1d8", "Slashing", ["Deadly d8", "Forceful", "Reach"], True),
            ("greatsword", "Greatsword", "1d12", "Slashing", ["Versatile P"], True),
            ("bastard sword", "Bastard Sword", "1d8", "Slashing", ["Two-Hand d12"], True),
            ("shortsword", "Shortsword", "1d6", "Piercing", ["Agile", "Finesse", "Versatile S"], True),
            ("longsword", "Longsword", "1d8", "Slashing", ["Versatile P"], True),
            ("sword", "Longsword", "1d8", "Slashing", ["Versatile P"], True),
            ("rapier", "Rapier", "1d6", "Piercing", ["Deadly d8", "Disarm", "Finesse"], True),
            ("greataxe", "Greataxe", "1d12", "Slashing", ["Sweep"], True),
            ("battleaxe", "Battleaxe", "1d8", "Slashing", ["Sweep"], True),
            ("axe", "Battleaxe", "1d8", "Slashing", ["Sweep"], True),
            ("maul", "Maul", "1d12", "Bludgeoning", ["Shove"], True),
            ("warhammer", "Warhammer", "1d8", "Bludgeoning", ["Shove"], True),
            ("longbow", "Longbow", "1d8", "Piercing", ["Deadly d10", "Volley 30 ft"], True),
            ("shortbow", "Shortbow", "1d6", "Piercing", ["Deadly d10"], True),
            ("bow", "Shortbow", "1d6", "Piercing", ["Deadly d10"], True),
            ("dagger", "Dagger", "1d4", "Piercing", ["Agile", "Finesse", "Thrown 10 ft", "Versatile S"], False),
            ("spear", "Spear", "1d6", "Piercing", ["Thrown 20 ft"], False),
            ("staff", "Staff", "1d4", "Bludgeoning", ["Two-Hand d8"], False),
            ("club", "Club", "1d4", "Bludgeoning", ["Thrown 10 ft"], False),
            ("crossbow", "Crossbow", "1d8", "Piercing", ["Range 120 ft", "Reload 1"], False),
        ]

        parsed_strikes = []
        added_weapons = set()
        for kw, wname, wdice, wtype, wtraits, is_martial in weapon_presets:
            if wname in added_weapons:
                continue
            if kw in ("sword", "bow", "axe") and any(w in added_weapons for w in ("Greatsword", "Bastard Sword", "Shortsword", "Longsword", "Longbow", "Shortbow", "Greataxe", "Battleaxe")):
                continue
            if re.search(r"\b" + re.escape(kw) + r"\b", t_low):
                if is_martial and not has_martial_prof:
                    continue
                added_weapons.add(wname)
                is_ranged = "bow" in wname.lower() or "crossbow" in wname.lower()
                best_mod = sheet.attributes.dexterity if is_ranged else (max(sheet.attributes.strength, sheet.attributes.dexterity) if "Finesse" in wtraits else sheet.attributes.strength)
                prof_bonus = 4 if cls_key_eq == "fighter" else 2
                atk = best_mod + sheet.level + prof_bonus
                dmg_mod = 0 if is_ranged else sheet.attributes.strength
                dmg_str = f"{wdice}+{dmg_mod}" if dmg_mod > 0 else (f"{wdice}{dmg_mod}" if dmg_mod < 0 else wdice)
                strike_data = {
                    "name": wname,
                    "attack_bonus": str(atk),
                    "map_second": str(atk - 5),
                    "map_third": str(atk - 10),
                    "damage_dice": dmg_str,
                    "damage_type": wtype,
                    "traits": wtraits,
                }
                strike_cls = type(sheet.equipment.strikes[0]) if sheet.equipment.strikes else None
                new_entry = strike_cls.model_validate(strike_data) if hasattr(strike_cls, "model_validate") else strike_data
                parsed_strikes.append(new_entry)

        two_handed_weapons = {"Glaive", "Greatsword", "Greataxe", "Maul", "Longbow", "Shortbow", "Staff", "Crossbow"}
        ranged_weapon_names = {"Longbow", "Shortbow", "Crossbow"}
        strict_only_weapon = bool(re.search(
            r"\b(?:only|just|solely|exclusively)\s+(?:a|an|one|the|this)?\s*(?:[a-z]+\s+){0,2}(?:weapon|glaive|greatsword|bastard sword|shortsword|longsword|sword|rapier|greataxe|battleaxe|axe|maul|warhammer|longbow|shortbow|bow|dagger|spear|staff|club|crossbow)\b|\bsingle\s+weapon\b|\bno\s+(?:other|extra|secondary|backup)\s+weapons?\b",
            t_low,
        ))
        innate_tokens = ("elemental blast", "unarmed", "horn", "claw", "pincer", "fang", "jaw", "talon", "tail", "venom", "poison", "spine", "quill")

        if parsed_strikes and hasattr(sheet.equipment, "strikes"):
            preserved_innate = [
                s for s in (sheet.equipment.strikes or [])
                if any(tok in ((s.name if hasattr(s, "name") else str(s)).lower()) for tok in innate_tokens)
            ]
            if strict_only_weapon:
                final_strikes = parsed_strikes + preserved_innate
            else:
                # Keep full legal loadout: replace/dedupe matching melee/ranged slots and cap physical weapons cleanly
                existing_phys = [
                    s for s in (sheet.equipment.strikes or [])
                    if not any(tok in ((s.name if hasattr(s, "name") else str(s)).lower()) for tok in innate_tokens)
                ]
                parsed_names_low = {(ps.name if hasattr(ps, "name") else ps.get("name", "")).lower() for ps in parsed_strikes}
                parsed_has_ranged = any(n in ranged_weapon_names for n in parsed_names_low)
                parsed_has_melee = any(n not in ranged_weapon_names for n in parsed_names_low)

                kept_backups = []
                for ex in existing_phys:
                    ex_name_low = (ex.name if hasattr(ex, "name") else str(ex)).lower()
                    if ex_name_low in parsed_names_low:
                        continue
                    ex_is_ranged = any(rw in ex_name_low for rw in ("bow", "crossbow", "sling", "dart", "javelin"))
                    if parsed_has_ranged and ex_is_ranged:
                        continue
                    if parsed_has_melee and not ex_is_ranged:
                        continue
                    kept_backups.append(ex)

                final_strikes = parsed_strikes + kept_backups[:1] + preserved_innate

            # Dedupe duplicate ranged weapons (e.g., Longbow + Heavy Crossbow or Crossbow + Shortbow) unless explicitly requested
            ranged_tokens = ("bow", "crossbow", "sling")
            explicit_ranged_count = sum(
                1 for kw, wname, *_ in weapon_presets
                if any(rt in wname.lower() for rt in ranged_tokens)
                and re.search(r"\b" + re.escape(kw) + r"\b", t_low)
            )
            if explicit_ranged_count <= 1:
                deduped_strikes = []
                seen_ranged = False
                for st_obj in final_strikes:
                    st_n_low = ((st_obj.name if hasattr(st_obj, "name") else str(st_obj)) or "").lower()
                    is_ranged_st = any(rt in st_n_low for rt in ranged_tokens)
                    if is_ranged_st:
                        if seen_ranged:
                            continue
                        seen_ranged = True
                    deduped_strikes.append(st_obj)
                final_strikes = deduped_strikes

            # If only 1 physical melee weapon is present and no 'only' restriction is specified, ensure a ranged backup strike exists
            ranged_kw_tuple = ("bow", "crossbow", "sling", "dart", "javelin")
            phys_after_dedup = [
                s for s in final_strikes
                if not any(tok in ((s.name if hasattr(s, "name") else str(s)) or "").lower() for tok in innate_tokens)
            ]
            has_any_ranged = any(
                any(rk in ((s.name if hasattr(s, "name") else str(s)) or "").lower() for rk in ranged_kw_tuple)
                for s in phys_after_dedup
            )
            if not strict_only_weapon and len(phys_after_dedup) == 1 and not has_any_ranged:
                base_strike = phys_after_dedup[0]
                strike_cls = type(base_strike) if hasattr(base_strike, "attack_bonus") else None
                lvl_val = getattr(sheet, "level", 1) or 1
                dex_mod = int(getattr(getattr(sheet, "mods", {}), "get", lambda k, d=0: getattr(getattr(sheet, "mods", None), k, d))("dex", 0) or 0)
                atk_bonus = 2 + lvl_val + dex_mod
                backup_payload = {
                    "name": "Shortbow",
                    "attack_bonus": str(atk_bonus),
                    "map_second": str(atk_bonus - 5),
                    "map_third": str(atk_bonus - 10),
                    "damage_dice": "1d6",
                    "damage_type": "Piercing",
                    "traits": ["Deadly d10", "Range 60 ft"],
                }
                if strike_cls is not None and hasattr(strike_cls, "model_validate"):
                    try:
                        final_strikes.append(strike_cls.model_validate(backup_payload))
                    except Exception:
                        final_strikes.append(backup_payload)
                else:
                    final_strikes.append(backup_payload)

            sheet.equipment.strikes = final_strikes

            # Sync equipment.weapons Item list with physical weapons only (no innate natural attacks)
            final_phys_strikes = [
                s for s in (sheet.equipment.strikes or [])
                if not any(tok in ((s.name if hasattr(s, "name") else str(s)).lower()) for tok in innate_tokens)
            ]
            if hasattr(sheet.equipment, "weapons"):
                item_cls = type(sheet.equipment.weapons[0]) if sheet.equipment.weapons else None
                new_weapon_items = []
                for ps in final_phys_strikes:
                    w_title = ps.name if hasattr(ps, "name") else ps.get("name", "Weapon")
                    w_traits = ps.traits if hasattr(ps, "traits") else ps.get("traits", [])
                    item_payload = {
                        "name": w_title,
                        "category": "Weapon",
                        "bulk": "2" if w_title in two_handed_weapons else "1",
                        "traits": w_traits,
                        "description": f"{w_title} ({', '.join(w_traits)})" if w_traits else w_title,
                    }
                    if item_cls is not None and hasattr(item_cls, "model_validate"):
                        try:
                            new_weapon_items.append(item_cls.model_validate(item_payload))
                            continue
                        except Exception:
                            pass
                    new_weapon_items.append(item_payload)
                sheet.equipment.weapons = new_weapon_items

        # Shield override & two-handed hand-slot legality
        wants_shield = bool(re.search(r"\b(?:shield|buckler)\b", t_low)) and not bool(re.search(r"\bno\s+shield\b", t_low))
        only_two_handed = bool(added_weapons) and added_weapons.issubset(two_handed_weapons)
        if wants_shield:
            is_buckler = "buckler" in t_low
            sh_name = "Buckler" if is_buckler else "Steel Shield"
            sh_bonus = 1 if is_buckler else 2
            if hasattr(sheet.equipment, "shield"):
                sh_payload = {"name": sh_name, "category": "Shield", "bulk": "L" if is_buckler else "1", "traits": [], "description": f"+{sh_bonus} AC when raised"}
                if sheet.equipment.shield is not None and hasattr(type(sheet.equipment.shield), "model_validate"):
                    try:
                        sheet.equipment.shield = type(sheet.equipment.shield).model_validate(sh_payload)
                    except Exception:
                        pass
                elif sheet.equipment.weapons and hasattr(type(sheet.equipment.weapons[0]), "model_validate"):
                    try:
                        sheet.equipment.shield = type(sheet.equipment.weapons[0]).model_validate(sh_payload)
                    except Exception:
                        pass
            if hasattr(sheet.equipment, "gear") and not any("shield" in str(g).lower() or "buckler" in str(g).lower() for g in (sheet.equipment.gear or [])):
                sheet.equipment.gear.append(f"{sh_name} (+{sh_bonus} AC when raised)")
            if hasattr(sheet.defenses, "ac_notes"):
                sheet.defenses.ac_notes = f"+{sh_bonus} Shield"
        elif only_two_handed:
            # Two-handed weapons occupy both hands; clear any randomly assigned shield
            if hasattr(sheet.equipment, "shield"):
                sheet.equipment.shield = None
            if hasattr(sheet.equipment, "gear"):
                sheet.equipment.gear = [g for g in (sheet.equipment.gear or []) if "shield" not in str(g).lower()]
            if hasattr(sheet.defenses, "ac_notes") and "shield" in (getattr(sheet.defenses, "ac_notes", "") or "").lower():
                sheet.defenses.ac_notes = None

        # Explicit Armor override (within class/archetype armor proficiency rules)
        heavy_classes = {"champion", "fighter", "guardian"}
        medium_classes = heavy_classes | {"barbarian", "cleric", "druid", "inventor", "magus", "ranger", "thaumaturge", "vindicator", "commander"}
        light_classes = medium_classes | {"alchemist", "animist", "bard", "gunslinger", "investigator", "kineticist", "oracle", "rogue", "summoner", "swashbuckler"}
        has_heavy = cls_key_eq in heavy_classes or "sentinel" in arch_key_eq
        has_medium = has_heavy or cls_key_eq in medium_classes or any(a in arch_key_eq for a in ("champion", "fighter", "guardian"))
        has_light = has_medium or cls_key_eq in light_classes

        armor_presets = [
            ("full plate", "Full Plate", "heavy", 6, 0),
            ("half plate", "Half Plate", "heavy", 5, 1),
            ("splint mail", "Splint Mail", "heavy", 5, 1),
            ("breastplate", "Breastplate", "medium", 4, 1),
            ("chain mail", "Chain Mail", "medium", 4, 1),
            ("scale mail", "Scale Mail", "medium", 3, 2),
            ("hide armor", "Hide Armor", "medium", 3, 2),
            ("studded leather", "Studded Leather Armor", "light", 2, 3),
            ("leather armor", "Leather Armor", "light", 1, 4),
            ("padded armor", "Padded Armor", "light", 1, 3),
            ("unarmored", "Explorer's Clothing", "unarmored", 0, 5),
            ("explorer's clothing", "Explorer's Clothing", "unarmored", 0, 5),
        ]
        for akw, aname, acat, item_ac, dex_cap in armor_presets:
            if re.search(r"\b" + re.escape(akw) + r"\b", t_low):
                legal_armor = (
                    (acat == "heavy" and has_heavy)
                    or (acat == "medium" and has_medium)
                    or (acat == "light" and has_light)
                    or (acat == "unarmored")
                )
                if legal_armor:
                    if hasattr(sheet.equipment, "armor"):
                        arm_payload = {"name": aname, "category": f"{acat.title()} Armor", "bulk": "3" if acat == "heavy" else ("2" if acat == "medium" else "1"), "traits": [], "description": f"+{item_ac} AC, Dex Cap +{dex_cap}"}
                        arm_cls = type(sheet.equipment.armor) if sheet.equipment.armor is not None else (type(sheet.equipment.weapons[0]) if sheet.equipment.weapons else None)
                        if arm_cls is not None and hasattr(arm_cls, "model_validate"):
                            try:
                                sheet.equipment.armor = arm_cls.model_validate(arm_payload)
                            except Exception:
                                pass
                    if hasattr(sheet.defenses, "ac"):
                        prof_ac = 4 if (cls_key_eq == "monk" and acat == "unarmored") else 2
                        eff_dex = min(int(sheet.attributes.dexterity), dex_cap)
                        sheet.defenses.ac = 10 + sheet.level + prof_ac + item_ac + eff_dex
                break

        # Companion species override when explicitly named in prompt (e.g., "on horseback" -> Horse)
        if getattr(sheet, "companion", None) is not None:
            species_hints = [
                (r"\b(?:horseback|warhorse|horse)\b", "Horse"),
                (r"\bwolf\b", "Wolf"),
                (r"\bbear\b", "Bear"),
                (r"\bboar\b", "Boar"),
                (r"\bbadger\b", "Badger"),
                (r"\b(?:hawk|eagle|owl|bird|falcon)\b", "Bird"),
                (r"\b(?:panther|tiger|lion|leopard|cat)\b", "Cat"),
                (r"\bsnake|viper|python\b", "Snake"),
                (r"\bshark\b", "Shark"),
                (r"\bcrocodile|alligator\b", "Crocodile"),
            ]
            for spat, sp_label in species_hints:
                if re.search(spat, t_low):
                    comp = sheet.companion
                    if hasattr(comp, "species"):
                        comp.species = sp_label
                    if hasattr(comp, "creature_type") and comp.creature_type == "Animal Companion":
                        comp.creature_type = f"Animal Companion ({sp_label})"
                    break

        payload = sheet.model_dump()
        payload["concept_resolution"] = {
            "concept_text": spec.raw_text,
            "minimum_level": min_level,
            "extracted": {
                "ancestry": spec.ancestry or payload.get("ancestry"),
                "heritage": spec.heritage or payload.get("heritage"),
                "background": spec.background or payload.get("background"),
                "character_class": spec.character_class or payload.get("character_class"),
                "subclass": spec.subclass or payload.get("subclass"),
                "archetype": spec.archetype or payload.get("archetype"),
                "wants_companion": spec.wants_companion,
                "requested_feats": spec.requested_feats,
                "requested_spells": spec.requested_spells,
                "requested_skills": spec.requested_skills,
            },
            "level_drivers": [
                {"reason": r.reason, "min_level": r.min_level}
                for r in sorted(reqs, key=lambda x: (-x.min_level, x.reason))
            ],
        }
        return payload
