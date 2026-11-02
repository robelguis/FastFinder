from fastapi import FastAPI, Query, HTTPException, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from typing import Optional
import json

from app.engine.generator import PF2eGenerator
from app.engine.foundry import export_to_foundry_actor

app = FastAPI(title="FastFinder API", version="1.0.0")

STATIC_DIR = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

generator = PF2eGenerator()

@app.get("/")
def read_root():
    return FileResponse(STATIC_DIR / "index.html")

@app.get("/api/options")
def get_options():
    return {
        "ancestries": sorted([a.title() for a in generator.ancestries.keys()]),
        "classes": sorted([c.title() for c in generator.classes.keys()])
    }

@app.get("/api/generate")
def generate_character(
    ancestry: Optional[str] = Query(None),
    class_name: Optional[str] = Query(None),
    name: Optional[str] = Query(None),
    level: int = Query(1, ge=1, le=4),
    dedication: bool = Query(False)
):
    try:
        sheet = generator.generate(
            ancestry_name=ancestry,
            class_name=class_name,
            char_name=name,
            level=level
        )
        return sheet
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/export/foundry")
def export_foundry(
    ancestry: Optional[str] = Query(None),
    class_name: Optional[str] = Query(None),
    name: Optional[str] = Query(None),
    level: int = Query(1, ge=1, le=4),
    dedication: bool = Query(False)
):
    try:
        sheet = generator.generate(
            ancestry_name=ancestry,
            class_name=class_name,
            char_name=name,
            level=level
        )
        actor_data = export_to_foundry_actor(sheet)
        
        filename = f"{sheet.name.replace(' ', '_')}_Lvl{sheet.level}_PF2e.json"
        content = json.dumps(actor_data, indent=2)

        return Response(
            content=content,
            media_type="application/json",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
