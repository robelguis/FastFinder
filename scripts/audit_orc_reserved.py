#!/usr/bin/env python3
"""Scan FastFinder files for Paizo Reserved Material to prepare for ORC compliance."""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Directories and extensions to skip/include
SKIP_DIRS = {".git", ".venv", "venv", "__pycache__", "node_modules", ".pytest_cache", "dist", "build"}
SCAN_EXTS = {".json", ".yaml", ".yml", ".py", ".js", ".html", ".md", ".txt", ".csv"}

# Categories of Paizo Reserved Material (non-exhaustive starter list)
RESERVED_TERMS: dict[str, list[str]] = {
    "trademarks": [
        "Paizo",
        "Pathfinder",
        "Starfinder",
        "Lost Omens",
        "Pathfinder Society",
        "Golarion",
        "Archives of Nethys",
    ],
    "deities": [
        "Abadar",
        "Achaekek",
        "Arazni",
        "Aroden",
        "Asmodeus",
        "Calistria",
        "Cayden Cailean",
        "Desna",
        "Erastil",
        "Gorum",
        "Gozreh",
        "Iomedae",
        "Irori",
        "Lamashtu",
        "Nethys",
        "Norgorber",
        "Pharasma",
        "Rovagug",
        "Sarenrae",
        "Shelyn",
        "Torag",
        "Urgathoa",
        "Zon-Kuthon",
        "Godclaw",
        "Prismatic Ray",
    ],
    "locations_and_regions": [
        "Absalom",
        "Alkenstar",
        "Andoran",
        "Avistan",
        "Brevoy",
        "Cheliax",
        "Garund",
        "Inner Sea",
        "Irrisen",
        "Jalmeray",
        "Katapesh",
        "Kyonin",
        "Lastwall",
        "Mana Wastes",
        "Mendev",
        "Mwangi",
        "Mwangi Expanse",
        "Nidal",
        "Numeria",
        "Osirion",
        "Qadira",
        "Razmiran",
        "Sarkoris",
        "Shackles",
        "Sovyrian",
        "Starstone",
        "Taldor",
        "Tian Xia",
        "Ustalav",
        "Varisia",
        "Worldwound",
    ],
    "factions_and_lore": [
        "Aldori",
        "Aspis Consortium",
        "Bellflower Network",
        "Eagle Knights",
        "Firebrands",
        "Hellknight",
        "Knights of Lastwall",
        "Magaambya",
        "Old-Mage Jatembe",
        "Red Mantis",
        "Runelord",
        "Tar-Baphon",
        "Whispering Way",
    ],
}

# Compile whole-word, case-insensitive patterns
COMPILED: dict[str, list[tuple[str, re.Pattern[str]]]] = {
    cat: [(term, re.compile(rf"\b{re.escape(term)}\b", re.IGNORECASE)) for term in terms]
    for cat, terms in RESERVED_TERMS.items()
}


def should_scan(path: Path) -> bool:
    if any(part in SKIP_DIRS for part in path.parts):
        return False
    if path.name == "audit_orc_reserved.py" or path.name == "orc_audit_report.json":
        return False
    return path.suffix.lower() in SCAN_EXTS


def scan_repo() -> dict:
    category_counts: Counter[str] = Counter()
    term_counts: Counter[str] = Counter()
    file_counts: Counter[str] = Counter()
    findings: list[dict] = []

    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or not should_scan(path):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        rel_path = str(path.relative_to(ROOT))
        for line_no, line in enumerate(text.splitlines(), 1):
            for cat, patterns in COMPILED.items():
                for term, regex in patterns:
                    matches = regex.findall(line)
                    if matches:
                        count = len(matches)
                        category_counts[cat] += count
                        term_counts[f"{cat}:{term}"] += count
                        file_counts[rel_path] += count
                        findings.append(
                            {
                                "file": rel_path,
                                "line": line_no,
                                "category": cat,
                                "term": term,
                                "snippet": line.strip()[:160],
                            }
                        )

    return {
        "total_hits": sum(category_counts.values()),
        "files_with_hits": len(file_counts),
        "by_category": dict(category_counts.most_common()),
        "top_terms": dict(term_counts.most_common(25)),
        "top_files": dict(file_counts.most_common(20)),
        "findings": findings,
    }


def main() -> None:
    report = scan_repo()
    out_path = ROOT / "orc_audit_report.json"
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("=== FASTFINDER ORC RESERVED MATERIAL AUDIT ===")
    print(f"Total hits      : {report['total_hits']}")
    print(f"Files affected  : {report['files_with_hits']}")
    print("\nHits by category:")
    for cat, cnt in report["by_category"].items():
        print(f"  {cat:<24} {cnt}")

    print("\nTop 15 flagged terms:")
    for term, cnt in list(report["top_terms"].items())[:15]:
        print(f"  {cnt:5d}x  {term}")

    print("\nTop 15 affected files:")
    for fpath, cnt in list(report["top_files"].items())[:15]:
        print(f"  {cnt:5d}x  {fpath}")

    print(f"\nFull line-by-line report written to: {out_path}")


if __name__ == "__main__":
    main()
