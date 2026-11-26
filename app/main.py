from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.engine.archetypes import get_all_archetype_names
from app.engine.deities import get_all_deities, list_all_domains
from app.engine.foundry import export_to_foundry_actor
from app.engine.generator import PF2eGenerator
from app.engine.subclasses import CLASS_SUBCLASSES

app = FastAPI(title="FastFinder PF2e Generator")

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

generator = PF2eGenerator()


def _normalize_archetype(archetype: Optional[str]) -> Optional[str]:
    if not archetype or archetype.strip().lower() in ("", "any", "any archetype", "none"):
        return None
    return archetype.strip()


class ConceptRequest(BaseModel):
    concept: str


class LevelUpPayload(BaseModel):
    character: Dict[str, Any]
    target_level: int = Field(..., ge=1, le=20)
    use_dedication: bool = False
    archetype: Optional[str] = None


@app.get("/")
def root():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/options")
def get_options():
    subclasses_by_class = {
        cls_k.lower(): [o["name"] for o in sub_info.get("options", [])]
        for cls_k, sub_info in CLASS_SUBCLASSES.items()
    }
    return {
        "ancestries": sorted(a["name"] for a in generator.ancestries.values()),
        "classes": sorted(c["name"] for c in generator.classes.values()),
        "backgrounds": sorted(b["name"] for b in generator.backgrounds.values()),
        "archetypes": get_all_archetype_names(),
        "subclasses": subclasses_by_class,
        "deities": [d["name"] for d in get_all_deities()],
        "deity_domains": {
            d["name"].lower(): {
                "primary": d.get("domains", {}).get("primary", []),
                "alternate": d.get("domains", {}).get("alternate", []),
            }
            for d in get_all_deities()
        },
        "domains": list_all_domains(),
    }


@app.get("/api/generate")
def generate_character(
    name: Optional[str] = None,
    ancestry: Optional[str] = None,
    heritage: Optional[str] = None,
    class_name: Optional[str] = None,
    subclass: Optional[str] = None,
    background: Optional[str] = None,
    deity: Optional[str] = None,
    domain: Optional[str] = None,
    archetype: Optional[str] = None,
    level: int = Query(1, ge=1, le=20),
    dedication: bool = Query(False),
):
    try:
        clean_arch = _normalize_archetype(archetype)
        clean_heritage = heritage.strip() if heritage and heritage.strip() and heritage.strip().lower() not in ("any", "any heritage", "none") else None
        return generator.generate(
            ancestry_name=ancestry,
            heritage_name=clean_heritage,
            class_name=class_name,
            subclass_name=subclass,
            background_name=background,
            deity_name=deity,
            domain_name=domain,
            archetype_name=clean_arch,
            char_name=name,
            level=level,
            use_dedication=dedication or bool(clean_arch),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/generate-from-concept")
async def generate_from_concept(req: ConceptRequest):
    try:
        return generator.generate_character_from_concept(req.concept)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/epic-backstory")
async def epic_backstory(char_data: dict):
    try:
        return generator.generate_epic_backstory(char_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/levelup")
def level_up_endpoint(payload: LevelUpPayload):
    char_data = payload.character
    current_level = int(char_data.get("level", 1))
    target = max(1, min(20, int(payload.target_level)))

    if target == current_level:
        return char_data

    existing_arch = char_data.get("archetype") or char_data.get("archetype_name")
    if isinstance(existing_arch, dict):
        existing_arch = existing_arch.get("name")

    locked_arch = _normalize_archetype(str(existing_arch)) if existing_arch else _normalize_archetype(payload.archetype)
    use_ded = (payload.use_dedication or bool(locked_arch)) if target >= 2 else False

    try:
        return generator.level_up(
            char_data,
            target,
            use_dedication=use_ded,
            archetype_name=locked_arch,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/export/foundry")
def export_foundry(
    name: Optional[str] = None,
    ancestry: Optional[str] = None,
    class_name: Optional[str] = None,
    subclass: Optional[str] = None,
    background: Optional[str] = None,
    deity: Optional[str] = None,
    domain: Optional[str] = None,
    archetype: Optional[str] = None,
    level: int = Query(1, ge=1, le=20),
    dedication: bool = Query(False),
):
    try:
        clean_arch = _normalize_archetype(archetype)
        sheet = generator.generate(
            ancestry_name=ancestry,
            class_name=class_name,
            subclass_name=subclass,
            background_name=background,
            deity_name=deity,
            domain_name=domain,
            archetype_name=clean_arch,
            char_name=name,
            level=level,
            use_dedication=dedication or bool(clean_arch),
        )
        foundry_actor = export_to_foundry_actor(sheet)
        char_name = getattr(sheet, "name", None) or (sheet.get("name") if isinstance(sheet, dict) else "character")
        filename = f"{char_name.lower().replace(' ', '_')}_foundry.json"

        return JSONResponse(
            content=foundry_actor,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
