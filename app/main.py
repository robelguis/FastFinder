from app.engine.subclasses import CLASS_SUBCLASSES
from app.engine.archetypes import ARCHETYPES_CATALOG, get_all_archetype_names
from pathlib import Path
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, Query, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

from app.engine.generator import PF2eGenerator
from app.engine.subclasses import CLASS_SUBCLASSES
from app.engine.archetypes import ARCHETYPES_CATALOG, get_all_archetype_names
from app.engine.foundry import export_to_foundry_actor

app = FastAPI(title="FastFinder PF2e Generator")

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

generator = PF2eGenerator()


class LevelUpPayload(BaseModel):
    character: Dict[str, Any]
    target_level: int = Field(..., ge=1, le=7)
    use_dedication: bool = False
    archetype: Optional[str] = None


@app.get("/")
async def root():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/options")
def get_options():
    subclasses_by_class = {}
    for cls_k, sub_info in CLASS_SUBCLASSES.items():
        subclasses_by_class[cls_k.lower()] = [o["name"] for o in sub_info.get("options", [])]

    return {
        "ancestries": sorted([a["name"] for a in generator.ancestries.values()]),
        "classes": sorted([c["name"] for c in generator.classes.values()]),
        "backgrounds": sorted([b["name"] for b in generator.backgrounds.values()]),
        "archetypes": get_all_archetype_names(),
        "subclasses": subclasses_by_class,
    }

@app.get("/api/generate")
async def generate_character(
    name: Optional[str] = None,
    ancestry: Optional[str] = None,
    class_name: Optional[str] = None,
    subclass: Optional[str] = None,
    background: Optional[str] = None,
    archetype: Optional[str] = None,
    level: int = Query(1, ge=1, le=7),
    dedication: bool = Query(False),
):
    try:
        clean_arch = None if not archetype or archetype.lower() in ["any", "any archetype", "none"] else archetype
        sheet = generator.generate(
            ancestry_name=ancestry,
            class_name=class_name,
            subclass_name=subclass,
            background_name=background,
            archetype_name=clean_arch,
            char_name=name,
            level=level,
            use_dedication=dedication or bool(clean_arch),
        )
        return sheet
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/levelup")
async def level_up_endpoint(payload: LevelUpPayload):
    char_data = payload.character
    current_level = int(char_data.get("level", 1))
    target = max(1, min(7, int(payload.target_level)))

    if target == current_level:
        return char_data

    # Lock archetype
    existing_arch = char_data.get("archetype") or char_data.get("archetype_name")
    if isinstance(existing_arch, dict):
        existing_arch = existing_arch.get("name")

    if existing_arch and str(existing_arch).lower() not in ["", "none", "any", "any archetype"]:
        locked_arch = str(existing_arch).strip()
    else:
        req_arch = payload.archetype
        locked_arch = None if not req_arch or req_arch.lower() in ["any", "any archetype", "none"] else req_arch.strip()

    # In PF2e, dedication archetypes are level 2+ only
    use_ded = (payload.use_dedication or bool(locked_arch)) if target >= 2 else False

    try:
        if target > current_level:
            updated_sheet = generator.level_up(
                char_data,
                target,
                use_dedication=use_ded,
                archetype_name=locked_arch
            )
            return updated_sheet
        else:
            # Scale down: lock ancestry, heritage, class, subclass, background, name, and archetype
            anc_val = char_data.get("ancestry")
            anc_name = anc_val.get("name") if isinstance(anc_val, dict) else str(anc_val) if anc_val else None

            heritage_val = char_data.get("heritage")
            heritage_name = heritage_val.get("name") if isinstance(heritage_val, dict) else str(heritage_val) if heritage_val else None

            cls_name = char_data.get("character_class")

            subclass_val = char_data.get("subclass")
            subclass_name = subclass_val.get("name") if isinstance(subclass_val, dict) else str(subclass_val) if subclass_val else None

            bg_name = char_data.get("background")
            c_name = char_data.get("name")

            scaled_sheet = generator.generate(
                ancestry_name=anc_name,
                class_name=cls_name,
                background_name=bg_name,
                archetype_name=locked_arch if target >= 2 else None,
                char_name=c_name,
                level=target,
                use_dedication=use_ded,
                heritage_name=heritage_name,
                subclass_name=subclass_name
            )
            return scaled_sheet
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/export/foundry")
async def export_foundry(
    name: Optional[str] = None,
    ancestry: Optional[str] = None,
    class_name: Optional[str] = None,
    level: int = Query(1, ge=1, le=7),
    dedication: bool = Query(False),
):
    try:
        sheet = generator.generate(
            ancestry_name=ancestry,
            class_name=class_name,
            char_name=name,
            level=level,
            use_dedication=dedication,
        )
        foundry_actor = export_to_foundry_actor(sheet)
        filename = f"{sheet.name.lower().replace(' ', '_')}_foundry.json"
        return JSONResponse(
            content=foundry_actor,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
