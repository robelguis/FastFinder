from app.engine.archetypes import ARCHETYPES_CATALOG, get_all_archetype_names
from pathlib import Path
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, Query, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

from app.engine.generator import PF2eGenerator
from app.engine.archetypes import ARCHETYPES
from app.engine.foundry import export_to_foundry_actor

app = FastAPI(title="FastFinder PF2e Generator")

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

generator = PF2eGenerator()


class LevelUpPayload(BaseModel):
    character: Dict[str, Any]
    target_level: int = Field(..., ge=2, le=6)


@app.get("/")
async def root():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/options")
def get_options():
    return {
        "ancestries": sorted([a["name"] for a in generator.ancestries.values()]),
        "classes": sorted([c["name"] for c in generator.classes.values()]),
        "backgrounds": sorted([b["name"] for b in generator.backgrounds.values()]),
"archetypes": get_all_archetype_names(),
    }


@app.get("/api/generate")
async def generate_character(
    name: Optional[str] = None,
    ancestry: Optional[str] = None,
    class_name: Optional[str] = None,
    background: Optional[str] = None,
    archetype: Optional[str] = None,
    level: int = Query(1, ge=1, le=6),
    dedication: bool = Query(False),
):
    try:
        sheet = generator.generate(
            ancestry_name=ancestry,
            class_name=class_name,
            background_name=background,
            archetype_name=archetype,
            char_name=name,
            level=level,
            use_dedication=dedication or bool(archetype),
        )
        return sheet
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/levelup")
async def level_up_endpoint(payload: LevelUpPayload):
    current_level = int(payload.character.get("level", 1))
    if payload.target_level <= current_level:
        raise HTTPException(
            status_code=400,
            detail=f"Target level {payload.target_level} must be greater than current level {current_level}.",
        )
    try:
        updated_sheet = generator.level_up(payload.character, payload.target_level)
        return updated_sheet
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/export/foundry")
async def export_foundry(
    name: Optional[str] = None,
    ancestry: Optional[str] = None,
    class_name: Optional[str] = None,
    level: int = Query(1, ge=1, le=6),
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
