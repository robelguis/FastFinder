from fastapi import FastAPI, Query, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pathlib import Path
from typing import Optional

from app.engine.generator import PF2eGenerator
from app.engine.foundry import export_to_foundry_actor

app = FastAPI(title="FastFinder PF2e Generator")

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

generator = PF2eGenerator()

@app.get("/")
async def root():
    return FileResponse(STATIC_DIR / "index.html")

@app.get("/api/options")
async def get_options():
    return {
        "ancestries": sorted([a.title() for a in generator.ancestries.keys()]),
        "classes": sorted([c.title() for c in generator.classes.keys()])
    }

@app.get("/api/generate")
async def generate_character(
    name: Optional[str] = None,
    ancestry: Optional[str] = None,
    class_name: Optional[str] = None,
    level: int = Query(1, ge=1, le=6),
    dedication: bool = Query(False)
):
    try:
        sheet = generator.generate(
            ancestry_name=ancestry,
            class_name=class_name,
            char_name=name,
            level=level,
            use_dedication=dedication
        )
        return sheet
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/export/foundry")
async def export_foundry(
    name: Optional[str] = None,
    ancestry: Optional[str] = None,
    class_name: Optional[str] = None,
    level: int = Query(1, ge=1, le=6),
    dedication: bool = Query(False)
):
    try:
        sheet = generator.generate(
            ancestry_name=ancestry,
            class_name=class_name,
            char_name=name,
            level=level,
            use_dedication=dedication
        )
        foundry_actor = export_to_foundry_actor(sheet)
        filename = f"{sheet.name.lower().replace(' ', '_')}_foundry.json"
        return JSONResponse(
            content=foundry_actor,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
