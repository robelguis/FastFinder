from fastapi import FastAPI, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from typing import Optional
from app.engine.generator import PF2eGenerator
from app.engine.models import CharacterSheet

app = FastAPI(title="FastFinder - PF2e Fast Character Generator")

generator = PF2eGenerator()

STATIC_DIR = Path(__file__).resolve().parent / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)

@app.get("/api/options")
def get_options():
    return {
        "ancestries": sorted([a["name"] for a in generator.ancestries.values()]),
        "classes": sorted([c["name"] for c in generator.classes.values()])
    }

@app.get("/api/generate", response_model=CharacterSheet)
def generate_character(
    ancestry: Optional[str] = Query(None, description="Ancestry name"),
    class_name: Optional[str] = Query(None, description="Class name"),
    name: Optional[str] = Query("Valeros", description="Character name")
):
    return generator.generate(ancestry_name=ancestry, class_name=class_name, char_name=name)

# Mount frontend static directory
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/")
def serve_index():
    return FileResponse(STATIC_DIR / "index.html")
